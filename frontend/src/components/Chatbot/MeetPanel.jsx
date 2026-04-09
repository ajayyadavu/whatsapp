import React from 'react';
import './MeetPanel.css';

/**
 * MeetPanel — slides in from the right when a Google Meet booking
 * intent is detected or when the user clicks "Book a Meet" manually.
 *
 * Props:
 *   isOpen      {boolean}  controls visibility
 *   onClose     {fn}       called when the X is clicked
 *   payload     {object}   meet data from the backend __SIGNALS__ header
 *                          { calendar_link, title, duration, host_email,
 *                            user_name, contact }
 */
const MeetPanel = ({ isOpen, onClose, payload }) => {
  // Build a default Google Calendar link when no backend payload exists
  const getDefaultLink = () => {
    const t = new Date();
    t.setDate(t.getDate() + 1);
    t.setHours(4, 30, 0, 0); // 10 AM IST = 04:30 UTC
    const end = new Date(t.getTime() + 30 * 60000);
    const fmt = (d) =>
      d.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    const p = new URLSearchParams({
      action: 'TEMPLATE',
      text: 'Discovery Call with Swaran Soft',
      details:
        '30-minute discovery call with the Swaran Soft enterprise AI team.',
      dates: `${fmt(t)}/${fmt(end)}`,
      add: 'info@swaransoft.com',
      sf: 'true',
      output: 'xml',
    });
    return 'https://calendar.google.com/calendar/render?' + p.toString();
  };

  const calendarLink = payload?.calendar_link || getDefaultLink();
  const title        = payload?.title       || 'Discovery Call with Swaran Soft';
  const hostEmail    = payload?.host_email  || 'info@swaransoft.com';
  const userName     = payload?.user_name   || '';
  const isReady      = !!payload?.calendar_link;

  const subtitle = userName
    ? `Hi ${userName}! Your 30-min discovery call is pre-filled in Google Calendar — click below to confirm.`
    : 'Connect with our enterprise AI team and explore how we can help your organization.';

  return (
    <div className={`meet-panel ${isOpen ? 'open' : ''}`}>
      <div className="meet-panel-inner">
        {/* Header */}
        <div className="meet-panel-header">
          <h4 className="meet-panel-title">📅 Book a Meet</h4>
          <button className="meet-close-btn" onClick={onClose} aria-label="Close">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Status badge */}
        <span className={`meet-badge ${isReady ? 'ready' : 'default'}`}>
          <span className="meet-badge-dot" />
          {isReady ? 'Calendar invite ready' : 'Ready to schedule'}
        </span>

        {/* Card */}
        <div className="meet-card">
          <div className="meet-card-title">{title}</div>
          <div className="meet-card-sub">{subtitle}</div>
        </div>

        {/* Info rows */}
        <div className="meet-info-list">
          <div className="meet-info-row">
            <ClockIcon />
            <span>30 minutes</span>
          </div>
          <div className="meet-info-row">
            <VideoIcon />
            <span>Google Meet (video call)</span>
          </div>
          <div className="meet-info-row">
            <CalendarIcon />
            <span>Tomorrow at 10:00 AM IST</span>
          </div>
          <div className="meet-info-row">
            <UserIcon />
            <span>{hostEmail}</span>
          </div>
        </div>

        {/* CTA */}
        <a
          href={calendarLink}
          target="_blank"
          rel="noopener noreferrer"
          className="meet-open-btn"
        >
          <CalendarIcon size={15} />
          Open Google Calendar
        </a>

        <hr className="meet-divider" />

        {/* Contact */}
        <div className="meet-contact">
          <p>Or reach us directly:</p>
          <a href={`mailto:${hostEmail}`}>{hostEmail}</a>
          <p>India: +91 9220-313-650</p>
          <p>UAE: +971-50-9292-650</p>
        </div>
      </div>
    </div>
  );
};

// ── Tiny inline SVG icons ────────────────────────────────────────────────────
const ClockIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.8">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
);

const VideoIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.8">
    <path d="M15 10l4.553-2.069A1 1 0 0121 8.845v6.31a1 1 0 01-1.447.894L15 14" />
    <rect x="3" y="6" width="12" height="12" rx="2" />
  </svg>
);

const CalendarIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.8">
    <rect x="3" y="4" width="18" height="18" rx="2" />
    <line x1="16" y1="2" x2="16" y2="6" />
    <line x1="8" y1="2" x2="8" y2="6" />
    <line x1="3" y1="10" x2="21" y2="10" />
  </svg>
);

const UserIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.8">
    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);

export default MeetPanel;
