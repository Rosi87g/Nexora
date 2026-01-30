import React from 'react';
import { useNavigate } from 'react-router-dom';
import './ManageAccount.css';

const ManageAccount = () => {
  const navigate = useNavigate();

  const handleUpgrade = () => {
    window.open('/subscription', '_blank');
  };

  const handleManageSubscription = () => {
    window.open('/subscription', '_blank');
  };

  return (
    <div className="manage-account-page">
      {/* HEADER */}
      <header className="manage-header">
        <div className="header-content">
          <button className="back-btn" onClick={() => navigate(-1)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Back</span>
          </button>
          <h1 className="page-title">Manage Account</h1>
          <div className="header-spacer"></div>
        </div>
      </header>

      <div className="manage-content">
        {/* LEFT SIDEBAR */}
        <div className="manage-sidebar">
          <div className="sidebar-item active">
            <svg className="sidebar-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            <span>Account</span>
          </div>
          <div className="sidebar-item">
            <svg className="sidebar-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
            <span>Security</span>
          </div>
          <div className="sidebar-item">
            <svg className="sidebar-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21 12V7H5v14H16v-5h4v-2h-4v-2h4v-2h-4V7h12v5h-4zm-6 6l-6-6 1.41-1.41L12 12.17l4.59-4.59L15 6l-6 6z"/>
            </svg>
            <span>Sessions</span>
          </div>
          <div className="sidebar-item">
            <svg className="sidebar-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M4 6h18V4H4c-1.1 0-2 .9-2 2v11H0v3h14v-3H4V6zm19 2h-6c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h6c.55 0 1-.45 1-1V9c0-.55-.45-1-1-1zm-1 9h-4v-7h4v7z"/>
            </svg>
            <span>Data</span>
          </div>
        </div>

        {/* MAIN CONTENT */}
        <div className="manage-main">
          {/* ACCOUNT INFO SECTION */}
          <div className="account-info-section">
            <div className="section-header">
              <h2 className="section-title">Your account</h2>
              <p className="section-subtitle">Manage your account information.</p>
            </div>

            {/* ACCOUNT DETAILS GRID */}
            <div className="account-details-grid">
              {/* SUBSCRIPTION */}
              <div className="account-detail-card full-width">
                <div className="detail-header">
                  <h3>Nexora subscription</h3>
                  <button 
                    className="detail-action-btn manage-subscription"
                    onClick={handleManageSubscription}
                  >
                    Manage →
                  </button>
                </div>
                <div className="detail-content">
                  <div className="subscription-display">
                    <div className="subscription-info">
                      <span className="subscription-status free">Free</span>
                      <span className="subscription-description">
                        Upgrade to unlock unlimited conversations and advanced features
                      </span>
                    </div>
                    <button className="upgrade-btn" onClick={handleUpgrade}>
                      <span>Upgrade to Pro</span>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M9 5l7 7-7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              {/* ACCOUNT CREATED */}
              <div className="account-detail-card">
                <div className="detail-header">
                  <h3>Account created</h3>
                </div>
                <div className="detail-content">
                  <div className="display-content">
                    <span className="display-value">Nov 28, 2025</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* SIGN-IN METHODS SECTION */}
          <div className="signin-methods-section">
            <div className="section-header">
              <h2 className="section-title">Sign-in methods</h2>
              <p className="section-subtitle">Manage your ways of logging into xAI & Grok.</p>
            </div>
            
            <div className="methods-grid">
              {/* EMAIL & PASSWORD */}
              <div className="signin-method-card">
                <div className="method-header">
                  <div className="method-icon email-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                    </svg>
                  </div>
                  <div className="method-info">
                    <h4>Email & password</h4>
                    <p>Enable login with email</p>
                  </div>
                </div>
                <button className="method-action-btn primary">Enable</button>
              </div>

              {/* CONNECTED ACCOUNTS */}
              <div className="signin-method-card connected">
                <div className="method-header">
                  <div className="method-icon google-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                  </div>
                  <div className="method-info">
                    <h4>Google</h4>
                    <p>im24562@gmail.com</p>
                  </div>
                </div>
                <div className="method-actions">
                  <button className="method-action-btn primary small">Primary</button>
                  <button className="method-action-btn secondary small">Disable</button>
                </div>
              </div>

              {/* APPLE */}
              <div className="signin-method-card">
                <div className="method-header">
                  <div className="method-icon apple-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-2.07-1.04-3.7-1.04s-2.46 1.15-3.7 1.15c-1.33 0-2.2-1.21-3.05-2.47-1.19-1.77-1.17-5.33-1.11-6.42.06-1.25 1.43-4.06 3.42-5.72C7.73 4.46 7.79 4 8.67 4c1.03 0 2.34 1.69 3.81 1.69s2.92-1.69 3.81-1.69c.88 0 .94.46 2.23 1.82 1.99 1.64 3.36 4.47 3.42 5.72.06 1.09.08 4.65-1.17 6.46zM13 4.08c-.48 0-1.05.19-1.72.55-.59.36-1.05.88-1.36 1.49-.31.6-.35 1.28-.15 1.9.2.62.61 1.08 1.17 1.31.57.23 1.2.11 1.68-.33.48-.44.69-1.04.52-1.63-.17-.59-.67-1.03-1.14-1.19z"/>
                    </svg>
                  </div>
                  <div className="method-info">
                    <h4>Apple</h4>
                    <p>Connect Apple account</p>
                  </div>
                </div>
                <button className="method-action-btn primary">Connect</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManageAccount;