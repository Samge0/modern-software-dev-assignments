async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function noteListItem(n, { onReload }) {
  const li = document.createElement('li');
  li.textContent = `${n.title}: ${n.content}`;

  const editBtn = document.createElement('button');
  editBtn.textContent = 'Edit';
  editBtn.onclick = async () => {
    const title = prompt('Edit title', n.title);
    if (title === null) return;
    const content = prompt('Edit content', n.content);
    if (content === null) return;
    try {
      await fetchJSON(`/notes/${n.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content }),
      });
      onReload();
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    }
  };
  li.appendChild(editBtn);

  const delBtn = document.createElement('button');
  delBtn.textContent = 'Delete';
  delBtn.onclick = async () => {
    if (!confirm(`Delete note "${n.title}"?`)) return;
    try {
      await fetchJSON(`/notes/${n.id}`, { method: 'DELETE' });
      onReload();
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };
  li.appendChild(delBtn);

  return li;
}

async function loadNotes(query = '') {
  const list = document.getElementById('notes');
  list.innerHTML = '';
  const url = query
    ? `/notes/search/?q=${encodeURIComponent(query)}`
    : '/notes/';
  const notes = await fetchJSON(url);
  for (const n of notes) {
    list.appendChild(noteListItem(n, { onReload: () => loadNotes(query) }));
  }
}

async function loadActions() {
  const list = document.getElementById('actions');
  list.innerHTML = '';
  const items = await fetchJSON('/action-items/');
  for (const a of items) {
    const li = document.createElement('li');
    li.textContent = `${a.description} [${a.completed ? 'done' : 'open'}]`;
    if (!a.completed) {
      const btn = document.createElement('button');
      btn.textContent = 'Complete';
      btn.onclick = async () => {
        await fetchJSON(`/action-items/${a.id}/complete`, { method: 'PUT' });
        loadActions();
      };
      li.appendChild(btn);
    }
    list.appendChild(li);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('note-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('note-title').value;
    const content = document.getElementById('note-content').value;
    await fetchJSON('/notes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content }),
    });
    e.target.reset();
    loadNotes();
  });

  document.getElementById('search-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const query = document.getElementById('search-query').value.trim();
    loadNotes(query);
  });

  document.getElementById('search-clear').addEventListener('click', () => {
    document.getElementById('search-query').value = '';
    loadNotes();
  });

  document.getElementById('action-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const description = document.getElementById('action-desc').value;
    await fetchJSON('/action-items/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    e.target.reset();
    loadActions();
  });

  loadNotes();
  loadActions();
});
