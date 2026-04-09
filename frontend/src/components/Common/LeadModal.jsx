// import React, { useState } from 'react';
// import './LeadModal.css';

// const LeadModal = ({ isOpen, onClose, onSubmit }) => {
//   const [formData, setFormData] = useState({
//     name: '',
//     email: '',
//     company: '',
//     role: '',
//     industry: '',
//     phone: '',
//   });
//   const [submitting, setSubmitting] = useState(false);

//   const handleChange = (e) => {
//     setFormData({
//       ...formData,
//       [e.target.name]: e.target.value,
//     });
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();
    
//     if (!formData.name || !formData.email || !formData.company || !formData.industry) {
//       return;
//     }
    
//     setSubmitting(true);
//     const success = await onSubmit(formData);
//     setSubmitting(false);
    
//     if (success) {
//       onClose();
//       setFormData({
//         name: '',
//         email: '',
//         company: '',
//         role: '',
//         industry: '',
//         phone: '',
//       });
//     }
//   };

//   if (!isOpen) return null;

//   return (
//     <div className="modal-overlay" onClick={onClose}>
//       <div className="modal" onClick={(e) => e.stopPropagation()}>
//         <div className="modal-header">
//           <div>
//             <h3>Book a Discovery Call</h3>
//             <p>Our team will reach out within 24 hours to schedule a live pilot.</p>
//           </div>
//           <button className="modal-close" onClick={onClose}>✕</button>
//         </div>
        
//         <form onSubmit={handleSubmit} className="modal-body">
//           <div className="form-row">
//             <div className="form-group">
//               <label>Full Name <span className="required">*</span></label>
//               <input
//                 name="name"
//                 value={formData.name}
//                 onChange={handleChange}
//                 placeholder="John Smith"
//                 required
//               />
//             </div>
//             <div className="form-group">
//               <label>Work Email <span className="required">*</span></label>
//               <input
//                 name="email"
//                 type="email"
//                 value={formData.email}
//                 onChange={handleChange}
//                 placeholder="john@company.com"
//                 required
//               />
//             </div>
//           </div>
          
//           <div className="form-row">
//             <div className="form-group">
//               <label>Company <span className="required">*</span></label>
//               <input
//                 name="company"
//                 value={formData.company}
//                 onChange={handleChange}
//                 placeholder="Acme Corp"
//                 required
//               />
//             </div>
//             <div className="form-group">
//               <label>Job Role</label>
//               <input
//                 name="role"
//                 value={formData.role}
//                 onChange={handleChange}
//                 placeholder="CTO, Head of AI…"
//               />
//             </div>
//           </div>
          
//           <div className="form-group">
//             <label>Industry <span className="required">*</span></label>
//             <select
//               name="industry"
//               value={formData.industry}
//               onChange={handleChange}
//               required
//             >
//               <option value="">Select your industry</option>
//               <option>Healthcare</option>
//               <option>Banking & Finance (BFSI)</option>
//               <option>Telecom</option>
//               <option>Retail</option>
//               <option>Manufacturing</option>
//               <option>Real Estate</option>
//               <option>Education</option>
//               <option>Logistics</option>
//               <option>Government</option>
//               <option>Other</option>
//             </select>
//           </div>
          
//           <div className="form-group">
//             <label>Phone / WhatsApp</label>
//             <input
//               name="phone"
//               value={formData.phone}
//               onChange={handleChange}
//               placeholder="+91 98765 43210"
//               type="tel"
//             />
//           </div>
          
//           <div className="modal-footer">
//             <button type="submit" className="btn-submit" disabled={submitting}>
//               {submitting ? 'Submitting...' : 'Submit Request'}
//             </button>
//             <button type="button" className="btn-cancel" onClick={onClose}>
//               Cancel
//             </button>
//           </div>
//         </form>
//       </div>
//     </div>
//   );
// };

// export default LeadModal;


import React, { useState } from 'react';
import './LeadModal.css';

const LeadModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    role: '',
    industry: '',
    phone: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleClose = () => {
    if (onClose) {
      onClose();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.email || !formData.company || !formData.industry) {
      return;
    }
    
    setSubmitting(true);
    if (onSubmit) {
      const success = await onSubmit(formData);
      if (success) {
        handleClose();
        setFormData({
          name: '',
          email: '',
          company: '',
          role: '',
          industry: '',
          phone: '',
        });
      }
    }
    setSubmitting(false);
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal">
        <div className="modal-header">
          <div>
            <h3>Book a Discovery Call</h3>
            <p>Our team will reach out within 24 hours to schedule a live pilot.</p>
          </div>
          <button className="modal-close" onClick={handleClose}>✕</button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-row">
            <div className="form-group">
              <label>Full Name <span className="required">*</span></label>
              <input
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="John Smith"
                required
              />
            </div>
            <div className="form-group">
              <label>Work Email <span className="required">*</span></label>
              <input
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="john@company.com"
                required
              />
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label>Company <span className="required">*</span></label>
              <input
                name="company"
                value={formData.company}
                onChange={handleChange}
                placeholder="Acme Corp"
                required
              />
            </div>
            <div className="form-group">
              <label>Job Role</label>
              <input
                name="role"
                value={formData.role}
                onChange={handleChange}
                placeholder="CTO, Head of AI…"
              />
            </div>
          </div>
          
          <div className="form-group">
            <label>Industry <span className="required">*</span></label>
            <select
              name="industry"
              value={formData.industry}
              onChange={handleChange}
              required
            >
              <option value="">Select your industry</option>
              <option>Healthcare</option>
              <option>Banking & Finance (BFSI)</option>
              <option>Telecom</option>
              <option>Retail</option>
              <option>Manufacturing</option>
              <option>Real Estate</option>
              <option>Education</option>
              <option>Logistics</option>
              <option>Government</option>
              <option>Other</option>
            </select>
          </div>
          
          <div className="form-group">
            <label>Phone / WhatsApp</label>
            <input
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="+91 98765 43210"
              type="tel"
            />
          </div>
          
          <div className="modal-footer">
            <button type="submit" className="btn-submit" disabled={submitting}>
              {submitting ? 'Submitting...' : 'Submit Request'}
            </button>
            <button type="button" className="btn-cancel" onClick={handleClose}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LeadModal;