// // import React from 'react';
// // import { useAuth } from '../../contexts/AuthContext';
// // import Sidebar from './Sidebar';
// // import Navbar from './Navbar';
// // import './Layout.css';

// // const Layout = ({ children, activeTab, setActiveTab }) => {
// //   const { user, logout, isAdmin } = useAuth();
// //   const [sidebarOpen, setSidebarOpen] = React.useState(false);

// //   return (
// //     <div className="layout">
// //       <Sidebar 
// //         isOpen={sidebarOpen} 
// //         onClose={() => setSidebarOpen(false)}
// //         activeTab={activeTab}
// //         setActiveTab={setActiveTab}
// //         isAdmin={isAdmin}
// //       />
// //       <div className="layout-main">
// //         <Navbar 
// //           user={user} 
// //           onLogout={logout} 
// //           onMenuClick={() => setSidebarOpen(true)}
// //         />
// //         <main className="layout-content">
// //           {children}
// //         </main>
// //       </div>
// //     </div>
// //   );
// // };

// // export default Layout;



// import React from 'react';
// import './Sidebar.css';

// const Sidebar = ({ isOpen, onClose, activeTab, setActiveTab, isAdmin }) => {
//   const menuItems = [
//     { id: 'chat', label: 'Chat', icon: '💬', visible: true },
//     { id: 'upload', label: 'Upload PDF', icon: '📄', visible: isAdmin },
//   ];

//   return (
//     <>
//       {isOpen && <div className="sidebar-overlay" onClick={onClose} />}
//       <div className={`sidebar ${isOpen ? 'open' : ''}`}>
//         <div className="sidebar-header">
//           <div className="logo">
//             <span className="logo-icon">🤖</span>
//             <span className="logo-text">Swaran Soft AI</span>
//           </div>
//           {isAdmin && <span className="admin-badge">Admin</span>}
//         </div>

//         <nav className="sidebar-nav">
//           {menuItems.map(item => item.visible && (
//             <button
//               key={item.id}
//               className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
//               onClick={() => {
//                 setActiveTab(item.id);
//                 onClose();
//               }}
//             >
//               <span className="nav-icon">{item.icon}</span>
//               <span className="nav-label">{item.label}</span>
//             </button>
//           ))}
//         </nav>
//       </div>
//     </>
//   );
// };

// export default Sidebar;
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import './Layout.css';

const Layout = ({ children, activeTab, setActiveTab, onSessionChange }) => {
  const { user, logout, isAdmin } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  const handleMenuClick = () => {
    setSidebarOpen(true);
  };

  return (
    <div className="layout">
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={handleSidebarClose}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isAdmin={isAdmin}
        onSessionChange={onSessionChange}
      />
      <div className="layout-main">
        <Navbar 
          user={user} 
          onLogout={logout} 
          onMenuClick={handleMenuClick}
        />
        <main className="layout-content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;