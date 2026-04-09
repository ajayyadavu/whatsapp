import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Logs.css';

const LIMIT = 50;

const INTENT_COLORS = {
  greeting:     '#10b981',
  returning:    '#3b82f6',
  name_capture: '#8b5cf6',
  services:     '#f59e0b',
  meet:         '#ec4899',
  answer:       '#6366f1',
  off_topic:    '#ef4444',
};

const LogsPage = () => {
  const { user, isAdmin } = useAuth();
  const navigate          = useNavigate();

  const [logs,          setLogs]          = useState([]);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState(null);
  const [hasMore,       setHasMore]       = useState(false);
  const [filterSession, setFilterSession] = useState('');
  const [filterUser,    setFilterUser]    = useState('');
  const [selected,      setSelected]      = useState(null);

  const offsetRef = useRef(0);

  // Redirect non-admins
  useEffect(() => {
    if (user && !isAdmin) navigate('/');
  }, [user, isAdmin, navigate]);

  // Initial load
  useEffect(() => {
    if (isAdmin) doFetch(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  async function doFetch(reset, sessionFilter, userFilter) {
    const sid = sessionFilter !== undefined ? sessionFilter : filterSession;
    const uid = userFilter    !== undefined ? userFilter    : filterUser;

    setLoading(true);
    setError(null);

    const offset = reset ? 0 : offsetRef.current;

    const params = { skip: offset, limit: LIMIT };
    if (sid.trim()) params.session_id = sid.trim();
    if (uid.trim()) params.username   = uid.trim();

    try {
      const res  = await api.get('/logs/', { params });
      const data = res.data;

      setLogs(prev => reset ? data : [...prev, ...data]);
      offsetRef.current = offset + data.length;
      setHasMore(data.length === LIMIT);
    } catch (e) {
      const msg =
        e.response?.data?.detail ||
        e.response?.data?.message ||
        e.message ||
        'Failed to fetch logs';
      setError(msg);
      console.error('[LOGS ERROR]', e);
    } finally {
      setLoading(false);
    }
  }

  const handleSearch = (e) => {
    e.preventDefault();
    offsetRef.current = 0;
    doFetch(true, filterSession, filterUser);
  };

  const handleClear = () => {
    setFilterSession('');
    setFilterUser('');
    offsetRef.current = 0;
    doFetch(true, '', '');
  };

  if (!isAdmin) return null;

  return (
    <div className="logs-page">
      <div className="logs-header">
        <div>
          <h1 className="logs-title">Chat Logs</h1>
          <p className="logs-subtitle">
            {logs.length} record{logs.length !== 1 ? 's' : ''} loaded — admin view only
          </p>
        </div>
        <button
          className="logs-refresh-btn"
          onClick={() => { offsetRef.current = 0; doFetch(true); }}
          disabled={loading}
        >
          ↻ Refresh
        </button>
      </div>

      {/* Filters */}
      <form className="logs-filters" onSubmit={handleSearch}>
        <input
          className="logs-input"
          placeholder="Filter by session ID…"
          value={filterSession}
          onChange={e => setFilterSession(e.target.value)}
        />
        <input
          className="logs-input"
          placeholder="Filter by username…"
          value={filterUser}
          onChange={e => setFilterUser(e.target.value)}
        />
        <button type="submit" className="logs-search-btn" disabled={loading}>
          Search
        </button>
        <button
          type="button"
          className="logs-clear-btn"
          onClick={handleClear}
          disabled={loading}
        >
          Clear
        </button>
      </form>

      {error && (
        <div className="logs-error">
          ⚠ {error}
          <button
            style={{ marginLeft: 12, fontSize: 12, cursor: 'pointer' }}
            onClick={() => { offsetRef.current = 0; doFetch(true); }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Table */}
      <div className="logs-table-wrap">
        <table className="logs-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Timestamp</th>
              <th>Username</th>
              <th>IP Address</th>
              <th>Intent</th>
              <th>Query</th>
              <th>Response</th>
              <th>Session ID</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 && !loading && (
              <tr>
                <td colSpan={8} className="logs-empty">No logs found.</td>
              </tr>
            )}
            {logs.map((log) => (
              <tr
                key={log.id}
                className={`logs-row ${selected === log.id ? 'selected' : ''}`}
                onClick={() => setSelected(selected === log.id ? null : log.id)}
              >
                <td className="logs-cell-id">{log.id}</td>
                <td className="logs-cell-ts">
                  {log.timestamp
                    ? new Date(log.timestamp).toLocaleString()
                    : '—'}
                </td>
                <td className="logs-cell">{log.username || '—'}</td>
                <td className="logs-cell-ip">{log.ip_address || '—'}</td>
                <td className="logs-cell-intent">
                  <span
                    className="intent-badge"
                    style={{ background: INTENT_COLORS[log.intent] || '#94a3b8' }}
                  >
                    {log.intent || '—'}
                  </span>
                </td>
                <td className="logs-cell-query">{log.query}</td>
                <td className="logs-cell-response">
                  {selected === log.id
                    ? log.response
                    : ((log.response || '').slice(0, 80) +
                       ((log.response || '').length > 80 ? '…' : ''))}
                </td>
                <td className="logs-cell-session">{log.session_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {loading && <div className="logs-loading">Loading…</div>}
      {hasMore && !loading && (
        <button className="logs-load-more" onClick={() => doFetch(false)}>
          Load more
        </button>
      )}
    </div>
  );
};

export default LogsPage;
