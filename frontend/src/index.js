// This file is unused. Vite uses src/main.jsx as the entry point.
// Do not add render logic here.

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

// Clear session when browser is closed (optional)
window.addEventListener('beforeunload', () => {
  // Don't clear on refresh, only on close
  // This is optional - remove if not needed
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);