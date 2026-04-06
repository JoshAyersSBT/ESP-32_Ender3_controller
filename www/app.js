async function refreshStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    document.getElementById('status').innerHTML = `
      <p><strong>Network:</strong> ${data.network_mode} (${data.ip_address})</p>
      <p><strong>Printer:</strong> ${data.printer_connected ? 'Connected' : 'Waiting'}</p>
      <p><strong>State:</strong> ${data.printer_state}</p>
      <p><strong>Current file:</strong> ${data.current_file ?? '--'}</p>
      <p><strong>Progress:</strong> ${data.progress_percent ?? 0}%</p>
      <p><strong>Nozzle:</strong> ${data.nozzle_temp ?? '--'} / ${data.nozzle_target ?? '--'} C</p>
      <p><strong>Bed:</strong> ${data.bed_temp ?? '--'} / ${data.bed_target ?? '--'} C</p>
      <p><strong>Message:</strong> ${data.last_message ?? ''}</p>
      <p><strong>Error:</strong> ${data.last_error ?? ''}</p>
    `;
  } catch (err) {
    document.getElementById('status').textContent = 'Failed to load status';
  }
}

async function refreshFiles() {
  try {
    const res = await fetch('/api/files');
    const data = await res.json();
    const box = document.getElementById('files');

    if (!data.files || !data.files.length) {
      box.innerHTML = '<p>No files uploaded.</p>';
      return;
    }

    box.innerHTML = data.files.map(f => `
      <div class="file-row">
        <div>
          <strong>${f.name}</strong><br>
          <span>${f.size} bytes</span>
        </div>
        <div class="row">
          <button onclick="startPrint('${escapeQuotes(f.name)}')">Print</button>
          <button onclick="deleteFile('${escapeQuotes(f.name)}')">Delete</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    document.getElementById('files').textContent = 'Failed to load files';
  }
}

function escapeQuotes(v) {
  return String(v).replace(/'/g, "\'");
}

async function cmd(path) {
  await fetch(path);
  await refreshStatus();
  await refreshFiles();
}

async function setHotend() {
  const v = document.getElementById('hotend').value;
  await fetch(`/api/hotend?s=${encodeURIComponent(v)}`);
  refreshStatus();
}

async function setBed() {
  const v = document.getElementById('bed').value;
  await fetch(`/api/bed?s=${encodeURIComponent(v)}`);
  refreshStatus();
}

async function uploadFile() {
  const input = document.getElementById('uploadFile');
  if (!input.files.length) return;

  const file = input.files[0];
  const buf = await file.arrayBuffer();

  await fetch('/api/upload', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/octet-stream',
      'X-Filename': file.name,
      'Content-Length': String(buf.byteLength),
    },
    body: buf,
  });

  input.value = '';
  await refreshFiles();
  await refreshStatus();
}

async function startPrint(name) {
  await fetch(`/api/start?name=${encodeURIComponent(name)}`);
  await refreshStatus();
}

async function deleteFile(name) {
  await fetch(`/api/delete?name=${encodeURIComponent(name)}`);
  await refreshFiles();
  await refreshStatus();
}

setInterval(() => {
  refreshStatus();
  refreshFiles();
}, 2000);

refreshStatus();
refreshFiles();