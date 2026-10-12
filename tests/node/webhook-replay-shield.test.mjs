import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {join} from "node:path";
import {runInNewContext} from "node:vm";
import test from "node:test";

const read = file => JSON.parse(readFileSync(join("n8n/webhook-replay-shield",file),"utf8"));
const workflow = read("workflow.json");
const nodes = new Map(workflow.nodes.map(node => [node.name,node]));
const evalCode = (name, json) => {
  const text = "(function() {\n" + nodes.get(name).parameters.jsCode + "\n})()";
  return JSON.parse(JSON.stringify(runInNewContext(text, {$input:{first:()=>({json})}}, {timeout:1500})[0].json));
};

test("inactive import contains valid 202 / 200 / 422 branches",() => {
  assert.equal(workflow.active,false);
  assert.equal(workflow.settings.executionOrder,"v1");
  assert.equal(nodes.get("Receive Event").parameters.responseMode,"responseNode");
  assert.equal(nodes.get("Receive Event").parameters.path,"webhook-replay-shield");
  for(const [name,status] of [["Return 202 First Seen",202],["Return 200 Duplicate",200],["Return 422 Invalid",422]]) {
    assert.equal(nodes.get(name).parameters.options.responseCode,status);
  }
  const branch = workflow.connections["Valid Event?"].main;
  assert.equal(branch[0][0].node,"Remember Seen Event Keys");
  assert.equal(branch[1][0].node,"Reject Invalid Event");
});

test("dedupe node uses n8n persisted prior-execution history",() => {
  const node=nodes.get("Remember Seen Event Keys");
  assert.equal(node.type,"n8n-nodes-base.removeDuplicates");
  assert.equal(node.typeVersion,2);
  assert.equal(node.parameters.operation,"removeItemsSeenInPreviousExecutions");
  assert.equal(node.parameters.dedupeValue,"={{ $json.eventKey }}");
  const branches=workflow.connections[node.name].main;
  assert.equal(branches[0][0].node,"First Delivery Response");
  assert.equal(branches[1][0].node,"Duplicate Delivery Response");
});

test("first and repeat deliveries return safe fictional example response bodies",() => {
  const request=read("sample-request.json");
  const event=evalCode("Validate Event Envelope",{body:request});
  assert.equal(event.valid,true);
  assert.equal(event.eventKey,"crm:"+request.event_id);
  assert.equal(event.lead,undefined);
  assert.equal(JSON.stringify(event).includes("nobody@example.invalid"),false);
  assert.deepEqual(evalCode("First Delivery Response",event),read("sample-response.json"));
  assert.deepEqual(evalCode("Duplicate Delivery Response",event),read("sample-duplicate-response.json"));
});

test("valid identifiers are source-scoped with case-sensitive event IDs",() => {
  const event=evalCode("Validate Event Envelope",{body:{source:"  CRM ",eventId:"Abc_def_01"}});
  assert.equal(event.eventKey,"crm:Abc_def_01");
  assert.equal(event.valid,true);
  const next=evalCode("Validate Event Envelope",{body:{source:"CRM",event_id:"abc_def_01"}});
  assert.notEqual(event.eventKey,next.eventKey);
});

test("invalid envelopes skip dedupe and return explicit safe error",() => {
  const invalid=evalCode("Validate Event Envelope",{body:read("sample-invalid-request.json")});
  assert.equal(invalid.valid,false);
  assert.equal(invalid.eventKey,null);
  assert.deepEqual(evalCode("Reject Invalid Event",invalid),read("sample-invalid-response.json"));
  for(const body of [
    {event_id:"too",source:"crm"},
    {event_id:12,source:"crm"},
    {event_id:"event_000001",source:"???"},
    {event_id:"private@email",source:"crm"},
    {event_id:"event_000001"}
  ]) assert.equal(evalCode("Validate Event Envelope",{body}).valid,false);
});

test("extra private input keys are not echoed",() => {
  const body={source:"crm",event_id:"event_000001"};
  for(let i=0;i<40;i++) body["private_"+i]="private_value";
  const invalid=evalCode("Validate Event Envelope",{body});
  assert.equal(invalid.valid,false);
  assert.equal(JSON.stringify(invalid).includes("private_value"),false);
});

test("sample template has no active side effects or credentials",() => {
  assert.equal(workflow.nodes.filter(node=>node.type==="n8n-nodes-base.httpRequest").length,0);
  assert.equal(workflow.nodes.filter(node=>node.type==="n8n-nodes-base.respondToWebhook").length,3);
  assert.ok(workflow.nodes.every(node=>node.credentials==null));
  assert.equal(new Set(workflow.nodes.map(node=>node.id)).size,workflow.nodes.length);
});
