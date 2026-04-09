import React from 'react';
import './Navbar.css';

const Navbar = ({ onMenuClick }) => {
  const handleMenuClick = () => {
    if (onMenuClick) {
      onMenuClick();
    }
  };

  return (
    <header className="navbar">
      <button className="menu-btn" onClick={handleMenuClick}>
        ☰
      </button>
      
      <div className="navbar-right">
        {/* Removed the navbar title */}
      </div>
    </header>
  );
};

export default Navbar;