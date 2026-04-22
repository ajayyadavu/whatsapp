import React from 'react';
import './Chatbot.css';

// ── WhatsApp-style text formatter ─────────────────────────────────────────────
// Handles: *bold*, _italic_ (single words only), URLs, emails
// Special case: _(some text)_ → render full phrase as italic (footer lines)
const formatWhatsAppText = (text) => {
  if (!text) return null;

  // Tokeniser — processes one segment of plain text into React nodes
  const tokenise = (str) => {
    const tokens = [];
    // Order matters: URL first (greedy), then email, then *bold*, then _italic_
    const PATTERN = /(https?:\/\/[^\s]+)|([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)|(\*[^*\n]+\*)|(_\([^)]+\)_)|(_\S+_)/g;

    let lastIndex = 0;
    let match;

    while ((match = PATTERN.exec(str)) !== null) {
      // plain text before this token
      if (match.index > lastIndex) {
        tokens.push({ type: 'plain', value: str.slice(lastIndex, match.index) });
      }

      const [full, url, email, bold, italicPhrase, italicWord] = match;

      if (url) {
        tokens.push({ type: 'url', value: url });
      } else if (email) {
        tokens.push({ type: 'email', value: email });
      } else if (bold) {
        tokens.push({ type: 'bold', value: bold.slice(1, -1) });
      } else if (italicPhrase) {
        // _(some phrase)_ — strip leading _ and trailing _
        tokens.push({ type: 'italic', value: italicPhrase.slice(1, -1) });
      } else if (italicWord) {
        // _word_ — single word italic
        tokens.push({ type: 'italic', value: italicWord.slice(1, -1) });
      } else {
        tokens.push({ type: 'plain', value: full });
      }

      lastIndex = match.index + full.length;
    }

    // remainder
    if (lastIndex < str.length) {
      tokens.push({ type: 'plain', value: str.slice(lastIndex) });
    }
    return tokens;
  };

  const tokens = tokenise(text);

  return tokens.map((tok, i) => {
    switch (tok.type) {
      case 'bold':
        return <strong key={i}>{tok.value}</strong>;
      case 'italic':
        // Recursively format the inner content (may contain *bold* etc.)
        return <em key={i}>{formatWhatsAppText(tok.value)}</em>;
      case 'url':
        return (
          <a
            key={i}
            href={tok.value}
            target="_blank"
            rel="noopener noreferrer"
            className="message-link"
            onClick={(e) => e.stopPropagation()}
          >
            {tok.value}
          </a>
        );
      case 'email':
        return (
          <a key={i} href={`mailto:${tok.value}`} className="message-link">
            {tok.value}
          </a>
        );
      default:
        return tok.value;
    }
  });
};

// ── Render a single line ───────────────────────────────────────────────────────
const FormattedLine = ({ line }) => <>{formatWhatsAppText(line)}</>;

// ── Full message: split on newlines, preserve blank lines ─────────────────────
const FormattedText = ({ text }) => {
  if (!text) return null;
  const lines = text.split('\n');
  return (
    <>
      {lines.map((line, i) => (
        <React.Fragment key={i}>
          <FormattedLine line={line} />
          {i < lines.length - 1 && <br />}
        </React.Fragment>
      ))}
    </>
  );
};

// ── Get user initial from localStorage ────────────────────────────────────────
const getUserInitial = () => {
  try {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      return user?.username?.charAt(0).toUpperCase() || 'U';
    }
  } catch (e) {
    // ignore
  }
  return 'U';
};

// ── Google Calendar-style Meet Card ──────────────────────────────────────────
const MeetCard = ({ meetLink, slotStr, service, name }) => {
  // Parse slot string like "Tuesday, 15 Apr at 3:00 PM IST"
  const parts = slotStr ? slotStr.replace(' IST', '').split(' at ') : [];
  const dateLabel = parts[0] || '';
  const timeLabel = parts[1] || '';

  return (
    <div className="gcal-meet-card">
      {/* Header bar — mimics Google Calendar green event */}
      <div className="gcal-header">
        <div className="gcal-header-left">
          <span className="gcal-dot" />
          <span className="gcal-event-title">📹 {service || 'Discovery Call'} — Swaran Soft</span>
        </div>
        <span className="gcal-badge">Confirmed</span>
      </div>

      {/* Date & time block */}
      <div className="gcal-datetime">
        <div className="gcal-date-col">
          <div className="gcal-month">
            {dateLabel.split(' ')[2] || 'Apr'}
          </div>
          <div className="gcal-day-num">
            {dateLabel.split(' ')[1]?.replace(',', '') || '--'}
          </div>
          <div className="gcal-weekday">
            {dateLabel.split(',')[0] || ''}
          </div>
        </div>
        <div className="gcal-divider-v" />
        <div className="gcal-time-col">
          <div className="gcal-time">{timeLabel}</div>
          <div className="gcal-duration">15 min · Google Meet</div>
          {name && <div className="gcal-guest">👤 {name}</div>}
        </div>
      </div>

      {/* Join button */}
      <a
        href={meetLink}
        target="_blank"
        rel="noopener noreferrer"
        className="gcal-join-btn"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <polygon points="23 7 16 12 23 17 23 7" />
          <rect x="1" y="5" width="15" height="14" rx="2" />
        </svg>
        Join Google Meet
      </a>

      <div className="gcal-footer">📧 Calendar invite sent to your email</div>
    </div>
  );
};

// ── Detect Meet card in bot message ───────────────────────────────────────────
const extractMeetInfo = (text) => {
  if (!text) return null;
  // Must have a meet.google.com link AND a slot pattern
  const linkMatch = text.match(/(https:\/\/meet\.google\.com\/[a-z-]+)/i);
  const slotMatch = text.match(/([A-Za-z]+,\s+\d+\s+[A-Za-z]+\s+at\s+\d+:\d+\s+[APM]+\s+IST)/i);
  if (!linkMatch) return null;
  // Extract service name
  const serviceMatch = text.match(/\*([^*]+)\*.*[Mm]eet|[Mm]eet.*\*([^*]+)\*/);
  const service = serviceMatch ? (serviceMatch[1] || serviceMatch[2]) : null;
  return {
    meetLink: linkMatch[1],
    slotStr: slotMatch ? slotMatch[1] : '',
    service,
  };
};

// ── ChatMessage ────────────────────────────────────────────────────────────────
const extractCalendlyLink = (text) => {
  if (!text) return null;
  const match = text.match(/(https?:\/\/(?:www\.)?calendly\.com\/[^\s]+)/i);
  return match ? match[1] : null;
};

const ChatMessage = ({ message }) => {
  const { role, text, isStreaming, isError, isSuccess } = message;
  const displayText = typeof text === 'string' ? text : (text ? JSON.stringify(text) : '');

  // Check for meet card
  const meetInfo = role === 'bot' ? extractMeetInfo(displayText) : null;
  const calendlyLink = role === 'bot' ? extractCalendlyLink(displayText) : null;

  // Typing indicator — empty streaming message
  if (isStreaming && !displayText) {
    return (
      <div className={`message ${role}`}>
        <div className="message-avatar">
          {role === 'user' ? getUserInitial() : '🤖'}
        </div>
        <div className="typing-indicator">
          <span /><span /><span />
        </div>
      </div>
    );
  }

  if (!displayText && !isStreaming) return null;

  return (
    <div className={`message ${role} ${isError ? 'error' : ''} ${isSuccess ? 'success' : ''}`}>
      <div className="message-avatar">
        {role === 'user' ? getUserInitial() : '🤖'}
      </div>
      <div className="message-content">
        <FormattedText text={displayText} />
        {isStreaming && <span className="cursor-blink">▌</span>}
        {calendlyLink && !isStreaming && !meetInfo && (
          <a
            href={calendlyLink}
            target="_blank"
            rel="noopener noreferrer"
            className="meeting-cta-btn"
          >
            📅 Book a 15-min Meeting
          </a>
        )}
        {/* Google Calendar-style Meet Card */}
        {meetInfo && !isStreaming && (
          <MeetCard
            meetLink={meetInfo.meetLink}
            slotStr={meetInfo.slotStr}
            service={meetInfo.service}
            name={message.userName}
          />
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
