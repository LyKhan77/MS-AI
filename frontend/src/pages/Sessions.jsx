import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Sessions = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_sessions: 0,
    total_count: 0,
    avg_count: 0,
    sessions_today: 0
  });
  const [sessions, setSessions] = useState([]);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0
  });
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState(null);

  // Fetch stats on mount
  useEffect(() => {
    fetchStats();
  }, []);

  // Fetch sessions when page changes
  useEffect(() => {
    fetchSessions();
  }, [pagination.page]);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats/overview');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/sessions/list?page=${pagination.page}&per_page=${pagination.per_page}`
      );
      const data = await response.json();
      setSessions(data.sessions);
      setPagination(prev => ({
        ...prev,
        total: data.total,
        total_pages: data.total_pages
      }));
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (startTime, endTime) => {
    if (!endTime) return 'Active';
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diff = end - start;
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  };

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('id-ID', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="p-8 pb-12 h-full flex flex-col gap-8 overflow-y-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Sessions History</h1>
        <p className="text-gray-400">View and analyze past production sessions</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white/5 border border-white/10 p-4 rounded-lg backdrop-blur-sm">
          <div className="text-gray-400 text-sm">Total Sessions</div>
          <div className="text-3xl font-bold text-white mt-1">{stats.total_sessions}</div>
        </div>
        <div className="bg-white/5 border border-white/10 p-4 rounded-lg backdrop-blur-sm">
          <div className="text-gray-400 text-sm">Total Count</div>
          <div className="text-3xl font-bold text-white mt-1">{stats.total_count}</div>
        </div>
        <div className="bg-white/5 border border-white/10 p-4 rounded-lg backdrop-blur-sm">
          <div className="text-gray-400 text-sm">Average Count</div>
          <div className="text-3xl font-bold text-white mt-1">{stats.avg_count}</div>
        </div>
        <div className="bg-white/5 border border-white/10 p-4 rounded-lg backdrop-blur-sm">
          <div className="text-gray-400 text-sm">Today</div>
          <div className="text-3xl font-bold text-white mt-1">{stats.sessions_today}</div>
        </div>
      </div>

      {/* Sessions Table */}
      <div className="bg-white/5 border border-white/10 rounded-lg backdrop-blur-sm overflow-hidden flex-1 flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full">
            <thead className="bg-white/5 border-b border-white/10">
              <tr>
                <th className="text-left p-4 text-gray-300 font-semibold">Session Name</th>
                <th className="text-left p-4 text-gray-300 font-semibold">Date</th>
                <th className="text-left p-4 text-gray-300 font-semibold">Count</th>
                <th className="text-left p-4 text-gray-300 font-semibold">Duration</th>
                <th className="text-left p-4 text-gray-300 font-semibold">Status</th>
                <th className="text-left p-4 text-gray-300 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center p-8 text-gray-400">
                    Loading sessions...
                  </td>
                </tr>
              ) : sessions.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center p-8 text-gray-400">
                    No sessions found. Start a new session to begin tracking!
                  </td>
                </tr>
              ) : (
                sessions.map((session) => (
                  <tr 
                    key={session.id} 
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="p-4 text-white font-medium">{session.name}</td>
                    <td className="p-4 text-gray-300 text-sm">{formatDate(session.start_time)}</td>
                    <td className="p-4">
                      <span className={`font-mono ${
                        session.total_count >= session.max_count 
                          ? 'text-green-400' 
                          : 'text-yellow-400'
                      }`}>
                        {session.total_count} / {session.max_count}
                      </span>
                    </td>
                    <td className="p-4 text-gray-300 font-mono text-sm">
                      {formatDuration(session.start_time, session.end_time)}
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        session.status === 'completed' 
                          ? 'bg-green-500/20 text-green-400' 
                          : 'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {session.status}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => setSelectedSession(session)}
                          className="px-3 py-1 bg-primary hover:bg-secondary rounded text-white text-sm transition-colors"
                        >
                          View
                        </button>
                        <button
                          onClick={() => handleDelete(session.id)}
                          className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-white text-sm transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pagination.total_pages > 1 && (
          <div className="border-t border-white/10 p-4 flex justify-between items-center">
            <div className="text-sm text-gray-400">
              Page {pagination.page} of {pagination.total_pages} ({pagination.total} total)
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
                disabled={pagination.page === 1}
                className="px-3 py-1 bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed rounded text-white text-sm transition-colors"
              >
                Previous
              </button>
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: Math.min(prev.total_pages, prev.page + 1) }))}
                disabled={pagination.page === pagination.total_pages}
                className="px-3 py-1 bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed rounded text-white text-sm transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Session Detail Modal */}
      {selectedSession && (
        <SessionDetailModal
          session={selectedSession}
          onClose={() => setSelectedSession(null)}
        />
      )}
    </div>
  );
};

// Session Detail Modal Component
const SessionDetailModal = ({ session, onClose }) => {
  const [captures, setCaptures] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCaptures();
  }, []);

  const fetchCaptures = async () => {
    try {
      const response = await fetch(`/api/sessions/${session.id}/captures`);
      const data = await response.json();
      setCaptures(data.captures);
    } catch (err) {
      console.error('Failed to fetch captures:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1a2e] border border-white/20 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-white/10 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-white">{session.name}</h2>
            <p className="text-gray-400 text-sm mt-1">Session ID: {session.id}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-gray-400">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto flex-1">
          {/* Session Info */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <div className="text-gray-400 text-sm">Total Count</div>
              <div className="text-2xl font-bold text-white">{session.total_count}</div>
            </div>
            <div>
              <div className="text-gray-400 text-sm">Max Count</div>
              <div className="text-2xl font-bold text-white">{session.max_count}</div>
            </div>
            <div>
              <div className="text-gray-400 text-sm">Status</div>
              <div className={`text-lg font-semibold ${
                session.status === 'completed' ? 'text-green-400' : 'text-yellow-400'
              }`}>
                {session.status}
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-sm">Captures</div>
              <div className="text-2xl font-bold text-white">{captures.length}</div>
            </div>
          </div>

          {/* Captures Gallery */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Captured Images</h3>
            {loading ? (
              <div className="text-center text-gray-400 py-8">Loading captures...</div>
            ) : captures.length === 0 ? (
              <div className="text-center text-gray-400 py-8">No captures found</div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {captures.map((filename, index) => (
                  <div key={index} className="aspect-square bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-primary transition-colors">
                    <img
                      src={`/api/sessions/${session.id}/captures/${filename}`}
                      alt={`Capture ${index + 1}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23333" width="100" height="100"/%3E%3Ctext x="50%25" y="50%25" fill="%23666" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
                      }}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-white/10 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-white transition-colors"
          >
            Close
          </button>
          <button
            className="px-4 py-2 bg-primary hover:bg-secondary rounded-lg text-white transition-colors"
            onClick={() => alert('Export feature coming soon!')}
          >
            Export Data
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sessions;
