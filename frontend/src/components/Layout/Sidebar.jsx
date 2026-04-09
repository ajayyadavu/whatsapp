import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { 
  getChatHistory, 
  deleteChatSession, 
  deleteAllChatSessions,
  setActiveSession,
  clearActiveSession
} from '../../services/chatHistory';
import './Sidebar.css';

const Sidebar = ({ isOpen, onClose, activeTab, setActiveTab, isAdmin, onSessionChange }) => {
  const [chatHistory, setChatHistory] = useState([]);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Load chat history from localStorage
  useEffect(() => {
    loadChatHistory();
  }, []);

  const loadChatHistory = () => {
    const history = getChatHistory();
    setChatHistory(history);
  };

  const handleSessionClick = (session) => {
    // Load the selected session
    setActiveSession(session);
    if (onSessionChange) {
      onSessionChange(session);
    }
    if (onClose) {
      onClose();
    }
  };

  const handleDeleteSession = (sessionId, e) => {
    e.stopPropagation();
    setShowDeleteConfirm(sessionId);
  };

  const confirmDelete = (sessionId) => {
    deleteChatSession(sessionId);
    loadChatHistory();
    setShowDeleteConfirm(null);
    
    // Clear active session if it was deleted
    const activeSession = JSON.parse(localStorage.getItem('active_chat_session') || '{}');
    if (activeSession.id === sessionId) {
      clearActiveSession();
      if (onSessionChange) {
        onSessionChange(null);
      }
    }
  };

  const handleDeleteAll = () => {
    if (window.confirm('Are you sure you want to delete all chat history? This cannot be undone.')) {
      deleteAllChatSessions();
      loadChatHistory();
      clearActiveSession();
      if (onSessionChange) {
        onSessionChange(null);
      }
    }
  };

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
    }
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  // Menu items
  const menuItems = [
    { id: 'chat',   label: 'Chat',       icon: '💬', visible: true },
    { id: 'upload', label: 'Upload PDF',  icon: '📄', visible: isAdmin },
    { id: 'logs',   label: 'Chat Logs',  icon: '📊', visible: isAdmin, route: '/logs' },
  ];

  const handleNavClick = (item) => {
    if (item.route) {
      navigate(item.route);
    } else if (setActiveTab) {
      setActiveTab(item.id);
    }
    if (onClose) onClose();
  };

  const handleOverlayClick = () => {
    if (onClose) {
      onClose();
    }
  };

  return (
    <>
      {isOpen && <div className="sidebar-overlay" onClick={handleOverlayClick} />}
      <div className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon"></span>
            <span className="logo-text">Swaran Soft AI Assistant</span>
          </div>
          {isAdmin && <span className="admin-badge">Admin</span>}
        </div>

        <nav className="sidebar-nav">
          {menuItems.map(item => item.visible && (
            <button
              key={item.id}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => handleNavClick(item)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="history-section">
          <div className="history-header">
            <div className="history-label">Recent Chats</div>
            {chatHistory.length > 0 && (
              <button className="delete-all-btn" onClick={handleDeleteAll} title="Delete all chats">
                🗑️
              </button>
            )}
          </div>
          <div className="history-list">
            {chatHistory.length === 0 ? (
              <div className="history-empty">No chats yet</div>
            ) : (
              chatHistory.map((chat) => (
                <div 
                  key={chat.id} 
                  className="history-item"
                  onClick={() => handleSessionClick(chat)}
                >
                  <div className="history-item-content">
                    <div className="history-question">{chat.title || 'New Chat'}</div>
                    <div className="history-preview">{chat.preview || 'Click to continue...'}</div>
                    <div className="history-time">{formatTime(chat.updatedAt || chat.createdAt)}</div>
                  </div>
                  <button 
                    className="history-delete-btn"
                    onClick={(e) => handleDeleteSession(chat.id, e)}
                    title="Delete this chat"
                  >
                    ✕
                  </button>
                  {showDeleteConfirm === chat.id && (
                    <div className="delete-confirm">
                      <span>Delete?</span>
                      <button onClick={(e) => { e.stopPropagation(); confirmDelete(chat.id); }}>Yes</button>
                      <button onClick={(e) => { e.stopPropagation(); setShowDeleteConfirm(null); }}>No</button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* User Profile Section at Bottom */}
        <div className="sidebar-footer">
          <div className="user-profile" onClick={() => setShowUserMenu(!showUserMenu)}>
            <div className="user-avatar">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="user-info">
              <div className="user-name">{user?.username || 'User'}</div>
              <div className="user-role">{isAdmin ? 'Administrator' : 'User'}</div>
            </div>
            <div className="user-arrow">{showUserMenu ? '▲' : '▼'}</div>
          </div>
          
          {showUserMenu && (
            <div className="user-menu">
              <button className="user-menu-item" onClick={handleLogout}>
                <span className="menu-icon">🚪</span>
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default Sidebar;