import React, { useState } from 'react';
import MapComponent from './MapComponent';

function App() {
  const [phone, setPhone] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    if (phone.length >= 10) {
      setIsLoggedIn(true);
    } else {
      alert("Please enter a valid phone number.");
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="login-container" style={{ padding: '40px 20px' }}>
        <h1 className="login-title" style={{ fontSize: '28px', marginBottom: '10px' }}>Farm Mapper</h1>
        <p style={{ color: '#666', marginBottom: '30px', fontSize: '16px' }}>Enter your phone number to begin.</p>
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%', maxWidth: '350px' }}>
          <input 
            type="tel" 
            placeholder="e.g. +91 9876543210" 
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            style={{ 
              padding: '16px', fontSize: '18px', borderRadius: '12px', 
              border: '2px solid #ddd', outline: 'none', width: '100%',
              boxSizing: 'border-box', textAlign: 'center'
            }}
            required
          />
          <button type="submit" style={{ 
            padding: '16px', fontSize: '18px', backgroundColor: '#4CAF50', 
            color: 'white', border: 'none', borderRadius: '12px', 
            cursor: 'pointer', fontWeight: 'bold', width: '100%',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
          }}>
            Continue
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="app-container">
      <MapComponent userPhone={phone} />
    </div>
  );
}

export default App;
