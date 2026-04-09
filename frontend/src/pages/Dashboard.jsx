// import React, { useState } from 'react';
// import { useAuth } from '../contexts/AuthContext';
// import Layout from '../components/Layout/Layout';
// import Chatbot from '../components/Chatbot/Chatbot';
// import UploadPDF from '../components/Upload/UploadPDF';
// import './Dashboard.css';

// const Dashboard = () => {
//   const { isAdmin } = useAuth();
//   const [activeTab, setActiveTab] = useState('chat');

//   return (
//     <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
//       {activeTab === 'chat' && <Chatbot />}
//       {activeTab === 'upload' && isAdmin && <UploadPDF />}
//     </Layout>
//   );
// };

// export default Dashboard;


import React, { useState, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout/Layout';
import Chatbot from '../components/Chatbot/Chatbot';
import UploadPDF from '../components/Upload/UploadPDF';

const Dashboard = () => {
  const { isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const [chatSession, setChatSession] = useState(null);

  const handleSessionChange = useCallback((session) => {
    setChatSession(session);
    // Force Chatbot to re-render with new session
    window.dispatchEvent(new CustomEvent('sessionChange', { detail: session }));
  }, []);

  return (
    <Layout 
      activeTab={activeTab} 
      setActiveTab={setActiveTab}
      onSessionChange={handleSessionChange}
    >
      {activeTab === 'chat' && <Chatbot key={chatSession?.id || 'new'} />}
      {activeTab === 'upload' && isAdmin && <UploadPDF />}
    </Layout>
  );
};

export default Dashboard;