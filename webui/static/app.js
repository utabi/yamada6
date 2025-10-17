const statusEl = document.getElementById('status');
const pendingTable = document.querySelector('#pending-table tbody');
const appliedTable = document.querySelector('#applied-table tbody');
const auditTable = document.querySelector('#audit-table tbody');
const refreshBtn = document.getElementById('refresh-btn');
const controlButtons = document.querySelectorAll('.controls button');
const patchForm = document.getElementById('patch-form');

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}\n${text}`);
  }
  return res.json();
}

function renderStatus(payload) {
  statusEl.innerHTML = `
    <ul>
      <li>Loop count: ${payload.loop_count}</li>
      <li>Paused: ${payload.paused}</li>
      <li>Interval: ${payload.loop_interval_seconds}s</li>
      <li>Last plan: ${payload.last_plan ? payload.last_plan.summary : '-'} </li>
      <li>Pending patches: ${payload.pending_patches.length}</li>
    </ul>
  `;
}

function renderPending(patches) {
  pendingTable.innerHTML = '';
  patches.forEach((patch) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${patch.patch_id}</td>
      <td>${patch.summary}</td>
      <td>${patch.author}</td>
      <td>${patch.created_at}</td>
      <td>
        <button data-apply="${patch.patch_id}">apply</button>
        <button data-rollback="${patch.patch_id}">rollback</button>
      </td>
    `;
    pendingTable.appendChild(tr);
  });
}

function renderApplied(patches) {
  appliedTable.innerHTML = '';
  patches.forEach((patch) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${patch.patch_id}</td>
      <td>${patch.summary}</td>
      <td>${patch.notes || patch.artifact_local_path || ''}</td>
    `;
    appliedTable.appendChild(tr);
  });
}

function renderAudit(entries) {
  auditTable.innerHTML = '';
  entries.slice().reverse().forEach((entry) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${entry.timestamp}</td>
      <td>${entry.patch_id}</td>
      <td>${entry.status}</td>
      <td>${entry.detail || ''}</td>
    `;
    auditTable.appendChild(tr);
  });
}

async function refreshAll() {
  try {
    const [status, pending, applied, audit] = await Promise.all([
      fetchJSON('/status'),
      fetchJSON('/patches'),
      fetchJSON('/patches/applied'),
      fetchJSON('/patches/audit'),
    ]);
    renderStatus(status);
    renderPending(pending);
    renderApplied(applied);
    renderAudit(audit);
  } catch (err) {
    console.error(err);
    alert(`取得に失敗しました\n${err.message}`);
  }
}

refreshBtn.addEventListener('click', refreshAll);

controlButtons.forEach((btn) => {
  btn.addEventListener('click', async () => {
    const action = btn.dataset.action;
    try {
      await fetchJSON(`/control/${action}`, { method: 'POST' });
      await refreshAll();
    } catch (err) {
      alert(`${action} failed\n${err.message}`);
    }
  });
});

pendingTable.addEventListener('click', async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLButtonElement)) return;

  if (target.dataset.apply) {
    const id = target.dataset.apply;
    try {
      await fetchJSON(`/patches/${id}/apply`, { method: 'POST' });
      await refreshAll();
    } catch (err) {
      alert(`apply failed\n${err.message}`);
    }
  }

  if (target.dataset.rollback) {
    const id = target.dataset.rollback;
    try {
      await fetchJSON(`/patches/${id}/rollback`, { method: 'POST' });
      await refreshAll();
    } catch (err) {
      alert(`rollback failed\n${err.message}`);
    }
  }
});

patchForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(patchForm);
  const payload = Object.fromEntries(formData.entries());
  payload.created_at = new Date().toISOString();

  try {
    await fetchJSON('/patches', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    patchForm.reset();
    await refreshAll();
  } catch (err) {
    alert(`登録に失敗しました\n${err.message}`);
  }
});

refreshAll().catch(console.error);
