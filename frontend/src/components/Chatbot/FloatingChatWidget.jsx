import React, { useState, useRef, useEffect, useCallback } from 'react';
import { chatAPI } from '../../services/api';
import { getSessionId } from '../../utils/constants';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import './FloatingChatWidget.css';

const FloatingChatWidget = () => {
  const [isOpen, setIsOpen]         = useState(false);
  const [messages, setMessages]     = useState([]);
  const [isLoading, setIsLoading]   = useState(false);
  const [hasUnread, setHasUnread]   = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);

  const abortControllerRef = useRef(null);
  const chatContainerRef   = useRef(null);
  const sessionId          = getSessionId();

  // Auto-scroll
  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      if (chatContainerRef.current)
        chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }, 80);
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

  // Mark unread dot when closed and new bot message arrives
  useEffect(() => {
    if (!isOpen && messages.length > 0) {
      const last = messages[messages.length - 1];
      if (last.role === 'bot' && !last.isStreaming) {
        setHasUnread(true);
      }
    }
  }, [messages, isOpen]);

  const openChat = () => {
    setIsOpen(true);
    setHasUnread(false);
    setIsMinimized(false);
  };

  const closeChat = () => {
    setIsOpen(false);
  };

  const sendMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    const userMsg = {
      id: Date.now(), role: 'user',
      text: text.trim(), timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    if (abortControllerRef.current) abortControllerRef.current.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const botMsgId = Date.now() + 1;
    setMessages(prev => [
      ...prev,
      { id: botMsgId, role: 'bot', text: '', isStreaming: true },
    ]);

    try {
      const response = await chatAPI.flowChat(text, sessionId, controller.signal);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader  = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let fullText  = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;
        setMessages(prev =>
          prev.map(msg =>
            msg.id === botMsgId
              ? { ...msg, text: fullText, isStreaming: true }
              : msg
          )
        );
        scrollToBottom();
      }

      const finalText = fullText.trim() || 'No response received.';
      setMessages(prev =>
        prev.map(msg =>
          msg.id === botMsgId
            ? { ...msg, text: finalText, isStreaming: false }
            : msg
        )
      );
    } catch (error) {
      if (error.name !== 'AbortError') {
        setMessages(prev =>
          prev.map(msg =>
            msg.id === botMsgId
              ? {
                  ...msg,
                  text: 'Error: Could not reach the backend. Please try again.',
                  isStreaming: false,
                  isError: true,
                }
              : msg
          )
        );
      } else {
        setMessages(prev => prev.filter(msg => msg.id !== botMsgId));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    if (abortControllerRef.current) abortControllerRef.current.abort();
    setMessages([]);
    setIsLoading(false);
  };

  return (
    <div className="fcw-root">
      {/* Chat Panel */}
      {isOpen && (
        <div className={`fcw-panel ${isMinimized ? 'fcw-minimized' : ''}`}>
          {/* Header */}
          <div className="fcw-header">
            <div className="fcw-header-left">
              <div className="fcw-avatar">🤖</div>
              <div>
                <div className="fcw-title">Swaran AI</div>
                <div className="fcw-status">● Online</div>
              </div>
            </div>
            <div className="fcw-header-actions">
              {messages.length > 0 && (
                <button className="fcw-action-btn" onClick={clearChat} title="Clear chat">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
                    <path d="M10 11v6M14 11v6" />
                  </svg>
                </button>
              )}
              <button
                className="fcw-action-btn"
                onClick={() => setIsMinimized(m => !m)}
                title={isMinimized ? 'Expand' : 'Minimize'}
              >
                {isMinimized ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="18 15 12 9 6 15" />
                  </svg>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                )}
              </button>
              <button className="fcw-action-btn fcw-close-btn" onClick={closeChat} title="Close">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages */}
          {!isMinimized && (
            <>
              <div className="fcw-messages" ref={chatContainerRef}>
                {messages.length === 0 ? (
                  <div className="fcw-empty">
                    <div className="fcw-empty-icon">🤖</div>
                    <p className="fcw-empty-title">Hi! I'm Swaran AI 👋</p>
                    <p className="fcw-empty-sub">How can I help you today?</p>
                    <div className="fcw-suggestions">
                      <button onClick={() => sendMessage('Hi')}>👋 Hi</button>
                      <button onClick={() => sendMessage('What services do you offer?')}>Our Services</button>
                      <button onClick={() => sendMessage('Tell me about AI Consulting')}>AI Consulting</button>
                    </div>
                  </div>
                ) : (
                  messages.map(msg => <ChatMessage key={msg.id} message={msg} />)
                )}
              </div>
              <ChatInput onSend={sendMessage} disabled={isLoading} />
            </>
          )}
        </div>
      )}

      {/* FAB Toggle Button */}
      <button
        className={`fcw-fab ${isOpen ? 'fcw-fab-open' : ''}`}
        onClick={isOpen ? closeChat : openChat}
        title={isOpen ? 'Close chat' : 'Chat with Swaran AI'}
      >
        {hasUnread && !isOpen && <span className="fcw-unread-dot" />}
        {isOpen ? (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          </svg>
        )}
      </button>
    </div>
  );
};

export default FloatingChatWidget;
