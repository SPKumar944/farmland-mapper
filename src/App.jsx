import React, { useState } from 'react';
import MapComponent from './MapComponent';
import logo from './assets/logo.jpeg';

function App() {
  const [name, setName] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    if (name.trim().length > 0) {
      setIsLoggedIn(true);
    } else {
      alert("Please enter your name.");
    }
  };

  if (!isLoggedIn) {
    return (
      <div style={{ 
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        height: '100%', width: '100%', backgroundColor: '#f2f2f7'
      }}>
        <div style={{
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
          padding: '40px 30px', borderRadius: '24px', boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
          width: '90%', maxWidth: '360px', textAlign: 'center',
          border: '1px solid rgba(255,255,255,0.4)'
        }}>
          <img 
            src={logo} 
            alt="Farm Mapper Logo" 
            style={{ 
              width: '100%', maxWidth: '200px', height: 'auto', borderRadius: '12px', 
              marginBottom: '16px', objectFit: 'contain'
            }} 
          />
          <h1 style={{ fontSize: '24px', fontWeight: '600', color: '#1d1d1f', marginBottom: '8px' }}>
            Farm Mapper<br/><span style={{fontSize: '16px', fontWeight: '500'}}>பண்ணை எல்லை குறிப்பான்</span>
          </h1>
          <p style={{ color: '#86868b', marginBottom: '32px', fontSize: '15px' }}>
            Enter your name to begin.<br/>தொடங்க உங்கள் பெயரை உள்ளிடவும்.
          </p>
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <input 
              type="text" 
              placeholder="Your Name / உங்கள் பெயர்" 
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ 
                padding: '16px', fontSize: '17px', borderRadius: '12px', 
                border: '1px solid #d2d2d7', outline: 'none', width: '100%',
                boxSizing: 'border-box', textAlign: 'center',
                backgroundColor: '#ffffff', color: '#1d1d1f'
              }}
              required
            />
            <button type="submit" style={{ 
              padding: '14px', fontSize: '17px', backgroundColor: '#007AFF', 
              color: 'white', border: 'none', borderRadius: '12px', 
              cursor: 'pointer', fontWeight: '600', width: '100%'
            }}>
              Continue<br/><span style={{fontSize: '14px', fontWeight: '400'}}>தொடரவும்</span>
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <MapComponent userName={name} />
    </div>
  );
}

export default App;
