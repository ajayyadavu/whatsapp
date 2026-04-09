// // Session management
// export const SESSION_KEY = 'swaran_session_id';

// export const getSessionId = () => {
//   let id = localStorage.getItem(SESSION_KEY);
//   if (!id) {
//     id = 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2);
//     localStorage.setItem(SESSION_KEY, id);
//   }
//   return id;
// };

// // UTM Parameters
// export const getUTMParams = () => {
//   const urlParams = new URLSearchParams(window.location.search);
//   return {
//     utm_source: urlParams.get('utm_source') || '',
//     utm_medium: urlParams.get('utm_medium') || '',
//     utm_campaign: urlParams.get('utm_campaign') || '',
//   };
// };

// // Default settings
// export const defaultSettings = {
//   theme: 'light',
//   fontSize: 14,
//   enterToSend: true,
//   streaming: true,
//   responseLength: 'balanced',
// };

// Session management
export const SESSION_KEY = 'swaran_session_id';

export const getSessionId = () => {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2);
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
};

// Clear session (call this on logout if needed)
export const clearSession = () => {
  localStorage.removeItem(SESSION_KEY);
};

// UTM Parameters
export const getUTMParams = () => {
  const urlParams = new URLSearchParams(window.location.search);
  return {
    utm_source: urlParams.get('utm_source') || '',
    utm_medium: urlParams.get('utm_medium') || '',
    utm_campaign: urlParams.get('utm_campaign') || '',
  };
};

// Default settings
export const defaultSettings = {
  theme: 'light',
  fontSize: 14,
  enterToSend: true,
  streaming: true,
  responseLength: 'balanced',
};