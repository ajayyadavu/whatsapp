


// import React, { createContext, useState, useContext, useEffect } from 'react';
// import { authAPI } from '../services/api';
// import toast from 'react-hot-toast';

// const AuthContext = createContext(null);

// export const useAuth = () => {
//   const context = useContext(AuthContext);
//   if (!context) {
//     throw new Error('useAuth must be used within AuthProvider');
//   }
//   return context;
// };

// export const AuthProvider = ({ children }) => {
//   const [user, setUser] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const [token, setToken] = useState(localStorage.getItem('accessToken'));

//   useEffect(() => {
//     const storedUser = localStorage.getItem('user');
//     const storedToken = localStorage.getItem('accessToken');
    
//     if (storedUser && storedToken) {
//       try {
//         const parsedUser = JSON.parse(storedUser);
//         setUser(parsedUser);
//         setToken(storedToken);
//       } catch (error) {
//         console.error('Failed to parse stored user:', error);
//         localStorage.removeItem('user');
//         localStorage.removeItem('accessToken');
//       }
//     }
//     setLoading(false);
//   }, []);

//   const login = async (username, password) => {
//     try {
//       console.log('Attempting login for:', username);
//       const response = await authAPI.login(username, password);
//       console.log('Login response:', response);
      
//       const { access_token, user: userData } = response;
      
//       // Ensure userData has is_admin field
//       const userWithRole = {
//         ...userData,
//         role: userData.is_admin ? 'admin' : 'user',
//         is_admin: userData.is_admin || false
//       };
      
//       localStorage.setItem('accessToken', access_token);
//       localStorage.setItem('user', JSON.stringify(userWithRole));
      
//       setUser(userWithRole);
//       setToken(access_token);
      
//       toast.success('Login successful!');
//       return { success: true, user: userWithRole };
//     } catch (error) {
//       console.error('Login error:', error);
//       const message = error.response?.data?.detail || 'Login failed. Please check your credentials.';
//       toast.error(message);
//       return { success: false, error: message };
//     }
//   };

//   const register = async (username, email, password, role = 'user') => {
//     try {
//       console.log('Attempting registration for:', username, 'with role:', role);
      
//       const response = await authAPI.register(username, email, password);
//       console.log('Registration response:', response);
      
//       toast.success('Registration successful! Please login.');
//       return { success: true };
//     } catch (error) {
//       console.error('Registration error:', error);
//       const message = error.response?.data?.detail || 'Registration failed. Please try again.';
//       toast.error(message);
//       return { success: false, error: message };
//     }
//   };

//   const logout = () => {
//     localStorage.removeItem('accessToken');
//     localStorage.removeItem('user');
//     setUser(null);
//     setToken(null);
//     toast.success('Logged out successfully');
//     window.location.href = '/login';
//   };

//   // Function to get fresh token
//   const getToken = () => {
//     return localStorage.getItem('accessToken');
//   };

//   const isAdmin = user?.is_admin === true || user?.role === 'admin';

//   const value = {
//     user,
//     token,
//     loading,
//     isAuthenticated: !!user && !!token,
//     isAdmin,
//     login,
//     register,
//     logout,
//     getToken,
//   };

//   return (
//     <AuthContext.Provider value={value}>
//       {children}
//     </AuthContext.Provider>
//   );
// };


import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('accessToken'));

  // Validate token on app load
  useEffect(() => {
    const validateToken = async () => {
      const storedToken = localStorage.getItem('accessToken');
      const storedUser = localStorage.getItem('user');
      
      if (!storedToken || !storedUser) {
        setLoading(false);
        return;
      }

      try {
        // Try to get current user to validate token
        const response = await authAPI.getCurrentUser();
        if (response) {
          setUser(JSON.parse(storedUser));
          setToken(storedToken);
        }
      } catch (error) {
        console.error('Token validation failed:', error);
        // Token is invalid, clear storage
        localStorage.removeItem('accessToken');
        localStorage.removeItem('user');
        localStorage.removeItem('userRole');
        setUser(null);
        setToken(null);
      } finally {
        setLoading(false);
      }
    };

    validateToken();
  }, []);

  const login = async (username, password) => {
    try {
      console.log('Attempting login for:', username);
      const response = await authAPI.login(username, password);
      console.log('Login response:', response);
      
      const { access_token, user: userData } = response;
      
      // Ensure userData has is_admin field
      const userWithRole = {
        ...userData,
        role: userData.is_admin ? 'admin' : 'user',
        is_admin: userData.is_admin || false
      };
      
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('user', JSON.stringify(userWithRole));
      localStorage.setItem('loginTime', Date.now().toString());
      
      setUser(userWithRole);
      setToken(access_token);
      
      toast.success('Login successful!');
      return { success: true, user: userWithRole };
    } catch (error) {
      console.error('Login error:', error);
      const message = error.response?.data?.detail || 'Login failed. Please check your credentials.';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const register = async (username, email, password, role = 'user') => {
    try {
      console.log('Attempting registration for:', username, 'with role:', role);
      
      // Store the role in localStorage
      localStorage.setItem('userRole', role);
      
      const response = await authAPI.register(username, email, password);
      console.log('Registration response:', response);
      
      toast.success('Registration successful! Please login.');
      return { success: true };
    } catch (error) {
      console.error('Registration error:', error);
      const message = error.response?.data?.detail || 'Registration failed. Please try again.';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');
    localStorage.removeItem('userRole');
    localStorage.removeItem('loginTime');
    localStorage.removeItem('swaran_session_id');
    localStorage.removeItem('chat_history');
    localStorage.removeItem('active_chat_session');
    setUser(null);
    setToken(null);
    toast.success('Logged out successfully');
    window.location.href = '/login';
  };

  // Check if session is expired (optional: add time-based expiry)
  const isSessionExpired = () => {
    const loginTime = localStorage.getItem('loginTime');
    if (!loginTime) return true;
    
    // Session expires after 24 hours (optional)
    const expiryTime = 24 * 60 * 60 * 1000; // 24 hours
    const now = Date.now();
    return (now - parseInt(loginTime)) > expiryTime;
  };

  const isAdmin = user?.is_admin === true || user?.role === 'admin';

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!user && !!token && !isSessionExpired(),
    isAdmin,
    login,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};