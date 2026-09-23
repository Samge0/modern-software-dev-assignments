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

// ================= Actions section (TASK 4/8) =================
// completion filter + bulk-complete UI, paginated envelope

const actionsState = { completed: '', page: 1, pageSize: 10, selected: new Set() };

async function loadActions() {
  const list = document.getElementById('actions');
  if (!list) return;
  list.innerHTML = '';
  actionsState.selected.clear();

  const params = new URLSearchParams({
    page: String(actionsState.page),
    page_size: String(actionsState.pageSize),
  });
  if (actionsState.completed !== '') params.set('completed', actionsState.completed);

  const body = await fetchJSON(`/action-items/?${params}`);

  // "select all open" bulk action bar (TASK 4)
  const bulkBar = document.getElementById('actions-bulk');
  if (bulkBar) {
    const openItems = body.items.filter((a) => !a.completed);
    const bulkBtn = bulkBar.querySelector('button');
    bulkBtn.disabled = openItems.length === 0;
    bulkBtn.textContent = `Bulk complete selected (${openItems.length} open on page)`;
  }

  for (const a of body.items) {
    const li = document.createElement('li');

    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.disabled = a.completed; // only open items are bulk-completable
    cb.onchange = () => {
      if (cb.checked) actionsState.selected.add(a.id);
      else actionsState.selected.delete(a.id);
    };
    li.appendChild(cb);

    const span = document.createElement('span');
    span.textContent = `${a.description} [${a.completed ? 'done' : 'open'}]`;
    li.appendChild(span);

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

  // filter toggle + pager (TASK 4/8)
  const counter = document.getElementById('actions-count');
  if (counter) {
    const pages = Math.max(1, Math.ceil(body.total / actionsState.pageSize));
    counter.textContent = `${body.total} item(s) — page ${actionsState.page}/${pages}`;
  }
  const pager = document.getElementById('actions-pager');
  if (pager) {
    pager.innerHTML = '';
    const pages = Math.max(1, Math.ceil(body.total / actionsState.pageSize));
    const prev = document.createElement('button');
    prev.textContent = '‹ Prev';
    prev.disabled = actionsState.page <= 1;
    prev.onclick = () => { actionsState.page--; loadActions(); };
    const next = document.createElement('button');
    next.textContent = 'Next ›';
    next.disabled = actionsState.page >= pages;
    next.onclick = () => { actionsState.page++; loadActions(); };
    pager.appendChild(prev);
    pager.appendChild(next);
  }
}

function initActionControls() {
  const actionForm = document.getElementById('action-form');
  if (actionForm) {
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

  // completion filter (TASK 4): '' = all, 'false' = open, 'true' = done
  const filterSel = document.getElementById('actions-filter');
  if (filterSel) {
    filterSel.addEventListener('change', () => {
      actionsState.completed = filterSel.value;
      actionsState.page = 1;
      loadActions();
    });
  }

  const bulkBar = document.getElementById('actions-bulk');
  if (bulkBar) {
    const bulkBtn = bulkBar.querySelector('button');
    bulkBtn.addEventListener('click', async () => {
      const ids = [...actionsState.selected];
      if (ids.length === 0) {
        // nothing selected: default to every open item on the current page
        const params = new URLSearchParams({
          completed: 'false',
          page: String(actionsState.page),
          page_size: String(actionsState.pageSize),
        });
        const body = await fetchJSON(`/action-items/?${params}`);
        ids.push(...body.items.map((a) => a.id));
      }
      if (ids.length === 0) return;
      try {
        const res = await fetchJSON('/action-items/bulk-complete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ids }),
        });
        console.info(`bulk completed ${res.updated_count} item(s)`);
        loadActions();
      } catch (err) {
        alert(`Bulk complete failed (transaction rolled back): ${err.message}`);
      }
    });
  }
}

window.addEventListener('DOMContentLoaded', () => {
  initNotesControls();
  initActionControls();
  loadNotes();
  loadActions();
});
