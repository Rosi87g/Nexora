import React, { useState, useContext, useEffect, useRef } from "react";
import "./Sidebar.css";
import { assets } from "../../assets/assets";
import { AuthContext } from "../../context/AuthContext";
import { useLoading } from "../../context/LoadingContext";
import axios from "axios";
import { apiAxios } from "@/lib/api";
import SettingsModal from "./SettingsModal";
import ShareChatModal from "./ShareChatModal";

const Sidebar = ({ newChatFromMain, currentChat, setCurrentChat, messages, setMessages, onOpenHelp, onOpenAuthModal }) => {
  const { user } = useContext(AuthContext);
  const { setLoading } = useLoading();

  const [extended, setExtended] = useState(!!user);
  const [recentChats, setRecentChats] = useState(
    JSON.parse(localStorage.getItem("recentChats")) || []
  );
  const [openMenuId, setOpenMenuId] = useState(null);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
  const [animatingChatId, setAnimatingChatId] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [selectedChatForShare, setSelectedChatForShare] = useState(null);
  const menuRefs = useRef({});

  useEffect(() => {
    if (user) {
      setExtended(true);
    } else {
      setExtended(false);
    }
  }, [user]);

  useEffect(() => {
    const storedChats = JSON.parse(localStorage.getItem("recentChats"));
    const storedCurrentChat = JSON.parse(localStorage.getItem("currentChat"));

    if (storedChats) setRecentChats(storedChats);
    if (storedCurrentChat && setCurrentChat) {
      if (typeof storedCurrentChat === "string") {
        setCurrentChat({ id: storedCurrentChat });
      } else {
        setCurrentChat(storedCurrentChat);
      }
    }
  }, []);

  useEffect(() => {
    if (newChatFromMain && user) {
      setRecentChats(prev => {
        const existingIndex = prev.findIndex(c => String(c.id) === String(newChatFromMain.id));

        if (existingIndex !== -1) {
          if (existingIndex === 0) {
            const updated = [...prev];
            updated[0] = { ...updated[0], ...newChatFromMain };
            localStorage.setItem("recentChats", JSON.stringify(updated));
            return updated;
          } else {
            const updated = [
              { ...prev[existingIndex], ...newChatFromMain },
              ...prev.filter((_, i) => i !== existingIndex)
            ];
            localStorage.setItem("recentChats", JSON.stringify(updated));
            return updated;
          }
        }

        setAnimatingChatId(newChatFromMain.id);
        setTimeout(() => setAnimatingChatId(null), 800);

        const updated = [newChatFromMain, ...prev];
        localStorage.setItem("recentChats", JSON.stringify(updated));
        return updated;
      });
    }
  }, [newChatFromMain, user]);

  useEffect(() => {
    if (user?.token) fetchChats();
  }, [user?.token]);

  const fetchChats = async () => {
    try {
      setLoading(true);
      const res = await apiAxios.get("/list", {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      setRecentChats(res.data || []);
      localStorage.setItem("recentChats", JSON.stringify(res.data || []));
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch chats:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!currentChat) return;

    const currentId = currentChat.id || currentChat;

    setRecentChats(prev => {
      const exists = prev.find(c => String(c.id) === String(currentId));

      if (exists) return prev;

      const toAdd = typeof currentChat === "string"
        ? { id: currentChat, title: "New Chat" }
        : currentChat;

      setAnimatingChatId(toAdd.id);
      setTimeout(() => setAnimatingChatId(null), 800);

      const updated = [toAdd, ...prev];
      localStorage.setItem("recentChats", JSON.stringify(updated));
      return updated;
    });
  }, [currentChat]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (openMenuId && !e.target.closest('.options') && !e.target.closest('.menu-dropdown')) {
        setOpenMenuId(null);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [openMenuId]);

  const handleNewChat = async () => {
    if (!user?.token) return;
    try {
      const res = await apiAxios.post(
        "/new",
        {},
        { headers: { Authorization: `Bearer ${user.token}` } }
      );
      const newChat = { id: res.data.id, title: res.data.title };
      setRecentChats(prev => {
        const updated = [newChat, ...prev];
        localStorage.setItem("recentChats", JSON.stringify(updated));
        return updated;
      });
      setCurrentChat(newChat);
      localStorage.setItem("currentChat", JSON.stringify(newChat));
      setMessages([]);
    } catch (err) {
      console.error("Failed to create new chat:", err);
    }
  };

  const handleSettingsClick = () => {
    setIsSettingsOpen(true);
  };

  const handleHelpClick = () => {
    if (onOpenHelp) {
      onOpenHelp();
    }
  };

  const toggleMenu = (id, event) => {
    if (openMenuId === id) {
      setOpenMenuId(null);
      return;
    }

    const button = event.currentTarget;
    const rect = button.getBoundingClientRect();

    setMenuPosition({
      top: rect.top + rect.height / 2,
      left: rect.left - 130,
    });

    setOpenMenuId(id);
  };

  const selectChat = async (chat) => {
    setCurrentChat(chat);
    localStorage.setItem("currentChat", JSON.stringify(chat));

    const storedMessages = JSON.parse(localStorage.getItem(`messages-${chat.id}`));
    if (storedMessages) {
      setMessages(storedMessages);
      return;
    }

    try {
      const res = await apiAxios.get(`/${chat.id}/history`, {
        headers: { Authorization: `Bearer ${user?.token}` },
      });

      const messagesArr = [];
      (res.data.messages || []).forEach(msg => {
        messagesArr.push({ from: "user", text: msg.user_message });
        messagesArr.push({ from: "bot", text: msg.bot_reply });
      });

      setMessages(messagesArr);
      localStorage.setItem(`messages-${chat.id}`, JSON.stringify(messagesArr));
    } catch (err) {
      console.error("Failed to fetch chat history:", err);
      setMessages([]);
    }
  };

  const renameChat = async id => {
    const newTitle = prompt("Enter new chat title:");
    if (!newTitle?.trim()) {
      setOpenMenuId(null);
      return;
    }

    try {
      await apiAxios.put(
        `/${id}/rename`,
        { title: newTitle },
        { headers: { Authorization: `Bearer ${user.token}` } }
      );
      const updatedChats = recentChats.map(chat =>
        chat.id === id ? { ...chat, title: newTitle } : chat
      );
      setRecentChats(updatedChats);
      localStorage.setItem("recentChats", JSON.stringify(updatedChats));

      if (currentChat?.id === id) {
        const updatedChat = { ...currentChat, title: newTitle };
        setCurrentChat(updatedChat);
        localStorage.setItem("currentChat", JSON.stringify(updatedChat));
      }
    } catch (err) {
      console.error(err);
      alert("Failed to rename chat");
    }

    setOpenMenuId(null);
  };

  const deleteChat = async id => {
    const confirmed = confirm("Are you sure you want to delete this chat?");
    if (!confirmed) {
      setOpenMenuId(null);
      return;
    }

    try {
      await apiAxios.delete(`/${id}`, {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      const updatedChats = recentChats.filter(chat => chat.id !== id);
      setRecentChats(updatedChats);
      localStorage.setItem("recentChats", JSON.stringify(updatedChats));
      localStorage.removeItem(`messages-${id}`);

      if (currentChat?.id === id) {
        setCurrentChat(null);
        localStorage.removeItem("currentChat");
        setMessages([]);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to delete chat");
    }

    setOpenMenuId(null);
  };

  const shareChat = (id) => {
    const chat = recentChats.find(c => c.id === id);
    if (chat) {
      setSelectedChatForShare(chat);
      setShareModalOpen(true);
    }
    setOpenMenuId(null);
  };

  const ProfileAvatar = ({ size = 36, onClick }) => {
    // Check both possible picture sources
    const profileImage = user?.picture || user?.photoURL;
    const emailInitial = user?.email?.charAt(0)?.toUpperCase() || user?.name?.charAt(0)?.toUpperCase() || 'U';

    return (
      <div
        className={`profile-avatar-wrapper ${onClick ? 'clickable' : ''}`}
        onClick={onClick}
        style={{
          width: size,
          height: size,
          position: 'relative',
          flexShrink: 0
        }}
      >
        {profileImage ? (
          <img
            src={profileImage}
            alt="Profile"
            className="profile-image google-profile-img"
            style={{
              width: '100%',
              height: '100%',
              borderRadius: '50%',
              objectFit: 'cover'
            }}
            onError={(e) => {
              // Hide image and show initial on error
              e.target.style.display = 'none';
            }}
          />
        ) : null}

        {/* Fallback initial - always render but hide if image loads */}
        <div
          className="profile-initial"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: profileImage ? 'none' : 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: '#ffffff',
            fontSize: `${size * 0.45}px`,
            fontWeight: '600',
            borderRadius: '50%',
            textTransform: 'uppercase'
          }}
        >
          {emailInitial}
        </div>

        {user && (
          <div
            className="online-indicator"
            style={{
              position: 'absolute',
              bottom: 0,
              right: 0,
              width: `${size * 0.25}px`,
              height: `${size * 0.25}px`,
              background: '#22c55e',
              border: '2px solid #1e293b',
              borderRadius: '50%'
            }}
          />
        )}
      </div>
    );
  };

  return (
    <>
      <div className={`sidebar ${extended ? "open" : "closed"}`}>
        {extended && <img src={assets.octopus_logo} className="octopus-logo" alt="logo" />}

        <div className="top">
          <img
            onClick={() => setExtended(prev => !prev)}
            className="menu"
            src={extended ? assets.close_icon : assets.menu_icon}
            alt="menu"
            data-tooltip={!extended ? "Menu" : ""}
          />

          {user && (
            <div
              className="new-chat slide-fade"
              onClick={handleNewChat}
              data-tooltip={!extended ? "New Chat" : ""}
            >
              <img className="plus-icon" src={assets.plus_icon} alt="+" />
              {extended && <p>New Chat</p>}
            </div>
          )}

          {user && extended && (
            <div className="recent">
              <p className="recent-title">Recent</p>
              {recentChats.map(chat => (
                <div
                  key={chat.id}
                  className="recent-entry"
                  data-tooltip={!extended ? chat.title : ""}
                >
                  <div
                    className="options"
                    onClick={e => e.stopPropagation()}
                    ref={el => menuRefs.current[chat.id] = el}
                  >
                    <img
                      src={assets.three_dots}
                      alt="options"
                      onClick={(e) => toggleMenu(chat.id, e)}
                      style={{ cursor: "pointer", width: 16, flexShrink: 0 }}
                    />
                  </div>

                  <p
                    onClick={() => selectChat(chat)}
                    title={chat.title}
                    style={{
                      margin: 2,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      flex: 1,
                      minWidth: 0,
                      cursor: "pointer",
                    }}
                  >
                    {chat.title}
                  </p>
                  <img
                    src={assets.message_icon}
                    alt="message"
                    style={{ width: 20, height: 20, marginRight: 0 }}
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bottom">
          {!extended && user && (
            <div
              className="recent-icon-wrapper"
              onClick={() => setExtended(true)}
              data-tooltip="Recent Chats"
            >
              <img src={assets.recent_icon} alt="recent" style={{ width: 20, height: 20 }} />
            </div>
          )}

          <div
            className="bottom-item recent-entry"
            onClick={handleHelpClick}
            data-tooltip={!extended ? "Help & Guide" : ""}
          >
            <img src={assets.question_icon} alt="help" />
            {extended && <p>Help & Guide</p>}
          </div>

          <div
            className="bottom-item recent-entry"
            onClick={handleSettingsClick}
            data-tooltip={!extended ? "Settings" : ""}
          >
            <img src={assets.setting_icon} alt="settings" />
            {extended && <p>Settings</p>}
          </div>

          {!extended && user && (
            <div
              className="user-initial-wrapper"
              onClick={() => setExtended(true)}
              data-tooltip="Profile"
            >
              <ProfileAvatar size={36} />
            </div>
          )}

          {user && extended && (
            <div className="profile-section slide-fade">
              <ProfileAvatar size={48} />
              <div className="profile-text">
                <p className="profile-name">{user.name || user.email}</p>
                <p className="profile-email">{user.email}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {openMenuId && (
        <div
          className="menu-dropdown"
          style={{
            top: `${menuPosition.top}px`,
            left: `${menuPosition.left}px`,
          }}
        >
          <p onClick={() => shareChat(openMenuId)}>
            <span className="menu-icon">🔗</span> Share
          </p>
          <p onClick={() => renameChat(openMenuId)}>
            <span className="menu-icon">✏️</span> Rename
          </p>
          <p onClick={() => deleteChat(openMenuId)} className="delete-option">
            <span className="menu-icon">🗑️</span> Delete
          </p>
        </div>
      )}

      {isSettingsOpen && (
        <SettingsModal
          open={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
          onOpenAuthModal={onOpenAuthModal}
        />
      )}

      {shareModalOpen && selectedChatForShare && (
        <ShareChatModal
          open={shareModalOpen}
          onClose={() => {
            setShareModalOpen(false);
            setSelectedChatForShare(null);
          }}
          chatId={selectedChatForShare.id}
          chatTitle={selectedChatForShare.title}
          user={user}
        />
      )}
    </>
  );
};

export default Sidebar;