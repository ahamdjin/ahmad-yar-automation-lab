"""Audit an OpenAPI schema for common GPT Action / model-tool integration problems."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
OPERATION_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class Finding:
    level: str
    location: str
    message: str


def load_spec(path: str) -> dict:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        return json.loads(text)

    if source.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError("YAML input requires PyYAML. Install with: pip install '.[yaml]'") from exc
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ValueError("OpenAPI document must be an object")
        return data

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Use .json, .yaml, or .yml for OpenAPI input") from exc


def audit(spec: dict) -> list[Finding]:
    findings: list[Finding] = []
    openapi = str(spec.get("openapi", ""))
    if not openapi.startswith("3."):
        findings.append(Finding("error", "openapi", "Expected an OpenAPI 3.x document."))

    info = spec.get("info")
    if not isinstance(info, dict):
        findings.append(Finding("error", "info", "Missing info object."))
    else:
        for key in ("title", "version"):
            if not info.get(key):
                findings.append(Finding("warning", f"info.{key}", f"Missing {key}."))

    servers = spec.get("servers")
    if not isinstance(servers, list) or not servers:
        findings.append(Finding("error", "servers", "Define at least one public HTTPS server."))
    else:
        for index, server in enumerate(servers):
            url = server.get("url") if isinstance(server, dict) else None
            if not url:
                findings.append(Finding("error", f"servers[{index}]", "Server is missing a URL."))
                continue
            parsed = urlparse(url)
            if parsed.scheme != "https":
                findings.append(Finding("error", f"servers[{index}].url", "GPT Actions should use HTTPS endpoints."))
            if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
                findings.append(Finding("error", f"servers[{index}].url", "Localhost is not a deployable action server."))

    top_security = spec.get("security")
    paths = spec.get("paths")
    if not isinstance(paths, dict) or not paths:
        findings.append(Finding("error", "paths", "No API paths defined."))
        return findings

    operation_ids: set[str] = set()
    operation_count = 0

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method_lower = method.lower()
            if method_lower not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_count += 1
            location = f"paths.{path}.{method_lower}"

            operation_id = operation.get("operationId")
            if not operation_id:
                findings.append(Finding("error", location, "Missing operationId; the model needs stable action names."))
            else:
                if operation_id in operation_ids:
                    findings.append(Finding("error", f"{location}.operationId", f'Duplicate operationId "{operation_id}".'))
                operation_ids.add(operation_id)
                if not OPERATION_ID_RE.match(str(operation_id)):
                    findings.append(Finding("warning", f"{location}.operationId", "Use a short identifier starting with a letter or underscore."))

            if not (operation.get("summary") or operation.get("description")):
                findings.append(Finding("warning", location, "Add a clear summary or description so the model knows when to call this action."))

            parameters = []
            if isinstance(path_item.get("parameters"), list):
                parameters.extend(path_item["parameters"])
            if isinstance(operation.get("parameters"), list):
                parameters.extend(operation["parameters"])
            for index, parameter in enumerate(parameters):
                if not isinstance(parameter, dict) or "$ref" in parameter:
                    continue
                if not parameter.get("name"):
                    findings.append(Finding("error", f"{location}.parameters[{index}]", "Parameter is missing a name."))
                if not parameter.get("description"):
                    findings.append(Finding("warning", f"{location}.parameters[{index}]", "Describe what this parameter means and when to use it."))
                if "schema" not in parameter:
                    findings.append(Finding("error", f"{location}.parameters[{index}]", "Parameter is missing a schema."))

            request_body = operation.get("requestBody")
            if method_lower == "get" and request_body:
                findings.append(Finding("warning", f"{location}.requestBody", "GET request bodies are poorly supported across clients; prefer parameters."))
            if isinstance(request_body, dict) and "$ref" not in request_body:
                content = request_body.get("content")
                if not isinstance(content, dict) or "application/json" not in content:
                    findings.append(Finding("warning", f"{location}.requestBody", "Prefer an application/json request schema for predictable tool calls."))
                elif "schema" not in content["application/json"]:
                    findings.append(Finding("error", f"{location}.requestBody.content.application/json", "Missing request schema."))

            responses = operation.get("responses")
            if not isinstance(responses, dict) or not responses:
                findings.append(Finding("error", f"{location}.responses", "Define at least one response."))
            elif not any(str(code).startswith("2") for code in responses):
                findings.append(Finding("warning", f"{location}.responses", "No 2xx success response documented."))

            effective_security = operation.get("security", top_security)
            if method_lower in {"post", "put", "patch", "delete"} and effective_security in (None, []):
                findings.append(Finding("warning", f"{location}.security", "State-changing action has no OpenAPI security requirement."))

    if operation_count > 30:
        findings.append(Finding("warning", "paths", f"{operation_count} operations may make tool selection harder; expose a focused action surface."))

    schemes = spec.get("components", {}).get("securitySchemes", {}) if isinstance(spec.get("components"), dict) else {}
    if schemes and not isinstance(schemes, dict):
        findings.append(Finding("error", "components.securitySchemes", "securitySchemes must be an object."))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenAPI JSON/YAML for GPT Action/tool usability.")
    parser.add_argument("spec", help="OpenAPI .json/.yaml file")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON")
    parser.add_argument("--strict-warnings", action="store_true", help="Exit non-zero when warnings exist")
    args = parser.parse_args()

    try:
        findings = audit(load_spec(args.spec))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2))
    else:
        if not findings:
            print("No findings.")
        for item in findings:
            print(f"{item.level.upper():7} {item.location}: {item.message}")

    errors = any(item.level == "error" for item in findings)
    warnings = any(item.level == "warning" for item in findings)
    return 1 if errors or (args.strict_warnings and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
