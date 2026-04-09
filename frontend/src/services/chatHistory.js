// Chat History Service - stores chat history in localStorage

const CHAT_HISTORY_KEY = 'chat_history';

// Get all chat history
export const getChatHistory = () => {
  const history = localStorage.getItem(CHAT_HISTORY_KEY);
  return history ? JSON.parse(history) : [];
};

// Save chat history
export const saveChatHistory = (history) => {
  localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(history));
};

// Add a new chat session
export const addChatSession = (session) => {
  const history = getChatHistory();
  const newSession = {
    id: Date.now(),
    title: session.title || 'New Chat',
    messages: session.messages || [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    preview: session.preview || ''
  };
  history.unshift(newSession);
  saveChatHistory(history);
  return newSession;
};

// Update existing chat session
export const updateChatSession = (sessionId, updates) => {
  const history = getChatHistory();
  const index = history.findIndex(s => s.id === sessionId);
  if (index !== -1) {
    history[index] = { ...history[index], ...updates, updatedAt: new Date().toISOString() };
    saveChatHistory(history);
    return history[index];
  }
  return null;
};

// Delete a chat session
export const deleteChatSession = (sessionId) => {
  const history = getChatHistory();
  const filtered = history.filter(s => s.id !== sessionId);
  saveChatHistory(filtered);
  return filtered;
};

// Delete all chat history
export const deleteAllChatSessions = () => {
  saveChatHistory([]);
  return [];
};

// Get current active session
export const getActiveSession = () => {
  const active = localStorage.getItem('active_chat_session');
  return active ? JSON.parse(active) : null;
};

// Set active session
export const setActiveSession = (session) => {
  localStorage.setItem('active_chat_session', JSON.stringify(session));
};

// Clear active session
export const clearActiveSession = () => {
  localStorage.removeItem('active_chat_session');
};