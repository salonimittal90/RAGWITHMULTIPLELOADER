const statusEl = document.getElementById('status');
const chatOutputEl = document.getElementById('chat-output');
const threadsOutputEl = document.getElementById('threads-output');
const threadIdInput = document.getElementById('thread-id');

function setStatus(message, type = 'info') {
  statusEl.className = `status ${type}`;
  statusEl.textContent = message;
}

function renderMessage(text, title = 'Answer') {
  const card = document.createElement('div');
  card.className = 'chat-bubble';
  card.innerHTML = `<strong>${title}</strong><div>${text}</div>`;
  chatOutputEl.prepend(card);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = typeof payload === 'object' && payload !== null ? payload.detail || payload.message : payload;
    throw new Error(detail || 'Request failed');
  }

  return payload;
}

document.getElementById('url-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const source = document.getElementById('source-url').value.trim();
  const sourceType = document.getElementById('source-type').value;

  try {
    setStatus('Loading content from the requested source...', 'info');
    const result = await requestJson(`/load_url?source=${encodeURIComponent(source)}&source_type=${encodeURIComponent(sourceType)}`, {
      method: 'POST',
    });
    setStatus(`Loaded successfully: ${result.message}`, 'success');
  } catch (error) {
    setStatus(error.message, 'error');
  }
});

document.getElementById('file-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const fileInput = document.getElementById('document-file');
  const file = fileInput.files[0];

  if (!file) {
    setStatus('Please choose a file to upload.', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    setStatus('Uploading file and indexing content...', 'info');
    const result = await requestJson('/load_file', {
      method: 'POST',
      body: formData,
    });
    setStatus(`File loaded successfully: ${result.message}`, 'success');
  } catch (error) {
    setStatus(error.message, 'error');
  }
});

document.getElementById('chat-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = document.getElementById('question').value.trim();
  const userEmail = document.getElementById('user-email').value.trim();
  const threadId = (threadIdInput.value || `thread-${Date.now()}`).trim();

  if (!question || !userEmail) {
    setStatus('Please enter a question and email.', 'error');
    return;
  }

  try {
    setStatus('Generating an answer...', 'info');
    const result = await requestJson('/ai/ask_question', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, thread_id: threadId, user_email: userEmail }),
    });
    threadIdInput.value = result.thread_id || threadId;
    renderMessage(result.content || 'No answer returned.', 'Answer');
    setStatus('Answer generated successfully.', 'success');
  } catch (error) {
    setStatus(error.message, 'error');
  }
});

async function loadRecentThreads() {
  try {
    const result = await requestJson('/cp/get_recent_threads');
    threadsOutputEl.innerHTML = '';

    if (!result.recent_threads || result.recent_threads.length === 0) {
      threadsOutputEl.innerHTML = '<div class="thread-item">No recent sessions found yet.</div>';
      return;
    }

    result.recent_threads.recent_threads.forEach((thread) => {
      const item = document.createElement('div');
      item.className = 'thread-item';
      item.style.display = 'flex';
      item.style.justifyContent = 'space-between';
      item.style.alignItems = 'center';

      const info = document.createElement('div');
      info.innerHTML = `
        <strong>${thread.thread_id || 'Unknown thread'}</strong>
        <div>${thread.email ? `Email: ${thread.email}` : 'Email not available'}</div>
      `;

      const btn = document.createElement('button');
      btn.textContent = 'View history';
      btn.className = 'history-button';
      btn.addEventListener('click', () => {
        loadThreadHistory(thread.thread_id, thread.email);
      });

      item.appendChild(info);
      item.appendChild(btn);
      threadsOutputEl.appendChild(item);
    });
  } catch (error) {
    threadsOutputEl.innerHTML = `<div class="thread-item">${error.message}</div>`;
  }
}

async function loadThreadHistory(threadId, email) {
  if (!threadId || !email) {
    setStatus('Thread ID and email are required.', 'error');
    return;
  }

  try {
    setStatus('Loading thread history...', 'info');
    const result = await requestJson(`/cp/latest_checkpoint_qa?thread_id=${encodeURIComponent(threadId)}&user_email=${encodeURIComponent(email)}`);
    const pairs = result.qa_pairs || [];

    if (pairs.length === 0) {
      setStatus('No Q/A history found for this thread.', 'error');
      return;
    }

    chatOutputEl.innerHTML = '';
    pairs.forEach(({ question, answer }) => {
      renderMessage(answer, question);
    });
    setStatus('Thread history loaded.', 'success');
  } catch (error) {
    setStatus(error.message, 'error');
  }
}

document.getElementById('recent-btn').addEventListener('click', loadRecentThreads);
loadRecentThreads();
