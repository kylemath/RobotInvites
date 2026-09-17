let state = null;
let playing = false;
let timer;
let activeTab = 'door';
let scene, camera, renderer;
let worldKey = '';
const robotVisuals = new Map();
const robotColors = ['#f26e4f', '#27756d', '#e0a52f', '#6576b8', '#c45d91', '#4d9b83', '#cf7548', '#6b6d73'];
const configs = {
  door: { label: 'ONE DOOR / ORDERLY QUEUE', note: 'Baseline: 30 robots, one 3-wide door, and a synchronized arrival surge.', config: { extra_doors: 0, door_width: 3, variability: 0, arrival_pattern: 'surge' } },
  doors: { label: 'MORE DOORS / PARALLEL FLOW', note: 'Two separate 3-wide doors double the modeled admission capacity from three to six robots per tick.', config: { extra_doors: 1, door_width: 3, variability: 0, arrival_pattern: 'surge' } },
  size: { label: 'BIGGER DOOR / WIDER FLOW', note: 'One opening expands to five robot widths while the synchronized arrival pattern stays the same.', config: { extra_doors: 0, door_width: 5, variability: 0, arrival_pattern: 'surge' } },
  schedule: { label: 'INVITE TIMING / SPREAD THE PEAK', note: 'Thirty arrivals are scheduled evenly across a seven-second window, eliminating the queue.', config: { extra_doors: 0, door_width: 3, variability: 0, arrival_pattern: 'scheduled' } },
  personality: { label: 'PERSONALITY / IMPERFECT PUNCTUALITY', note: 'Each robot receives an independent arrival time between zero and 3.5 seconds.', config: { extra_doors: 0, door_width: 3, variability: 0, arrival_pattern: 'personality' } },
  infinite: { label: 'AT THE LIMIT / MANY ROBOTS', note: 'One 3-wide door faces a 100-robot synchronized surge, making the fixed bottleneck persistent.', config: { extra_doors: 0, door_width: 3, variability: 0, arrival_pattern: 'surge' } }
};

async function api(path, options = {}) { const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options }); return response.json(); }
async function refresh() { try { state = await api('/api/state'); updateDashboard(); document.getElementById('connection').textContent = 'connected'; } catch { document.getElementById('connection').textContent = 'offline'; } }
async function step() { state = await api('/api/step', { method: 'POST', body: JSON.stringify({ seconds: Number(document.getElementById('speed').value) * .25 }) }); updateDashboard(); }
function updateDashboard() {
  if (!state) return;
  const metrics = state.metrics || {};
  document.getElementById('throughput').textContent = (metrics.throughput_per_minute || 0).toFixed(1);
  document.getElementById('average-wait').textContent = (metrics.average_wait || 0).toFixed(1);
  document.getElementById('utilization').textContent = `${Math.round((metrics.utilization || 0) * 100)}%`;
  document.getElementById('queue').textContent = metrics.waiting || 0;
  document.getElementById('clock').textContent = `T+ ${formatTime(state.time)}`;
  document.getElementById('event').textContent = metrics.event || 'ready';
  api('/api/log').then(data => { const recent = data.rows.slice(-28); const max = Math.max(1, ...recent.map(row => row.waiting)); document.getElementById('chart').innerHTML = recent.map(row => `<i class="bar" style="height:${Math.max(2, row.waiting / max * 100)}%" title="${row.waiting} waiting at ${row.time}s"></i>`).join(''); });
}
function formatTime(seconds) { const mins = Math.floor(seconds / 60).toString().padStart(2, '0'); const secs = Math.floor(seconds % 60).toString().padStart(2, '0'); return `${mins}:${secs}`; }
function togglePlay() { playing = !playing; const button = document.getElementById('play'); button.innerHTML = playing ? 'Ⅱ <span>Pause</span>' : '▶ <span>Run</span>'; if (playing) timer = setInterval(step, 160); else clearInterval(timer); }
async function chooseTab(tab) {
  activeTab = tab; worldKey = ''; document.querySelectorAll('.tab').forEach(button => button.classList.toggle('active', button.dataset.tab === tab));
  const choice = configs[tab]; document.getElementById('scenario-label').textContent = choice.label; document.getElementById('scenario-note').textContent = choice.note;
  if (playing) togglePlay(); state = await api('/api/reset', { method: 'POST', body: JSON.stringify({ ...choice.config, robot_count: tab === 'infinite' ? 100 : 30 }) }); robotVisuals.clear(); updateDashboard();
}

function material(color, roughness = .7) { return new THREE.MeshStandardMaterial({ color, roughness, metalness: .08 }); }
function setupScene() {
  const holder = document.getElementById('canvas-holder'); scene = new THREE.Scene(); scene.background = new THREE.Color('#dfe4dc');
  camera = new THREE.OrthographicCamera(-6, 6, 5, -5, .1, 100); camera.position.set(0, 10, 10); camera.lookAt(0, 0, 0);
  renderer = new THREE.WebGLRenderer({ antialias: true }); renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); renderer.shadowMap.enabled = true; holder.appendChild(renderer.domElement);
  scene.add(new THREE.HemisphereLight('#f7f4e8', '#87938a', 2.2)); const sun = new THREE.DirectionalLight('#fffaf0', 2.5); sun.position.set(-4, 10, 5); sun.castShadow = true; scene.add(sun); scene.add(new THREE.GridHelper(12, 12, '#c4ccc2', '#d2d8cf'));
  window.addEventListener('resize', resizeScene); resizeScene(); animate();
}
function resizeScene() { const holder = document.getElementById('canvas-holder'); const aspect = holder.clientWidth / Math.max(1, holder.clientHeight); const height = 10; camera.left = -height * aspect / 2; camera.right = height * aspect / 2; camera.top = height / 2; camera.bottom = -height / 2; camera.updateProjectionMatrix(); renderer.setSize(holder.clientWidth, holder.clientHeight, false); }
function clearWorld() { while (scene.children.length > 3) scene.remove(scene.children[scene.children.length - 1]); }
function addBlock(x, z, width, depth, height, color) { const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), material(color)); mesh.position.set(x, height / 2, z); mesh.castShadow = true; mesh.receiveShadow = true; scene.add(mesh); }
function doorCenters(config) { return config.extra_doors ? [-2.25, 2.25] : [0]; }
function drawWorld(config) {
  clearWorld(); addBlock(3.3, 0, 6.6, 10, .28, '#cfd6cb'); const centers = doorCenters(config); const openings = centers.map(center => [center - config.door_width / 2, center + config.door_width / 2]); let cursor = -5;
  openings.sort((a, b) => a[0] - b[0]).forEach(opening => { if (opening[0] > cursor) addBlock(0, (cursor + opening[0]) / 2, 1.1, opening[0] - cursor, 1.3, '#87948a'); cursor = opening[1]; }); if (cursor < 5) addBlock(0, (cursor + 5) / 2, 1.1, 5 - cursor, 1.3, '#87948a');
  addBlock(3.8, 0, 6.4, 10, .8, '#f1eee5'); centers.forEach(center => addBlock(.25, center, .5, config.door_width, 1.1, '#27756d'));
}
function laneFor(robot, config) { const centers = doorCenters(config); return centers[robot.robot_id % centers.length] + ((robot.robot_id * 7) % Math.max(1, Math.floor(config.door_width)) - Math.floor(config.door_width / 2)) * .82; }
function robotMesh(robot) { const group = new THREE.Group(); const body = new THREE.Mesh(new THREE.BoxGeometry(.62, .62, .62), material(robotColors[robot.robot_id % robotColors.length])); body.position.y = .45; body.castShadow = true; group.add(body); const head = new THREE.Mesh(new THREE.BoxGeometry(.42, .3, .42), material('#f2f0e9')); head.position.set(0, .9, -.08); group.add(head); [-.11, .11].forEach(x => { const eye = new THREE.Mesh(new THREE.BoxGeometry(.06, .06, .04), material('#17211f')); eye.position.set(x, .93, -.3); group.add(eye); }); return group; }
function renderRobots(config) {
  const active = new Set();
  for (const robot of state.robots) {
    active.add(robot.robot_id); let visual = robotVisuals.get(robot.robot_id); if (!visual) { visual = { group: robotMesh(robot), x: -4.5, z: robot.y - 5 }; robotVisuals.set(robot.robot_id, visual); scene.add(visual.group); }
    const lane = laneFor(robot, config); const targetZ = robot.status === 'inside' ? lane : robot.y - 5; const targetX = robot.status === 'inside' ? 2.2 + (robot.robot_id % 4) * .72 : robot.x; const throughDoorX = robot.status === 'inside' ? .55 : targetX; const previousX = visual.x;
    visual.x += (throughDoorX - visual.x) * (robot.status === 'inside' ? .16 : .12); visual.z += (targetZ - visual.z) * .12; if (robot.status === 'inside' && visual.x > .48) visual.x += (targetX - visual.x) * .13;
    visual.group.position.set(visual.x, 0, visual.z); visual.group.rotation.y = Math.atan2(visual.z - (robot.y - 5), visual.x - previousX) * .18;
  }
  robotVisuals.forEach((visual, id) => { if (!active.has(id)) { scene.remove(visual.group); robotVisuals.delete(id); } });
}
function animate() { requestAnimationFrame(animate); if (state) { const nextWorldKey = JSON.stringify(state.config); if (nextWorldKey !== worldKey) { drawWorld(state.config); worldKey = nextWorldKey; } renderRobots(state.config); } renderer.render(scene, camera); }
function setup() { setupScene(); document.getElementById('play').addEventListener('click', togglePlay); document.getElementById('step').addEventListener('click', step); document.getElementById('reset').addEventListener('click', () => chooseTab(activeTab)); document.querySelectorAll('.tab').forEach(button => button.addEventListener('click', () => chooseTab(button.dataset.tab))); chooseTab('door'); setInterval(refresh, 900); }
window.addEventListener('load', setup);
