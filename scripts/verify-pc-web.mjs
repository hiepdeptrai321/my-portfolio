import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const hash = (data) => createHash('sha256').update(data).digest('hex');
const data = await readFile('public/models/pc-upgrade.glb');
assert.equal(data.readUInt32LE(0), 0x46546c67);
assert.equal(data.readUInt32LE(4), 2);
assert.equal(data.readUInt32LE(8), data.length);
const gltf = JSON.parse(data.subarray(20, 20 + data.readUInt32LE(12)).toString());
const names = gltf.nodes.map((node) => node.name);
for (const name of ['PC_Reference_Case_Replacement', 'PC_Reference_Glass_Panel',
  'PC_Reference_Upper_Rear_Fan_Diffuser', 'PC_Reference_Bottom_LED_Diffuser']) {
  assert.ok(names.includes(name), `Missing reference geometry: ${name}`);
}
assert.equal(gltf.meshes.length, 9);
for (const name of ['PC_Reference_RAM_LED_0', 'PC_Reference_RAM_LED_1', 'PC_Reference_Top_LED_Diffuser',
  'PC_Reference_Lower_Rear_Fan_LED', 'PC_Reference_Power_Button_LED']) assert.ok(names.includes(name));
assert.ok(!names.some((name) => name?.startsWith('PC_Upgrade_')));
const bakedIndex = gltf.materials.findIndex((material) => material.name === 'PC_Reference_Baked_Day');
assert.ok(gltf.materials[bakedIndex]?.pbrMetallicRoughness.baseColorTexture);
const bakedPrimitives = gltf.meshes.flatMap((mesh) => mesh.primitives).filter((p) => p.material === bakedIndex);
assert.ok(bakedPrimitives.length);
assert.ok(bakedPrimitives.every((p) => p.attributes.TEXCOORD_0 !== undefined));
assert.ok(gltf.images.every((image) => image.bufferView !== undefined && !image.uri));

const exported = JSON.parse(await readFile('artifacts/pc-reference-match/web-export-report.json', 'utf8'));
assert.equal(hash(data), exported.sha256);
assert.equal(hash(await readFile('blender files/My Room - FINAL.blend')), exported.source_sha256);
assert.equal(hash(await readFile('dist/models/pc-upgrade.glb')), hash(data));
const url = 'http://localhost:5173/models/pc-upgrade.glb?v=20260920-pc-polish-v3';
const response = await fetch(url);
assert.equal(response.status, 200);
assert.equal(hash(Buffer.from(await response.arrayBuffer())), hash(data));
const sourceResponse = await fetch('http://localhost:5173/src/main.js');
assert.equal(sourceResponse.status, 200);
assert.ok((await sourceResponse.text()).includes('20260920-pc-polish-v3'));
const report = { passed: true, meshes: gltf.meshes.length,
  embeddedImages: gltf.images.length, materials: gltf.materials.map((m) => m.name),
  bytes: data.length, sha256: hash(data), sourceBlendUnchanged: true,
  buildAssetMatches: true, devServerAssetMatches: true, browserVisualCheck: 'unavailable' };
await writeFile('artifacts/pc-reference-match/web-verification.json', JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
