// import React from 'react';
// import './Chatbot.css';

// const ChatMessage = ({ message }) => {
//   const { role, text, isStreaming, isError, isSuccess } = message;
  
//   // Ensure text is a string
//   const displayText = typeof text === 'string' ? text : (text ? JSON.stringify(text) : '');
  
//   // Don't show empty streaming messages
//   if (isStreaming && !displayText) {
//     return (
//       <div className={`message ${role}`}>
//         <div className="message-avatar">
//           {role === 'user' ? '👤' : 'SW'}
//         </div>
//         <div className="typing-indicator">
//           <span></span>
//           <span></span>
//           <span></span>
//         </div>
//       </div>
//     );
//   }
  
//   // Don't render if text is empty and not streaming
//   if (!displayText && !isStreaming) {
//     return null;
//   }
  
//   return (
//     <div className={`message ${role} ${isError ? 'error' : ''} ${isSuccess ? 'success' : ''}`}>
//       <div className="message-avatar">
//         {role === 'user' ? '👤' : 'SW'}
//       </div>
//       <div className="message-content">
//         {displayText}
//       </div>
//     </div>
//   );
// };

// export default ChatMessage;


import React from 'react';
import './Chatbot.css';

const ChatMessage = ({ message }) => {
  const { role, text, isStreaming, isError, isSuccess } = message;
  
  // Function to convert URLs to clickable links
  const convertUrlsToLinks = (text) => {
    if (!text) return text;
    
    // Regular expression to match URLs
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    
    // Split text by URLs
    const parts = text.split(urlRegex);
    
    return parts.map((part, index) => {
      // Check if this part is a URL
      if (part && (part.startsWith('http://') || part.startsWith('https://'))) {
        return (
          <a 
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="message-link"
            onClick={(e) => e.stopPropagation()}
          >
            {part}
          </a>
        );
      }
      return part;
    });
  };
  
  // Function to convert email addresses to mailto links
  const convertEmailsToLinks = (text) => {
    if (!text) return text;
    
    const emailRegex = /([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/g;
    const parts = text.split(emailRegex);
    
    return parts.map((part, index) => {
      if (part && part.includes('@') && part.includes('.')) {
        return (
          <a 
            key={index}
            href={`mailto:${part}`}
            className="message-link"
          >
            {part}
          </a>
        );
      }
      return part;
    });
  };
  
  // Function to format text with links
  const formatTextWithLinks = (text) => {
    if (!text) return text;
    
    // First convert emails, then URLs
    const withEmails = convertEmailsToLinks(text);
    
    // If it's an array (has links), process each part
    if (Array.isArray(withEmails)) {
      return withEmails.map((part, idx) => {
        if (typeof part === 'string') {
          return convertUrlsToLinks(part);
        }
        return part;
      });
    }
    
    // If no emails, just convert URLs
    return convertUrlsToLinks(text);
  };
  
  // Get user initial from localStorage
  const getUserInitial = () => {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        return user?.username?.charAt(0).toUpperCase() || 'U';
      }
    } catch (e) {
      console.error('Failed to get user:', e);
    }
    return 'U';
  };
  
  // Ensure text is a string
  const displayText = typeof text === 'string' ? text : (text ? JSON.stringify(text) : '');
  const formattedContent = formatTextWithLinks(displayText);
  
  // Don't show empty streaming messages
  if (isStreaming && !displayText) {
    return (
      <div className={`message ${role}`}>
        <div className="message-avatar">
          {role === 'user' ? getUserInitial() : 'AI'}
        </div>
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    );
  }
  
  // Don't render if text is empty and not streaming
  if (!displayText && !isStreaming) {
    return null;
  }
  
  return (
    <div className={`message ${role} ${isError ? 'error' : ''} ${isSuccess ? 'success' : ''}`}>
      <div className="message-avatar">
        {role === 'user' ? getUserInitial() : 'AI'}
      </div>
      <div className="message-content">
        {formattedContent}
      </div>
    </div>
  );
};

export default ChatMessage;