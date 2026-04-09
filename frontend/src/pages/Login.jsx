// import React, { useState } from 'react';
// import { Link, useNavigate } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext';
// import './Auth.css';

// const Login = () => {
//   const [username, setUsername] = useState('');
//   const [password, setPassword] = useState('');
//   const [loading, setLoading] = useState(false);
//   const { login } = useAuth();
//   const navigate = useNavigate();

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     if (!username.trim() || !password) {
//       return;
//     }
    
//     setLoading(true);
//     const result = await login(username, password);
//     setLoading(false);
    
//     if (result.success) {
//       navigate('/');
//     }
//   };

//   return (
//     <div className="auth-container">
//       <div className="auth-card">
//         <div className="auth-header">
//           <div className="auth-logo">
//             <span className="logo-icon">🤖</span>
//             <h1>Swaran Soft AI</h1>
//           </div>
//           <p className="auth-subtitle">Intelligent Assistant</p>
//         </div>

//         <form onSubmit={handleSubmit} className="auth-form">
//           <div className="form-group">
//             <label htmlFor="username">Username</label>
//             <input
//               id="username"
//               type="text"
//               value={username}
//               onChange={(e) => setUsername(e.target.value)}
//               placeholder="Enter your username"
//               required
//               disabled={loading}
//             />
//           </div>

//           <div className="form-group">
//             <label htmlFor="password">Password</label>
//             <input
//               id="password"
//               type="password"
//               value={password}
//               onChange={(e) => setPassword(e.target.value)}
//               placeholder="Enter your password"
//               required
//               disabled={loading}
//             />
//           </div>

//           <button type="submit" className="auth-btn" disabled={loading}>
//             {loading ? 'Logging in...' : 'Login'}
//           </button>
//         </form>

//         <div className="auth-footer">
//           <p>
//             Don't have an account?{' '}
//             <Link to="/register" className="auth-link">
//               Register
//             </Link>
//           </p>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default Login;



// import React, { useState } from 'react';
// import { Link, useNavigate } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext';
// import './Auth.css';

// const Login = () => {
//   const [username, setUsername] = useState('');
//   const [password, setPassword] = useState('');
//   const [loading, setLoading] = useState(false);
//   const { login } = useAuth();
//   const navigate = useNavigate();

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     if (!username.trim() || !password) {
//       return;
//     }
    
//     setLoading(true);
//     const result = await login(username, password);
//     setLoading(false);
    
//     if (result.success) {
//       // Check if there's a pending role from registration
//       const pendingRole = localStorage.getItem('pendingUserRole');
//       if (pendingRole) {
//         // Update the user object with the role
//         const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
//         currentUser.role = pendingRole;
//         localStorage.setItem('user', JSON.stringify(currentUser));
//         localStorage.removeItem('pendingUserRole');
//       }
//       navigate('/');
//     }
//   };

//   return (
//     <div className="auth-container">
//       <div className="auth-card">
//         <div className="auth-header">
//           <div className="auth-logo">
//             <span className="logo-icon">🤖</span>
//             <h1>Swaran Soft AI</h1>
//           </div>
//           <p className="auth-subtitle">Intelligent Assistant</p>
//         </div>

//         <form onSubmit={handleSubmit} className="auth-form">
//           <div className="form-group">
//             <label htmlFor="username">Username</label>
//             <input
//               id="username"
//               type="text"
//               value={username}
//               onChange={(e) => setUsername(e.target.value)}
//               placeholder="Enter your username"
//               required
//               disabled={loading}
//             />
//           </div>

//           <div className="form-group">
//             <label htmlFor="password">Password</label>
//             <input
//               id="password"
//               type="password"
//               value={password}
//               onChange={(e) => setPassword(e.target.value)}
//               placeholder="Enter your password"
//               required
//               disabled={loading}
//             />
//           </div>

//           <button type="submit" className="auth-btn" disabled={loading}>
//             {loading ? 'Logging in...' : 'Login'}
//           </button>
//         </form>

//         <div className="auth-footer">
//           <p>
//             Don't have an account?{' '}
//             <Link to="/register" className="auth-link">
//               Register
//             </Link>
//           </p>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default Login;


// import React, { useState } from 'react';
// import { Link, useNavigate } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext';
// import toast from 'react-hot-toast';
// import './Auth.css';

// const Login = () => {
//   const [username, setUsername] = useState('');
//   const [password, setPassword] = useState('');
//   const [loading, setLoading] = useState(false);
//   const { login } = useAuth();
//   const navigate = useNavigate();

//   const handleSubmit = async (e) => {
//     e.preventDefault();
    
//     if (!username.trim()) {
//       toast.error('Please enter your username');
//       return;
//     }
    
//     if (!password) {
//       toast.error('Please enter your password');
//       return;
//     }
    
//     setLoading(true);
//     console.log('Submitting login for:', username);
    
//     const result = await login(username, password);
    
//     setLoading(false);
    
//     if (result.success) {
//       console.log('Login successful, redirecting to dashboard');
//       navigate('/');
//     } else {
//       console.log('Login failed:', result.error);
//     }
//   };

//   return (
//     <div className="auth-container">
//       <div className="auth-card">
//         <div className="auth-header">
//           <div className="auth-logo">
//             <span className="logo-icon">🤖</span>
//             <h1>Swaran Soft AI</h1>
//           </div>
//           <p className="auth-subtitle">Intelligent Assistant</p>
//         </div>

//         <form onSubmit={handleSubmit} className="auth-form">
//           <div className="form-group">
//             <label htmlFor="username">Username</label>
//             <input
//               id="username"
//               type="text"
//               value={username}
//               onChange={(e) => setUsername(e.target.value)}
//               placeholder="Enter your username"
//               required
//               disabled={loading}
//               autoComplete="username"
//             />
//           </div>

//           <div className="form-group">
//             <label htmlFor="password">Password</label>
//             <input
//               id="password"
//               type="password"
//               value={password}
//               onChange={(e) => setPassword(e.target.value)}
//               placeholder="Enter your password"
//               required
//               disabled={loading}
//               autoComplete="current-password"
//             />
//           </div>

//           <button type="submit" className="auth-btn" disabled={loading}>
//             {loading ? 'Logging in...' : 'Login'}
//           </button>
//         </form>

//         <div className="auth-footer">
//           <p>
//             Don't have an account?{' '}
//             <Link to="/register" className="auth-link">
//               Register
//             </Link>
//           </p>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default Login;

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import './Auth.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!username.trim()) {
      toast.error('Please enter your username');
      return;
    }
    
    if (!password) {
      toast.error('Please enter your password');
      return;
    }
    
    setLoading(true);
    console.log('Submitting login for:', username);
    
    const result = await login(username, password);
    
    setLoading(false);
    
    if (result.success) {
      console.log('Login successful, redirecting to dashboard');
      navigate('/');
    } else {
      console.log('Login failed:', result.error);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <span className="logo-icon"></span>
            <h1>Swaran Soft AI Assistant</h1>
          </div>
          <p className="auth-subtitle">Please login to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/register" className="auth-link">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;