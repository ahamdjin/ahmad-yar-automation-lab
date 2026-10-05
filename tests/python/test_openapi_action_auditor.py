import unittest

from gpt_tools.openapi_action_auditor import audit


class OpenApiAuditTests(unittest.TestCase):
    def test_good_spec_has_no_errors(self):
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "Lead API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/leads/{lead_id}": {
                    "get": {
                        "operationId": "getLead",
                        "summary": "Get a lead",
                        "parameters": [{
                            "name": "lead_id",
                            "in": "path",
                            "required": True,
                            "description": "Lead identifier",
                            "schema": {"type": "string"},
                        }],
                        "responses": {"200": {"description": "Lead"}},
                    }
                }
            }
        }
        findings = audit(spec)
        self.assertFalse(any(item.level == "error" for item in findings))

    def test_missing_operation_id_is_error(self):
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "X", "version": "1"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {"/x": {"get": {"summary": "X", "responses": {"200": {"description": "ok"}}}}},
        }
        findings = audit(spec)
        self.assertTrue(any("operationId" in item.message for item in findings))

    def test_mutation_without_security_warns(self):
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "X", "version": "1"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {"/x": {"post": {
                "operationId": "createX",
                "summary": "Create X",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                "responses": {"200": {"description": "ok"}},
            }}},
        }
        findings = audit(spec)
        self.assertTrue(any(item.location.endswith(".security") for item in findings))


if __name__ == "__main__":
    unittest.main()
