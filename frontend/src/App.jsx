import React, { useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import LogsPage from './pages/LogsPage';
import ProtectedRoute from './components/Common/ProtectedRoute';
import './App.css';

// Component to handle initial auth check
const AuthChecker = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      const token = localStorage.getItem('accessToken');
      const user = localStorage.getItem('user');
      if (token || user) {
        localStorage.clear();
      }
      navigate('/login');
    }
  }, [loading, isAuthenticated, navigate]);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
      }}>
        Loading...
      </div>
    );
  }

  return children;
};

function App() {
  return (
    <AuthProvider>
      <Toaster position="top-right" toastOptions={{ duration: 3000 }} />
      <Routes>
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Dashboard */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AuthChecker>
                <Dashboard />
              </AuthChecker>
            </ProtectedRoute>
          }
        />

        {/* Chat Logs — admin only (LogsPage handles the redirect internally) */}
        <Route
          path="/logs"
          element={
            <ProtectedRoute>
              <AuthChecker>
                <LogsPage />
              </AuthChecker>
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
