async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  // 204 (DELETE) has no body
  if (res.status === 204) return null;
  const body = await res.json();
  // response envelope: {ok, data} (added by TASK 7 middleware)
  if (body && typeof body === 'object' && 'ok' in body) {
    if (!body.ok) throw new Error(body.error?.message || 'Request failed');
    return body.data;
  }
  return body;
}

// ================= Notes section (TASK 2/3/8) =================
// search + sort + pagination + optimistic edit/delete

const notesState = { q: '', sort: 'created_desc', page: 1, pageSize: 5 };

async function loadNotes() {
  const list = document.getElementById('notes');
  const params = new URLSearchParams({
    q: notesState.q,
    sort: notesState.sort,
    page: String(notesState.page),
    page_size: String(notesState.pageSize),
  });
  const body = await fetchJSON(`/notes/search/?${params}`);
  list.innerHTML = '';
  for (const n of body.items) {
    const li = document.createElement('li');

    const span = document.createElement('span');
    span.className = 'note-text';
    span.textContent = `${n.title}: ${n.content}`;
    li.appendChild(span);

    // optimistic edit (TASK 3): update DOM first, roll back on error
    const editBtn = document.createElement('button');
    editBtn.textContent = 'Edit';
    editBtn.onclick = async () => {
      const title = prompt('Edit title', n.title);
      if (title === null) return;
      const content = prompt('Edit content', n.content);
      if (content === null) return;
      const prevText = span.textContent;
      span.textContent = `${title}: ${content}`;
      span.classList.add('pending');
      try {
        await fetchJSON(`/notes/${n.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, content }),
        });
        n.title = title;
        n.content = content;
      } catch (err) {
        span.textContent = prevText; // rollback
        alert(`Update failed, rolled back: ${err.message}`);
      } finally {
        span.classList.remove('pending');
      }
    };
    li.appendChild(editBtn);

    // optimistic delete (TASK 3): remove from DOM first, restore on error
    const delBtn = document.createElement('button');
    delBtn.textContent = 'Delete';
    delBtn.onclick = async () => {
      const nextSibling = li.nextSibling;
      li.remove();
      try {
        await fetchJSON(`/notes/${n.id}`, { method: 'DELETE' });
      } catch (err) {
        list.insertBefore(li, nextSibling); // rollback
        alert(`Delete failed, restored: ${err.message}`);
      }
    };
    li.appendChild(delBtn);

    list.appendChild(li);
  }

  // result count + prev/next pagination (TASK 2)
  const pages = Math.max(1, Math.ceil(body.total / notesState.pageSize));
  document.getElementById('notes-count').textContent =
    `${body.total} result(s) — page ${notesState.page}/${pages}`;

  const pager = document.getElementById('notes-pager');
  pager.innerHTML = '';
  const prevBtn = document.createElement('button');
  prevBtn.textContent = '‹ Prev';
  prevBtn.disabled = notesState.page <= 1;
  prevBtn.onclick = () => { notesState.page--; loadNotes(); };
  const nextBtn = document.createElement('button');
  nextBtn.textContent = 'Next ›';
  nextBtn.disabled = notesState.page >= pages;
  nextBtn.onclick = () => { notesState.page++; loadNotes(); };
  pager.appendChild(prevBtn);
  pager.appendChild(nextBtn);
}

function initNotesControls() {
  const searchForm = document.getElementById('search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      notesState.q = document.getElementById('search-input').value.trim();
      notesState.page = 1;
      loadNotes();
    });
    const sortSel = document.getElementById('sort-select');
    sortSel.addEventListener('change', () => {
      notesState.sort = sortSel.value;
      notesState.page = 1;
      loadNotes();
    });
  }

  const noteForm = document.getElementById('note-form');
  if (noteForm) {
    noteForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const title = document.getElementById('note-title').value;
      const content = document.getElementById('note-content').value;
      try {
        await fetchJSON('/notes/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, content }),
        });
        e.target.reset();
        notesState.page = 1;
        loadNotes();
      } catch (err) {
        alert(`Create failed: ${err.message}`);
      }
    });
  }
}

// ================= Actions section =================
// (baseline behavior — extended by agent-actions in a separate branch)

async function loadActions() {
  const list = document.getElementById('actions');
  if (!list) return;
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

function initActionControls() {
  const actionForm = document.getElementById('action-form');
  if (!actionForm) return;
  actionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const description = document.getElementById('action-desc').value;
    try {
      await fetchJSON('/action-items/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description }),
      });
      e.target.reset();
      loadActions();
    } catch (err) {
      alert(`Create failed: ${err.message}`);
    }
  });
}

window.addEventListener('DOMContentLoaded', () => {
  initNotesControls();
  initActionControls();
  loadNotes();
  loadActions();
});
