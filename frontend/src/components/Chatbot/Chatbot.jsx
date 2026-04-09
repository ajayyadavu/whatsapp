import React, { useState, useRef, useEffect, useCallback } from 'react';
import { chatAPI, leadAPI } from '../../services/api';
import { getSessionId, getUTMParams } from '../../utils/constants';
import {
  getChatHistory,
  addChatSession,
  updateChatSession,
  getActiveSession,
  setActiveSession,
  clearActiveSession,
} from '../../services/chatHistory';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import MeetPanel from './MeetPanel';
import LeadModal from '../Common/LeadModal';
import './Chatbot.css';

const Chatbot = () => {
  const [messages, setMessages]               = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [isLoading, setIsLoading]             = useState(false);
  const [showLeadModal, setShowLeadModal]     = useState(false);
  const [detectedSignals, setDetectedSignals] = useState([]);
  const [leadFormShown, setLeadFormShown]     = useState(false);
  const [messageCount, setMessageCount]       = useState(0);
  const [isInitialLoad, setIsInitialLoad]     = useState(true);
  const [meetPanelOpen, setMeetPanelOpen]     = useState(false);
  const [meetPayload, setMeetPayload]         = useState(null);

  const abortControllerRef = useRef(null);
  const chatContainerRef   = useRef(null);
  const sessionId          = getSessionId();
  const utmParams          = getUTMParams();

  // ── Restore session on mount ──────────────────────────────────────────────
  useEffect(() => {
    setIsInitialLoad(true);
    const activeSession = getActiveSession();
    if (activeSession?.messages?.length > 0) {
      setMessages(activeSession.messages);
      setCurrentSessionId(activeSession.id);
      setMessageCount(activeSession.messages.filter(m => m.role === 'user').length);
    } else {
      const history = getChatHistory();
      if (history.length > 0) {
        const recent = history[0];
        setMessages(recent.messages || []);
        setCurrentSessionId(recent.id);
        setMessageCount(recent.messages?.filter(m => m.role === 'user').length || 0);
        setActiveSession(recent);
      }
    }
    setIsInitialLoad(false);
  }, []);

  // ── Persist session on message change ────────────────────────────────────
  useEffect(() => {
    if (!isInitialLoad && messages.length > 0 && currentSessionId) {
      const firstUser = messages.find(m => m.role === 'user');
      const title   = firstUser?.text?.slice(0, 30) || 'Chat Session';
      const preview = messages[messages.length - 1]?.text?.slice(0, 50) || '';
      updateChatSession(currentSessionId, { messages, title, preview });
      setActiveSession({ id: currentSessionId, messages, title, preview });
    }
  }, [messages, currentSessionId, isInitialLoad]);

  // ── Auto-scroll ───────────────────────────────────────────────────────────
  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      if (chatContainerRef.current)
        chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }, 100);
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

  // ── Lead form logic (auto-popup disabled) ────────────────────────────────
  const checkLeadForm = useCallback((_signals, _count) => {
    // Book a Demo auto-popup disabled
  }, []);

  const handleLeadSubmit = async (leadData) => {
    try {
      const response = await leadAPI.submit({
        ...leadData,
        session_id: sessionId,
        buying_signals: detectedSignals,
        ...utmParams,
      });
      if (response.success) {
        setMessages(prev => [...prev, {
          id: Date.now(), role: 'bot',
          text: `✅ ${response.message}`, isSuccess: true,
        }]);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Lead submission error:', error);
      return false;
    }
  };

  // ── New / clear session ───────────────────────────────────────────────────
  const createNewSession = () => {
    if (messages.length > 0 && currentSessionId) {
      const firstUser = messages.find(m => m.role === 'user');
      updateChatSession(currentSessionId, {
        messages,
        title: firstUser?.text?.slice(0, 30) || 'Chat Session',
      });
    }
    setMessages([]);
    setCurrentSessionId(null);
    setMessageCount(0);
    setLeadFormShown(false);
    setDetectedSignals([]);
    setMeetPanelOpen(false);
    setMeetPayload(null);
    clearActiveSession();
  };

  // ── Core sendMessage ──────────────────────────────────────────────────────
  const sendMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    // Create session if none
    let sid = currentSessionId;
    if (!sid) {
      const newSession = addChatSession({
        title:    text.trim().slice(0, 30),
        messages: [],
        preview:  text.trim().slice(0, 50),
      });
      sid = newSession.id;
      setCurrentSessionId(sid);
    }

    const userMsg = {
      id: Date.now(), role: 'user',
      text: text.trim(), timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setMessageCount(prev => prev + 1);
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
      const response = await chatAPI.sendMessage(text, sessionId, controller.signal);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader   = response.body.getReader();
      const decoder  = new TextDecoder('utf-8');
      let fullText   = '';

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

      // ── Finalise ──────────────────────────────────────────────────────
      const finalText = fullText.trim() || 'No response received.';
      setMessages(prev =>
        prev.map(msg =>
          msg.id === botMsgId
            ? { ...msg, text: finalText, isStreaming: false }
            : msg
        )
      );

      // checkLeadForm disabled

    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Chat error:', error);
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

  // ── Render ────────────────────────────────────────────────────────────────
  if (isInitialLoad) {
    return (
      <div className="chatbot">
        <div className="chatbot-header"><h2>AI Assistant</h2></div>
        <div className="chat-messages">
          <div className="empty-state">
            <div className="empty-icon" />
            <h3>Loading your conversations…</h3>
          </div>
        </div>
        <ChatInput onSend={sendMessage} disabled />
      </div>
    );
  }

  return (
    <div className="chatbot-wrapper">
      {/* ── Main chat pane ──────────────────────────────────────────────── */}
      <div className="chatbot">
        <div className="chatbot-header">
          <h2>AI Assistant</h2>
          <div className="chatbot-header-actions">
            <a
              href="https://meet.google.com/new"
              target="_blank"
              rel="noopener noreferrer"
              className="book-meet-btn"
              title="Book a Google Meet"
            >
              📅 Book a Meet
            </a>
            {messages.length > 0 && (
              <button className="clear-chat-btn" onClick={createNewSession}>
                New Chat
              </button>
            )}
          </div>
        </div>

        <div className="chat-messages" ref={chatContainerRef}>
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon" />
              <h3>How can I help you today?</h3>
              <p>Ask me anything — powered by AI and ready to assist.</p>
              <div className="suggestions">
                <button onClick={() => sendMessage('What services does Swaran Soft offer?')}>
                  Our Services
                </button>
                <button onClick={() => sendMessage('Tell me about AI Consulting')}>
                  AI Consulting
                </button>
                <button onClick={() => sendMessage('Tell me about App Development')}>
                  App Development
                </button>
              </div>
            </div>
          ) : (
            messages.map(msg => <ChatMessage key={msg.id} message={msg} />)
          )}
        </div>

        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </div>

      {/* ── Meet panel (kept in code but never opened automatically) */}
      <MeetPanel
        isOpen={meetPanelOpen}
        onClose={() => setMeetPanelOpen(false)}
        payload={meetPayload}
      />

      {/* ── Lead modal (kept in code but never opened automatically) */}
      <LeadModal
        isOpen={showLeadModal}
        onClose={() => setShowLeadModal(false)}
        onSubmit={handleLeadSubmit}
      />
    </div>
  );
};

export default Chatbot;
