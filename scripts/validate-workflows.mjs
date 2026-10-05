import { readdir, readFile, access } from 'node:fs/promises';
import { join, dirname, relative } from 'node:path';
import process from 'node:process';

const root = process.cwd();
const n8nRoot = join(root, 'n8n');
const errors = [];
const webhookPaths = new Map();

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
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
    /\bsk-[A-Za-z0-9_-]{20,}\b/
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

async function validateWorkflow(file) {
  const raw = await readFile(file, 'utf8');
  secretCheck(file, raw);

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

  const names = new Set();
  for (const node of workflow.nodes || []) {
    if (!node.name) {
      fail(file, 'node missing name');
      continue;
    }
    if (names.has(node.name)) fail(file, `duplicate node name "${node.name}"`);
    names.add(node.name);

    if (node.type === 'n8n-nodes-base.webhook') {
      const path = node.parameters?.path;
      if (!path) fail(file, `webhook node "${node.name}" is missing a path`);
      else if (webhookPaths.has(path)) {
        fail(file, `webhook path "${path}" duplicates ${webhookPaths.get(path)}`);
      } else {
        webhookPaths.set(path, relative(root, file));
      }
    }
  }

  validateConnections(file, workflow, names);

  const readme = join(dirname(file), 'README.md');
  try {
    await access(readme);
  } catch {
    fail(file, 'missing sibling README.md');
  }
}

let files = [];
try {
  files = (await walk(n8nRoot)).filter((file) => file.endsWith('workflow.json'));
} catch {
  errors.push('n8n/: workflow directory is missing');
}

if (files.length === 0) errors.push('No n8n/**/workflow.json files found');

for (const file of files) await validateWorkflow(file);

if (errors.length) {
  console.error('Workflow validation failed:\n');
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log(`Validated ${files.length} workflow${files.length === 1 ? '' : 's'} successfully.`);
