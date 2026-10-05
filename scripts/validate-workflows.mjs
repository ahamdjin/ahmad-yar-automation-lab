import { readdir, readFile, access } from 'node:fs/promises';
import { join, dirname, relative, extname } from 'node:path';
import process from 'node:process';

const root = process.cwd();
const n8nRoot = join(root, 'n8n');
const errors = [];
const webhookPaths = new Map();

const ignoredDirectories = new Set(['.git', 'node_modules']);
const textExtensions = new Set(['.json', '.js', '.mjs', '.md', '.yml', '.yaml', '.txt']);

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue;
    const path = join(dir, entry.name);
    if (entry.isDirectory()) files.push(...await walk(path));
    else files.push(path);
  }
  return files;
}

function fail(file, message) {
  errors.push(`${relative(root, file)}: ${message}`);
}

function secretCheck(file, raw) {
  const patterns = [
    /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
    /\bghp_[A-Za-z0-9]{20,}\b/,
    /\bgithub_pat_[A-Za-z0-9_]{20,}\b/,
    /\bxox[baprs]-[A-Za-z0-9-]{20,}\b/,
    /\bsk-[A-Za-z0-9_-]{20,}\b/,
    /\bAKIA[0-9A-Z]{16}\b/
  ];
  for (const pattern of patterns) {
    if (pattern.test(raw)) fail(file, `possible secret matching ${pattern}`);
  }
}

function validateConnections(file, workflow, nodeNames) {
  for (const [source, groups] of Object.entries(workflow.connections || {})) {
    if (!nodeNames.has(source)) fail(file, `connection source "${source}" is not a node`);
    for (const branches of Object.values(groups || {})) {
      for (const branch of branches || []) {
        for (const connection of branch || []) {
          if (!nodeNames.has(connection.node)) {
            fail(file, `connection target "${connection.node}" is not a node`);
          }
        }
      }
    }
  }
}

async function requireSibling(file, name) {
  const sibling = join(dirname(file), name);
  try {
    await access(sibling);
  } catch {
    fail(file, `missing sibling ${name}`);
  }
}

async function validateWorkflow(file) {
  const raw = await readFile(file, 'utf8');

  let workflow;
  try {
    workflow = JSON.parse(raw);
  } catch (error) {
    fail(file, `invalid JSON: ${error.message}`);
    return;
  }

  if (!workflow.name || typeof workflow.name !== 'string') fail(file, 'missing workflow name');
  if (!Array.isArray(workflow.nodes) || workflow.nodes.length === 0) fail(file, 'nodes must be a non-empty array');
  if (!workflow.connections || typeof workflow.connections !== 'object') fail(file, 'missing connections object');
  if (workflow.active !== false) fail(file, 'public workflow exports must set active to false');
  if (!workflow.settings || workflow.settings.executionOrder !== 'v1') fail(file, 'settings.executionOrder must be v1');

  const names = new Set();
  const ids = new Set();
  const webhookNodes = [];
  const respondNodes = [];

  for (const node of workflow.nodes || []) {
    if (!node.name) {
      fail(file, 'node missing name');
      continue;
    }
    if (names.has(node.name)) fail(file, `duplicate node name "${node.name}"`);
    names.add(node.name);

    if (!node.id) fail(file, `node "${node.name}" is missing an id`);
    else if (ids.has(node.id)) fail(file, `duplicate node id "${node.id}"`);
    else ids.add(node.id);

    if (node.type === 'n8n-nodes-base.webhook') {
      webhookNodes.push(node);
      const path = node.parameters?.path;
      if (!path) fail(file, `webhook node "${node.name}" is missing a path`);
      else if (webhookPaths.has(path)) {
        fail(file, `webhook path "${path}" duplicates ${webhookPaths.get(path)}`);
      } else {
        webhookPaths.set(path, relative(root, file));
      }
    }

    if (node.type === 'n8n-nodes-base.respondToWebhook') {
      respondNodes.push(node);
      if (node.parameters?.options?.responseCode === undefined) {
        fail(file, `Respond to Webhook node "${node.name}" must set an explicit response code`);
      }
    }
  }

  for (const webhook of webhookNodes) {
    if (respondNodes.length > 0 && webhook.parameters?.responseMode !== 'responseNode') {
      fail(file, `webhook node "${webhook.name}" must use responseMode=responseNode when Respond to Webhook is present`);
    }
  }

  validateConnections(file, workflow, names);
  await requireSibling(file, 'README.md');

  if (webhookNodes.length > 0) {
    await requireSibling(file, 'sample-request.json');
    await requireSibling(file, 'sample-response.json');
  }
}

const allFiles = await walk(root);
for (const file of allFiles) {
  if (textExtensions.has(extname(file))) {
    const raw = await readFile(file, 'utf8');
    secretCheck(file, raw);
  }
}

const workflowFiles = allFiles.filter((file) =>
  file.startsWith(n8nRoot) && file.endsWith('workflow.json')
);

if (workflowFiles.length === 0) errors.push('No n8n/**/workflow.json files found');

for (const file of workflowFiles) await validateWorkflow(file);

if (errors.length) {
  console.error('Workflow validation failed:\n');
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log(`Validated ${workflowFiles.length} workflow${workflowFiles.length === 1 ? '' : 's'} successfully.`);
