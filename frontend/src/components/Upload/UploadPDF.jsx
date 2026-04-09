// import React, { useState } from 'react';
// import { useAuth } from '../../contexts/AuthContext';
// import { getSessionId } from '../../utils/constants';
// import toast from 'react-hot-toast';
// import './UploadPDF.css';

// const UploadPDF = () => {
//   const [selectedFile, setSelectedFile] = useState(null);
//   const [uploading, setUploading] = useState(false);
//   const [status, setStatus] = useState({ type: '', message: '' });
//   const [collectionType, setCollectionType] = useState('global');
//   const { token } = useAuth();
//   const sessionId = getSessionId();

//   const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

//   const handleFileSelect = (e) => {
//     const file = e.target.files[0];
//     if (file && file.type === 'application/pdf') {
//       setSelectedFile(file);
//       setStatus({ type: '', message: '' });
//     } else {
//       setSelectedFile(null);
//       setStatus({ type: 'error', message: 'Please select a valid PDF file.' });
//       toast.error('Please select a valid PDF file.');
//     }
//   };

//   const handleDragOver = (e) => {
//     e.preventDefault();
//     e.stopPropagation();
//   };

//   const handleDrop = (e) => {
//     e.preventDefault();
//     e.stopPropagation();
//     const file = e.dataTransfer.files[0];
//     if (file && file.type === 'application/pdf') {
//       setSelectedFile(file);
//       setStatus({ type: '', message: '' });
//     } else {
//       setStatus({ type: 'error', message: 'Please drop a valid PDF file.' });
//       toast.error('Please drop a valid PDF file.');
//     }
//   };

//   const handleUpload = async () => {
//     if (!selectedFile) {
//       setStatus({ type: 'error', message: 'Please select a file first.' });
//       toast.error('Please select a file first.');
//       return;
//     }

//     if (!token) {
//       setStatus({ type: 'error', message: 'Authentication required. Please login again.' });
//       toast.error('Authentication required. Please login again.');
//       return;
//     }

//     setUploading(true);
//     setStatus({ type: 'loading', message: 'Uploading and processing PDF...' });

//     const targetCollection = collectionType === 'global' 
//       ? 'swaransoft_website' 
//       : sessionId;

//     const formData = new FormData();
//     formData.append('file', selectedFile);
//     formData.append('session_id', targetCollection);

//     try {
//       console.log('Uploading to:', `${API_BASE_URL}/upload/pdf`);
//       console.log('File:', selectedFile.name);
//       console.log('Collection:', targetCollection);
      
//       const response = await fetch(`${API_BASE_URL}/upload/pdf`, {
//         method: 'POST',
//         headers: {
//           'Authorization': `Bearer ${token}`,
//         },
//         body: formData,
//       });

//       console.log('Response status:', response.status);
      
//       const data = await response.json();
//       console.log('Response data:', data);

//       if (response.ok) {
//         setStatus({ 
//           type: 'success', 
//           message: `${data.message || 'Upload successful!'} (${data.chunks_stored || 0} chunks stored in "${data.collection || targetCollection}")` 
//         });
//         toast.success('PDF uploaded successfully!');
//         setSelectedFile(null);
//         // Reset file input
//         const fileInput = document.getElementById('fileInput');
//         if (fileInput) fileInput.value = '';
//       } else if (response.status === 401 || response.status === 403) {
//         setStatus({ type: 'error', message: data.detail || 'Access denied. Please login again.' });
//         toast.error('Access denied. Please login again.');
//       } else {
//         setStatus({ type: 'error', message: data.detail || 'Upload failed. Please try again.' });
//         toast.error(data.detail || 'Upload failed. Please try again.');
//       }
//     } catch (error) {
//       console.error('Upload error:', error);
//       setStatus({ type: 'error', message: 'Could not reach the server. Please check if the backend is running on port 8000.' });
//       toast.error('Could not reach the server. Please check if the backend is running.');
//     } finally {
//       setUploading(false);
//     }
//   };

//   const formatFileSize = (bytes) => {
//     if (bytes < 1024) return bytes + ' B';
//     if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
//     return (bytes / 1024 / 1024).toFixed(1) + ' MB';
//   };

//   return (
//     <div className="upload-container">
//       <div className="upload-card">
//         <div className="upload-header">
//           <h1>Upload a PDF</h1>
//           <p>Chunk, embed and store a document into the knowledge base.</p>
//         </div>

//         <div className="upload-body">
//           <div className="collection-toggle">
//             <label className="toggle-label">Target Collection</label>
//             <div className="toggle-buttons">
//               <button
//                 type="button"
//                 className={`toggle-btn ${collectionType === 'global' ? 'active' : ''}`}
//                 onClick={() => setCollectionType('global')}
//                 disabled={uploading}
//               >
//                 Global KB (all users)
//               </button>
//               <button
//                 type="button"
//                 className={`toggle-btn ${collectionType === 'session' ? 'active' : ''}`}
//                 onClick={() => setCollectionType('session')}
//                 disabled={uploading}
//               >
//                 Session (current user only)
//               </button>
//             </div>
//           </div>

//           <div
//             className={`drop-zone ${selectedFile ? 'has-file' : ''}`}
//             onDragOver={handleDragOver}
//             onDrop={handleDrop}
//           >
//             <input
//               id="fileInput"
//               type="file"
//               accept=".pdf"
//               onChange={handleFileSelect}
//               disabled={uploading}
//             />
//             <div className="drop-icon">📄</div>
//             <h3>Drop your PDF here</h3>
//             <p>or <span>browse to choose a file</span></p>
//             <p className="file-limit">PDF files up to 50 MB</p>
//           </div>

//           {selectedFile && (
//             <div className="file-preview">
//               <div className="file-icon">📄</div>
//               <div className="file-info">
//                 <div className="file-name">{selectedFile.name}</div>
//                 <div className="file-size">{formatFileSize(selectedFile.size)}</div>
//               </div>
//               <button
//                 type="button"
//                 className="file-remove"
//                 onClick={() => {
//                   setSelectedFile(null);
//                   const fileInput = document.getElementById('fileInput');
//                   if (fileInput) fileInput.value = '';
//                   setStatus({ type: '', message: '' });
//                 }}
//                 disabled={uploading}
//               >
//                 ✕
//               </button>
//             </div>
//           )}

//           <button
//             type="button"
//             className="upload-btn"
//             onClick={handleUpload}
//             disabled={!selectedFile || uploading}
//           >
//             {uploading ? 'Uploading...' : 'Upload Document'}
//           </button>

//           {status.message && (
//             <div className={`status-area ${status.type}`}>
//               {status.type === 'loading' && <div className="spinner"></div>}
//               {status.type === 'success' && <span>✓</span>}
//               {status.type === 'error' && <span>⚠</span>}
//               <span>{status.message}</span>
//             </div>
//           )}

//           <div className="tips">
//             <h4>Admin Tips</h4>
//             <ul>
//               <li><strong>Global KB</strong> — document is searchable by ALL users immediately.</li>
//               <li><strong>Session</strong> — document is only visible to the current browser session.</li>
//               <li>PDFs with selectable text work best. Scanned images may lose accuracy.</li>
//               <li>Large PDFs are split into 500-token chunks automatically.</li>
//             </ul>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default UploadPDF;

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { getSessionId } from '../../utils/constants';
import toast from 'react-hot-toast';
import './UploadPDF.css';

const UploadPDF = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState({ type: '', message: '' });
  const [collectionType, setCollectionType] = useState('global');
  const { token, user, logout } = useAuth();
  const sessionId = getSessionId();

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

  // The session_id sent in chat must match the one used during PDF upload.
  // We ALWAYS use the stable localStorage session key for per-session uploads.
  const effectiveSessionId = collectionType === 'global' ? 'swaransoft_website' : sessionId;

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setStatus({ type: '', message: '' });
    } else {
      setSelectedFile(null);
      setStatus({ type: 'error', message: 'Please select a valid PDF file.' });
      toast.error('Please select a valid PDF file.');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setStatus({ type: '', message: '' });
    } else {
      setStatus({ type: 'error', message: 'Please drop a valid PDF file.' });
      toast.error('Please drop a valid PDF file.');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setStatus({ type: 'error', message: 'Please select a file first.' });
      toast.error('Please select a file first.');
      return;
    }

    // Get fresh token from localStorage
    const freshToken = localStorage.getItem('accessToken');
    
    if (!freshToken) {
      setStatus({ type: 'error', message: 'Authentication required. Please login again.' });
      toast.error('Authentication required. Please login again.');
      setTimeout(() => logout(), 2000);
      return;
    }

    // Check if user is admin
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
    if (!currentUser.is_admin && currentUser.role !== 'admin') {
      setStatus({ type: 'error', message: 'Only admin users can upload PDFs.' });
      toast.error('Only admin users can upload PDFs.');
      return;
    }

    setUploading(true);
    setStatus({ type: 'loading', message: 'Uploading and processing PDF...' });

    const targetCollection = effectiveSessionId;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('session_id', targetCollection);
    console.log('[UPLOAD] session_id used:', targetCollection);

    try {
      console.log('Uploading to:', `${API_BASE_URL}/upload/pdf`);
      console.log('File:', selectedFile.name);
      console.log('Collection:', targetCollection);
      console.log('Token:', freshToken ? `${freshToken.substring(0, 20)}...` : 'Missing');
      
      const response = await fetch(`${API_BASE_URL}/upload/pdf`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${freshToken}`,
        },
        body: formData,
      });

      console.log('Response status:', response.status);
      
      // Handle 401 Unauthorized
      if (response.status === 401) {
        setStatus({ type: 'error', message: 'Session expired. Please login again.' });
        toast.error('Session expired. Please login again.');
        setTimeout(() => logout(), 2000);
        return;
      }
      
      const data = await response.json();
      console.log('Response data:', data);

      if (response.ok) {
        setStatus({ 
          type: 'success', 
          message: `${data.message || 'Upload successful!'} (${data.chunks_stored || 0} chunks stored)` 
        });
        toast.success('PDF uploaded successfully!');
        setSelectedFile(null);
        // Reset file input
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.value = '';
      } else if (response.status === 403) {
        setStatus({ type: 'error', message: 'Access denied. Admin privileges required.' });
        toast.error('Access denied. Admin privileges required.');
      } else {
        setStatus({ type: 'error', message: data.detail || 'Upload failed. Please try again.' });
        toast.error(data.detail || 'Upload failed. Please try again.');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setStatus({ 
        type: 'error', 
        message: `Could not reach the server. Error: ${error.message}` 
      });
      toast.error('Could not reach the server. Please check if backend is running.');
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <div className="upload-header">
          <h1>Upload a PDF</h1>
          <p>Chunk, embed and store a document into the knowledge base.</p>
        </div>

        <div className="upload-body">
          <div className="collection-toggle">
            <label className="toggle-label">Target Collection</label>
            <div className="toggle-buttons">
              <button
                type="button"
                className={`toggle-btn ${collectionType === 'global' ? 'active' : ''}`}
                onClick={() => setCollectionType('global')}
                disabled={uploading}
              >
                Global KB (all users)
              </button>
              <button
                type="button"
                className={`toggle-btn ${collectionType === 'session' ? 'active' : ''}`}
                onClick={() => setCollectionType('session')}
                disabled={uploading}
              >
                Session (current user only)
              </button>
            </div>
          </div>

          <div
            className={`drop-zone ${selectedFile ? 'has-file' : ''}`}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <input
              id="fileInput"
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              disabled={uploading}
            />
            <div className="drop-icon">📄</div>
            <h3>Drop your PDF here</h3>
            <p>or <span>browse to choose a file</span></p>
            <p className="file-limit">PDF files up to 50 MB</p>
          </div>

          {selectedFile && (
            <div className="file-preview">
              <div className="file-icon">📄</div>
              <div className="file-info">
                <div className="file-name">{selectedFile.name}</div>
                <div className="file-size">{formatFileSize(selectedFile.size)}</div>
              </div>
              <button
                type="button"
                className="file-remove"
                onClick={() => {
                  setSelectedFile(null);
                  const fileInput = document.getElementById('fileInput');
                  if (fileInput) fileInput.value = '';
                  setStatus({ type: '', message: '' });
                }}
                disabled={uploading}
              >
                ✕
              </button>
            </div>
          )}

          <button
            type="button"
            className="upload-btn"
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
          >
            {uploading ? 'Uploading...' : 'Upload Document'}
          </button>

          {status.message && (
            <div className={`status-area ${status.type}`}>
              {status.type === 'loading' && <div className="spinner"></div>}
              {status.type === 'success' && <span>✓</span>}
              {status.type === 'error' && <span>⚠</span>}
              <span>{status.message}</span>
            </div>
          )}

          <div className="tips">
            <h4>Admin Tips</h4>
            <ul>
              <li><strong>Global KB</strong> — document is searchable by ALL users immediately.</li>
              <li><strong>Session</strong> — document is only visible to the current browser session.</li>
              <li>PDFs with selectable text work best. Scanned images may lose accuracy.</li>
              <li>Large PDFs are split into 500-token chunks automatically.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPDF;