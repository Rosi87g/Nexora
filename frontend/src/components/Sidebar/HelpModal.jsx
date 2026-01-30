import React, { useState, useEffect } from 'react';
import './HelpModal.css'; // We'll create this CSS file

const HelpModal = ({ open, onClose }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) {
      setActiveTab('overview');
    }
  }, [open]);

  if (!open) return null;

  if (loading) {
    return (
      <div className="help-modal-overlay">
        <div className="help-modal">
          <div className="help-header">
            <h2>Help & Guide</h2>
            <button className="close-btn" onClick={onClose}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </button>
          </div>
          <div className="help-body">
            <div style={{
              flex: 1, display: 'flex', alignItems: 'center',
              justifyContent: 'center', color: '#ffffff'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                <div style={{
                  width: '40px', height: '40px',
                  border: '3px solid rgba(14, 165, 233, 0.3)',
                  borderTop: '3px solid #0ea5e9', borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                <span>Loading help...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const renderOverviewContent = () => (
    <div className="help-content">
      <h3>What is Nexora?</h3>
      <p>Nexora is your personal AI assistant, designed as your second brain. It's a sovereign AI that remembers everything you tell it, free from corporate filters. Nexora can handle general questions, math problems, code explanations, document analysis, image processing, and more. It's built to learn from interactions and improve over time.</p>
      
      <h3>Key Features</h3>
      <ul>
        <li>Chat with AI: Ask anything from casual queries to complex problems.</li>
        <li>File Upload: Analyze PDFs, documents, images, code files, spreadsheets.</li>
        <li>Voice Input: Speak your questions instead of typing.</li>
        <li>Self-Learning: Improves responses based on feedback and usage.</li>
        <li>Multi-Model Support: Switch between different AI models.</li>
        <li>Guest Mode: Try 10 messages without signing up.</li>
        <li>Secure Auth: Login with email or Google.</li>
      </ul>
    </div>
  );

  const renderHowToUseContent = () => (
    <div className="help-content">
      <h3>Getting Started</h3>
      <p>1. Sign up or log in using email or Google.</p>
      <p>2. Start a new chat by typing your question in the bottom input box.</p>
      <p>3. Press Enter or click the send button to submit.</p>
      <p>4. For files: Click the upload icon and select a file (PDF, image, doc, etc.).</p>
      <p>5. For voice: Click the mic icon when the input is empty.</p>
      
      <h3>Tips</h3>
      <ul>
        <li>Use Shift+Enter for new lines in messages.</li>
        <li>Edit messages: Click the edit icon on your messages.</li>
        <li>Feedback: Use thumbs up/down on AI responses.</li>
        <li>Stop generation: Click the stop button during response.</li>
        <li>Regenerate: Click the regenerate icon on responses.</li>
      </ul>
    </div>
  );

  const renderWhatItDoesContent = () => (
    <div className="help-content">
      <h3>Core Capabilities</h3>
      <p>Nexora processes text, files, and images using advanced AI:</p>
      <ul>
        <li><strong>General Q&A</strong>: Answers any question like a smart assistant.</li>
        <li><strong>Math & Code</strong>: Solves equations, explains code, generates snippets.</li>
        <li><strong>Document Analysis</strong>: Upload files for summaries, extractions, Q&A.</li>
        <li><strong>Image Processing</strong>: Describe, analyze, or query images.</li>
        <li><strong>Memory</strong>: Remembers past conversations for context.</li>
        <li><strong>Self-Improvement</strong>: Learns from feedback to give better answers.</li>
      </ul>
      
      <h3>Suggestions</h3>
      <p>Try asking: "Explain quantum computing simply" or upload a PDF and ask "Summarize this document".</p>
    </div>
  );

  const renderFAQContent = () => (
    <div className="help-content">
      <h3>Frequently Asked Questions</h3>
      <ul className="faq-list">
        <li>
          <strong>Is Nexora free?</strong>
          <p>Yes, with guest mode (10 messages). Sign up for unlimited access.</p>
        </li>
        <li>
          <strong>How secure is my data?</strong>
          <p>All data is encrypted. We don't share or sell your information.</p>
        </li>
        <li>
          <strong>Can Nexora handle multiple languages?</strong>
          <p>Yes, it supports many languages for questions and responses.</p>
        </li>
        <li>
          <strong>What file types are supported?</strong>
          <p>PDF, DOC, TXT, images (JPG, PNG), code files, spreadsheets.</p>
        </li>
        <li>
          <strong>How does self-learning work?</strong>
          <p>Nexora improves based on your feedback (thumbs up/down).</p>
        </li>
        <li>
          <strong>Why is there a loading delay?</strong>
          <p>Complex queries may take time to process for accurate responses.</p>
        </li>
        <li>
          <strong>Can I delete my data?</strong>
          <p>Settings → Data Controls → Delete All Chats</p>
        </li>
      </ul>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'overview': return renderOverviewContent();
      case 'howtouse': return renderHowToUseContent();
      case 'whatitdoes': return renderWhatItDoesContent();
      case 'faq': return renderFAQContent();
      default: return renderOverviewContent();
    }
  };

  return (
    <div className="help-modal-overlay">
      <div className="help-modal">
        <div className="help-header">
          <h2>Help & Guide</h2>
          <button className="close-btn" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <div className="help-body">
          <div className="help-sidebar">
            {[
              { id: 'overview', label: 'Overview', icon: 'info' },
              { id: 'howtouse', label: 'How to Use', icon: 'guide' },
              { id: 'whatitdoes', label: 'What It Does', icon: 'features' },
              { id: 'faq', label: 'FAQ', icon: 'question' }
            ].map((tab) => (
              <div
                key={tab.id}
                className={`sidebar-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <div className="tab-icon">
                  {/* You can add SVG icons similar to SettingsModal */}
                </div>
                <span className="tab-label">{tab.label}</span>
              </div>
            ))}
          </div>
          <div className="help-content-wrapper">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpModal;