import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import Sidebar from './components/Sidebar/Sidebar';
import Main from './components/Main/Main';
import AuthModal from './components/AuthModal/AuthModal';
import SettingsModal from './components/Sidebar/SettingsModal';
import HelpModal from './components/Sidebar/HelpModal';
import SubscriptionPage from './components/Pages/SubscriptionPage';
import ManageAccount from './components/Pages/ManageAccount';
import Feedback from './components/Pages/Feedback';
import { LoadingProvider } from "./context/LoadingContext";
import LoadingOverlay from "./components/LoadingOverlay";
import { AuthProvider } from "./context/AuthContext";
import './styles/themes.css'; // ✅ Import theme styles

import { useLocation } from "react-router-dom";


const AppContent = () => {

  const location = useLocation();
  const isSharedView = location.pathname.startsWith("/shared/");


  const [currentChat, setCurrentChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newChatFromMain, setNewChatFromMain] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);
  const navigate = useNavigate();

  // ✅ Initialize theme on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';

    if (savedTheme === 'auto') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');

      // Listen for system theme changes
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = (e) => {
        if (localStorage.getItem('theme') === 'auto') {
          document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
        }
      };
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else {
      document.documentElement.setAttribute('data-theme', savedTheme);
    }
  }, []);

  // CRITICAL FIX: Restore currentChat and messages from localStorage on mount
  useEffect(() => {
    const storedChat = localStorage.getItem("currentChat");
    if (storedChat) {
      try {
        const chat = JSON.parse(storedChat);
        const chatObj = typeof chat === "string" ? { id: chat } : chat;
        setCurrentChat(chatObj);

        // Also restore messages for this chat
        const chatId = chatObj.id || chatObj;
        const storedMessages = localStorage.getItem(`messages-${chatId}`);
        if (storedMessages) {
          try {
            const parsed = JSON.parse(storedMessages);
            // Force bot messages to be complete
            const normalized = parsed.map(msg =>
              msg.from === "bot"
                ? { ...msg, text: msg.text || "", isComplete: true }
                : msg
            );
            setMessages(normalized);
          } catch (e) {
            console.error("Failed to parse messages", e);
          }
        }
      } catch (e) {
        console.error("Failed to parse currentChat", e);
      }
    }
  }, []); // Run only once on mount

  // Password reset logic
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const provider = urlParams.get('provider');

    if (token && provider !== 'google') {
      setIsAuthModalOpen(true);
      setTimeout(() => {
        window.history.replaceState({}, document.title, window.location.pathname);
      }, 1000);
    }
  }, []);

  return (
    <>
      <div className="app-layout">
        {!isSharedView && <Sidebar
          currentChat={currentChat}
          setCurrentChat={setCurrentChat}
          messages={messages}
          setMessages={setMessages}
          newChatFromMain={newChatFromMain}
          onOpenAuthModal={() => setIsAuthModalOpen(true)}
          onOpenHelp={() => setIsHelpModalOpen(true)}
        />}

        <div className="main-wrapper">
          <Main
            currentChat={currentChat}
            setCurrentChat={setCurrentChat}
            messages={messages}
            setMessages={setMessages}
            onNewChat={(chat) => setNewChatFromMain(chat)}
            onOpenAuthModal={() => setIsAuthModalOpen(true)}
          />
        </div>
      </div >

      <SettingsModal
        open={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
      />

      <HelpModal
        open={isHelpModalOpen}
        onClose={() => setIsHelpModalOpen(false)}
      />

      <AuthModal
        open={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <LoadingProvider>
        <LoadingOverlay />
        <Router>
          <Routes>
            <Route path="/" element={<AppContent />} />
            <Route path="/subscription" element={<SubscriptionPage />} />
            <Route path="/manage-account" element={<ManageAccount />} />
            <Route path="/feedback" element={<Feedback />} />
            <Route path="/chat/:chatId" element={<AppContent />} />
            <Route path="/shared/:token" element={<AppContent />} />
          </Routes>
        </Router>
      </LoadingProvider>
    </AuthProvider>
  );
};

export default App;