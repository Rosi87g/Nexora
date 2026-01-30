import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import './SettingsModal.css';
import { AuthContext } from '../../context/AuthContext';
import { apiAxios } from '@/lib/api';
import responseStyleService from '../ResponseStyleService';
import { useNavigate } from 'react-router-dom';

const SettingsModal = ({ open, onClose, onOpenAuthModal }) => {
  const [activeTab, setActiveTab] = useState('account');
  const [userData, setUserData] = useState(null);
  const [isEditingName, setIsEditingName] = useState(false);
  const [editName, setEditName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);
  const [fontSize, setFontSize] = useState("medium");
  const [lineSpacing, setLineSpacing] = useState("normal");
  const [successMessage, setSuccessMessage] = useState('');
  const [responseStyle, setResponseStyle] = useState(() => {
    return responseStyleService.getCurrentStyle();
  });
  const [theme, setTheme] = useState('dark');
  const [knowledgeMemoryEnabled, setKnowledgeMemoryEnabled] = useState(true);
  const [isLoadingChats, setIsLoadingChats] = useState(false);
  const [allChats, setAllChats] = useState([]);
  const [filteredChats, setFilteredChats] = useState([]);
  const [chatSearchQuery, setChatSearchQuery] = useState('');
  const [showChatsModal, setShowChatsModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [retentionPolicy, setRetentionPolicy] = useState('forever');
  const { user: authUser, logout } = useContext(AuthContext);
  const [uploadingPicture, setUploadingPicture] = useState(false);
  const fileInputRef = useRef(null);
  const [apiKeys, setApiKeys] = useState([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [justCreatedKey, setJustCreatedKey] = useState(null);
  const [apiKeyError, setApiKeyError] = useState('');
  const [apiKeySuccess, setApiKeySuccess] = useState('');
  const [loadingApiKeys, setLoadingApiKeys] = useState(false);
  const [openMenuId, setOpenMenuId] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [ownedBy, setOwnedBy] = useState('You');
  const [selectedPermissions, setSelectedPermissions] = useState('All');
  const navigate = useNavigate();

  useEffect(() => {
    if (!open || activeTab !== 'api-keys') {
      setShowCreateModal(false);
      setNewKeyName('');
      setOwnedBy('You');
      setSelectedPermissions('All');
    }
  }, [open, activeTab]);

  useEffect(() => {
    if (!open) {
      setActiveTab('account');
      setError('');
      setSuccessMessage('');
      setShowDeleteConfirm(false);
      setShowChatsModal(false);
      setChatSearchQuery('');
      setJustCreatedKey(null);
      setApiKeyError('');
      setApiKeySuccess('');
      setOpenMenuId(null);
    }
  }, [open]);

  useEffect(() => {
    if (open && activeTab === 'data') {
      fetchKnowledgeMemoryStatus();
      fetchRetentionPolicy();
    }
  }, [open, activeTab]);

  useEffect(() => {
    if (open && activeTab === 'api-keys') {
      fetchApiKeys();
    }
  }, [open, activeTab]);

  useEffect(() => {
    if (!open) return;

    const handleProfilePictureClick = () => {
      fileInputRef.current?.click();
    };

    const handleFileChange = async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
      if (!validTypes.includes(file.type)) {
        setError('Please upload a valid image file (JPG, PNG, GIF, or WebP)');
        setTimeout(() => setError(''), 4000);
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        setError('Image size must be less than 5MB');
        setTimeout(() => setError(''), 4000);
        return;
      }

      try {
        setUploadingPicture(true);
        setError('');
        const formData = new FormData();
        formData.append('file', file);

        const res = await apiAxios.post('/api/profile/upload-picture', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        setUserData(prev => ({
          ...prev,
          picture: res.data.picture_url
        }));

        setSuccessMessage('Profile picture updated successfully!');
        setTimeout(() => setSuccessMessage(''), 3000);
        setTimeout(() => window.location.reload(), 1000);
      } catch (err) {
        console.error('Failed to upload profile picture:', err);
        setError(err.response?.data?.detail || 'Failed to upload profile picture');
        setTimeout(() => setError(''), 4000);
      } finally {
        setUploadingPicture(false);
        e.target.value = null;
      }
    };

    const handleDeletePicture = async () => {
      const confirmed = confirm('Are you sure you want to delete your profile picture?');
      if (!confirmed) return;

      try {
        setError('');
        await apiAxios.delete('/api/profile/delete-picture');
        setUserData(prev => ({
          ...prev,
          picture: null
        }));
        setSuccessMessage('Profile picture deleted successfully!');
        setTimeout(() => setSuccessMessage(''), 3000);
        setTimeout(() => window.location.reload(), 1000);
      } catch (err) {
        console.error('Failed to delete profile picture:', err);
        setError(err.response?.data?.detail || 'Failed to delete profile picture');
        setTimeout(() => setError(''), 4000);
      }
    };

    const fetchUserData = async () => {
      try {
        setLoading(true);
        setError('');
        const res = await apiAxios.get("/auth/me");
        const data = res.data;
        const userInfo = {
          id: data.id || null,
          name: data.name || 'User',
          email: data.email || 'user@example.com',
          picture: data.picture || null,
          provider: data.provider || 'email',
          is_verified: data.is_verified || false,
          created_at: data.created_at || null,
          google_id: data.google_id || null,
        };
        setUserData(userInfo);
        setEditName(userInfo.name);
      } catch (err) {
        console.error("Failed to fetch user data:", err);
        let msg = "Could not load account information.";
        if (err.response?.status === 401) {
          msg = "You are not logged in. Please sign in again.";
        } else if (err.response?.data?.detail) {
          msg = err.response.data.detail;
        }
        setError(msg);
        setUserData({
          name: "Guest User",
          email: "guest@example.com",
          picture: null,
          provider: "email",
          is_verified: false,
          created_at: null,
        });
        setEditName("Guest User");
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();

    const input = fileInputRef.current;
    if (input) {
      input.addEventListener('change', handleFileChange);
    }

    return () => {
      if (input) {
        input.removeEventListener('change', handleFileChange);
      }
    };
  }, [open]);

  const fetchApiKeys = useCallback(async () => {
    if (!authUser) return;
    try {
      setLoadingApiKeys(true);
      setApiKeyError('');
      const res = await apiAxios.get('/api_keys/api_keys/my-keys');
      setApiKeys(res.data);
    } catch (err) {
      console.error('Failed to fetch API keys:', err);
      setApiKeyError(err.response?.data?.detail || 'Failed to load API keys');
    } finally {
      setLoadingApiKeys(false);
    }
  }, [authUser]);

  const createNewApiKey = async () => {
    if (!newKeyName.trim()) {
      setApiKeyError('Please enter a name for the key');
      return;
    }
    try {
      setApiKeyError('');
      setApiKeySuccess('');
      setJustCreatedKey(null);
      const res = await apiAxios.post(`/api_keys/api_keys/create?name=${encodeURIComponent(newKeyName.trim())}`);
      const createdKey = res.data;
      setJustCreatedKey(createdKey);
      setApiKeys(prev => [...prev, {
        id: Date.now(),
        name: newKeyName.trim(),
        type: createdKey.type,
        scopes: createdKey.scopes,
        max_queries: createdKey.max_queries,
        query_count: 0,
        created_at: new Date().toISOString()
      }]);
      setApiKeySuccess('API key created! Copy it now — it will never be shown again.');
      setNewKeyName('');
      setTimeout(() => setJustCreatedKey(null), 15000);
      setShowCreateModal(false);
    } catch (err) {
      console.error('Failed to create API key:', err);
      setApiKeyError(err.response?.data?.detail || 'Failed to create API key');
    }
  };

  const handleRevokeKey = async (keyId, keyName) => {
    try {
      await apiAxios.delete(`/api_keys/api_keys/${keyId}`);
      setApiKeys(prev => prev.filter(k => k.id !== keyId));
      setApiKeySuccess(`API key "${keyName}" revoked successfully`);
      setTimeout(() => setApiKeySuccess(''), 4000);
    } catch (err) {
      console.error('Failed to revoke API key:', err);
      setApiKeyError(err.response?.data?.detail || 'Failed to revoke API key');
      setTimeout(() => setApiKeyError(''), 5000);
    }
  };

  const toggleMenu = (keyId) => {
    setOpenMenuId(openMenuId === keyId ? null : keyId);
  };

  const handleLogout = async () => {
    try {
      await logout();
      window.location.href = "/";
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  const fetchKnowledgeMemoryStatus = async () => {
    try {
      const res = await apiAxios.get('/knowledge-memory-status');
      setKnowledgeMemoryEnabled(res.data.enable_knowledge_memory);
    } catch (err) {
      console.error('Failed to fetch knowledge memory status:', err);
    }
  };

  const fetchRetentionPolicy = async () => {
    try {
      const res = await apiAxios.get('/user/retention-policy');
      setRetentionPolicy(res.data.policy || 'forever');
    } catch (err) {
      console.error('Failed to fetch retention policy:', err);
      setRetentionPolicy('forever');
    }
  };

  const handleRetentionPolicyChange = async (newPolicy) => {
    try {
      await apiAxios.post('/user/retention-policy', { policy: newPolicy });
      setRetentionPolicy(newPolicy);
      setSuccessMessage(
        newPolicy === 'forever'
          ? 'Chats will be kept forever.'
          : `Old chats will be auto-deleted after ${newPolicy === '30days' ? '30' : '90'} days.`
      );
      setTimeout(() => setSuccessMessage(''), 4000);
    } catch (err) {
      console.error('Failed to update retention policy:', err);
      setError('Failed to update data retention setting');
      setTimeout(() => setError(''), 4000);
    }
  };

  const handleKnowledgeMemoryToggle = async () => {
    try {
      const newValue = !knowledgeMemoryEnabled;
      await apiAxios.post('/knowledge-memory-toggle', {
        enable: newValue
      });
      setKnowledgeMemoryEnabled(newValue);
      setSuccessMessage(`Knowledge Memory ${newValue ? 'enabled' : 'disabled'}`);
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      console.error('Failed to toggle knowledge memory:', err);
      setError('Failed to update knowledge memory setting');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleViewAllChats = async () => {
    setIsLoadingChats(true);
    try {
      const res = await apiAxios.get('/list?limit=100');
      const chats = res.data;
      setAllChats(chats);
      setFilteredChats(chats);
      setShowChatsModal(true);
    } catch (err) {
      console.error('Failed to fetch chats:', err);
      setError('Failed to load chats');
      setTimeout(() => setError(''), 3000);
    } finally {
      setIsLoadingChats(false);
    }
  };

  useEffect(() => {
    if (!chatSearchQuery.trim()) {
      setFilteredChats(allChats);
      return;
    }
    const query = chatSearchQuery.toLowerCase();
    const filtered = allChats.filter(chat =>
      chat.title?.toLowerCase().includes(query)
    );
    setFilteredChats(filtered);
  }, [chatSearchQuery, allChats]);

  const handleDeleteAllChats = () => {
    setShowDeleteConfirm(true);
  };

  const confirmDeleteAllChats = async () => {
    setShowDeleteConfirm(false);
    try {
      await apiAxios.delete('/delete-all');
      setSuccessMessage('All chats deleted successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      console.error('Failed to delete all chats:', err);
      setError(err.response?.data?.detail || 'Failed to delete chats');
      setTimeout(() => setError(''), 3000);
    }
  };

  const downloadFile = (content, filename, type = 'text/plain') => {
    const blob = new Blob([content], { type });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const exportChats = async (format) => {
    try {
      if (!authUser) {
        const allStored = {};
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key && key.startsWith('messages-')) {
            try {
              allStored[key] = JSON.parse(localStorage.getItem(key) || '[]');
            } catch (e) {
              console.error('Error parsing stored messages:', key);
            }
          }
        }
        const dateStr = new Date().toISOString().slice(0, 10);
        let filename = `nexora-guest-chats-${dateStr}`;
        let content = '';
        if (format === 'json') {
          content = JSON.stringify(allStored, null, 2);
          filename += '.json';
          downloadFile(content, filename, 'application/json');
        } else {
          let text = `# Nexora Chat History (Guest Mode)\n\nExported on ${new Date().toLocaleString()}\n\n`;
          Object.keys(allStored).forEach(key => {
            const messages = allStored[key];
            const chatId = key.replace('messages-', '');
            text += `## Chat: ${chatId}\n\n`;
            messages.forEach(msg => {
              const role = msg.from === 'user' ? 'You' : 'Nexora';
              text += `**${role}:** ${msg.text || '[File uploaded]'}\n\n`;
              if (msg.file) {
                text += `_File: ${msg.file.name} (${(msg.file.size / 1024).toFixed(1)} KB)_\n\n`;
              }
            });
            text += `---\n\n`;
          });
          content = text;
          filename += format === 'markdown' ? '.md' : '.txt';
          if (format === 'txt') {
            content = content.replace(/[#*]/g, '');
          }
          downloadFile(content, filename);
        }
      } else {
        const res = await apiAxios.get(`/chat/export?format=${format}`, {
          responseType: 'blob'
        });
        const blob = res.data;
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const ext = format === 'markdown' ? 'md' : format;
        a.download = `nexora-chats-${authUser.email.split('@')[0]}-${new Date().toISOString().slice(0, 10)}.${ext}`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
      setSuccessMessage(`Chats exported as ${format.toUpperCase()}!`);
      setTimeout(() => setSuccessMessage(''), 4000);
    } catch (err) {
      console.error('Export failed:', err);
      setError('Failed to export chats');
      setTimeout(() => setError(''), 4000);
    }
  };

  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!file.name.endsWith('.json')) {
      setError('Only JSON files are supported for import');
      setTimeout(() => setError(''), 4000);
      return;
    }
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      if (authUser) {
        const formData = new FormData();
        formData.append('file', file);
        await apiAxios.post('/chat/import', formData);
        setSuccessMessage('Chats imported successfully! Refreshing...');
        setTimeout(() => window.location.reload(), 2000);
      } else {
        let imported = 0;
        Object.keys(data).forEach(key => {
          if (key.startsWith('messages-')) {
            localStorage.setItem(key, JSON.stringify(data[key]));
            imported++;
          }
        });
        setSuccessMessage(`Imported ${imported} chat(s)! Refresh to see them.`);
        setTimeout(() => window.location.reload(), 2000);
      }
    } catch (err) {
      console.error('Import failed:', err);
      setError('Invalid or corrupted JSON file');
      setTimeout(() => setError(''), 4000);
    }
    e.target.value = null;
  };

  const handleSaveName = useCallback(async () => {
    try {
      setError('');
      setSuccessMessage('');
      await apiAxios.patch("/auth/update-profile", {
        name: editName.trim()
      });
      setUserData(prev => ({ ...prev, name: editName.trim() }));
      setIsEditingName(false);
      setSuccessMessage('Name updated successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      console.error("Failed to update name:", err);
      setError(err.response?.data?.detail || "Failed to update name");
    }
  }, [editName]);

  const handleResponseStyleChange = (newStyle) => {
    const success = responseStyleService.setStyle(newStyle);
    if (success) {
      setResponseStyle(newStyle);
      setSuccessMessage(`Response style changed to ${newStyle}!`);
      setTimeout(() => setSuccessMessage(''), 3000);
    } else {
      setError('Failed to update response style');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleAutoScrollToggle = () => {
    setAutoScrollEnabled(prev => !prev);
  };

  const handleFontSizeChange = (e) => {
    setFontSize(e.target.value);
  };

  const handleLineSpacingChange = (e) => {
    setLineSpacing(e.target.value);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "Not available";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return "Not available";
    }
  };

  if (!open) return null;

  if (!authUser) {
    return (
      <div className="settings-modal-overlay">
        <div className="settings-modal guest-only">
          <div className="settings-header">
            <h2>Settings</h2>
            <button className="close-btn" onClick={onClose}>×</button>
          </div>
          <div className="guest-only-body">
            <div className="guest-card">
              <div className="guest-icon">🔒</div>
              <h3>Login required</h3>
              <p>
                Please login or signup to access account settings,
                preferences, and data controls.
              </p>
              <button
                className="settings-btn primary"
                onClick={() => {
                  onClose();
                  onOpenAuthModal();
                }}
              >
                Login / Sign Up
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const ProfileAvatar = ({ size = 40, editable = false }) => {
    const profileImage = userData?.picture || authUser?.picture || authUser?.photoURL;
    const emailInitial = userData?.email?.charAt(0)?.toUpperCase() ||
      userData?.name?.charAt(0)?.toUpperCase() ||
      authUser?.email?.charAt(0)?.toUpperCase() || 'U';

    return (
      <div
        className={`settings-profile-avatar-wrapper ${editable ? 'editable' : ''}`}
        style={{
          width: size,
          height: size,
          position: 'relative',
          flexShrink: 0,
          cursor: editable ? 'pointer' : 'default'
        }}
        onClick={editable ? handleProfilePictureClick : undefined}
      >
        {profileImage ? (
          <img
            src={profileImage.startsWith('/') ? `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${profileImage}` : profileImage}
            alt="Profile"
            className="settings-profile-image"
            style={{
              width: '100%',
              height: '100%',
              borderRadius: '50%',
              objectFit: 'cover',
              display: 'block'
            }}
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        ) : null}
        <div
          className="settings-profile-initial"
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
        {editable && (
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              right: 0,
              width: `${size * 0.3}px`,
              height: `${size * 0.3}px`,
              background: '#0ea5e9',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '2px solid #1e293b',
              fontSize: `${size * 0.15}px`
            }}
          >
            <svg width={size * 0.18} height={size * 0.18} viewBox="0 0 24 24" fill="white">
              <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
            </svg>
          </div>
        )}
        <div
          className="settings-online-indicator"
          style={{
            position: 'absolute',
            bottom: editable ? `${size * 0.05}px` : 0,
            right: editable ? `${size * 0.35}px` : 0,
            width: `${size * 0.25}px`,
            height: `${size * 0.25}px`,
            background: '#22c55e',
            border: '2px solid #1e293b',
            borderRadius: '50%'
          }}
        />
      </div>
    );
  };

  if (loading) {
    return (
      <div className="settings-modal-overlay">
        <div className="settings-modal">
          <div className="settings-header">
            <h2>Settings</h2>
            <button className="close-btn" onClick={onClose}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </button>
          </div>
          <div className="settings-body">
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  border: '3px solid rgba(14, 165, 233, 0.3)',
                  borderTop: '3px solid #0ea5e9',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                <span>Loading settings...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const renderDocsContent = () => {
    const models = [
      {
        id: 'nexora-1.1',
        name: 'Nexora 1.1',
        tagline: 'Flagship Intelligence',
        description: 'Our most advanced model with enhanced reasoning capabilities and superior performance across all tasks.',
        status: 'development',
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        features: [
          'Advanced reasoning and logic',
          'Complex problem solving',
          'Multi-step task execution',
          'Code generation & analysis'
        ],
        specs: {
          contextWindow: '8,192 tokens',
          maxTokens: '4,096 tokens',
          recommendedRam: '8GB',
          internalModel: 'qwen2.5:7b'
        }
      },
      {
        id: 'nexora-1.0',
        name: 'Nexora 1.0',
        tagline: 'Production Ready',
        description: 'Fast, efficient, and perfectly balanced. Your go-to model for everyday conversations and tasks.',
        status: 'production',
        gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        features: [
          'Optimized response speed',
          'Balanced quality & performance',
          'General conversation',
          'Quick task completion'
        ],
        specs: {
          contextWindow: '4,096 tokens',
          maxTokens: '2,048 tokens',
          recommendedRam: '4GB',
          internalModel: 'gemma3:4b'
        }
      },
      {
        id: 'nexora-lite',
        name: 'Nexora Lite',
        tagline: 'Lightning Fast',
        description: 'Ultra-fast responses for simple queries. Perfect when you need quick answers without the wait.',
        status: 'development',
        gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        features: [
          'Instant responses',
          'Low resource usage',
          'Simple queries',
          'Quick lookups'
        ],
        specs: {
          contextWindow: '2,048 tokens',
          maxTokens: '1,024 tokens',
          recommendedRam: '2GB',
          internalModel: 'qwen2.5:3b'
        }
      },
      {
        id: 'nexora-code',
        name: 'Nexora Code',
        tagline: 'Developer Specialized',
        description: 'Built for developers. Excels at code generation, debugging, and technical documentation.',
        status: 'development',
        gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        features: [
          'Code generation',
          'Bug detection & fixing',
          'Technical documentation',
          'Multiple programming languages'
        ],
        specs: {
          contextWindow: '8,192 tokens',
          maxTokens: '4,096 tokens',
          recommendedRam: '8GB',
          internalModel: 'qwen2.5:14b'
        }
      }
    ];

    return (
      <div style={{
        padding: '32px',
        color: '#e2e8f0',
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <div style={{ marginBottom: '48px' }}>
          <h1 style={{
            fontSize: '36px',
            fontWeight: '700',
            margin: '0 0 16px 0',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            Nexora AI Models
          </h1>
          <p style={{
            fontSize: '18px',
            color: '#94a3b8',
            lineHeight: '1.6',
            maxWidth: '800px'
          }}>
            Choose the perfect model for your needs. From lightning-fast responses to deep analytical thinking,
            we have you covered.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '24px',
          marginBottom: '48px'
        }}>
          {models.map((model) => (
            <div
              key={model.id}
              style={{
                background: '#1e293b',
                borderRadius: '16px',
                overflow: 'hidden',
                border: '1px solid #334155',
                transition: 'all 0.3s ease',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 20px 40px rgba(0,0,0,0.3)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={{
                background: model.gradient,
                padding: '32px 24px',
                position: 'relative'
              }}>
                <div style={{
                  position: 'absolute',
                  top: '16px',
                  right: '16px'
                }}>
                  {model.status === 'production' ? (
                    <span style={{
                      padding: '6px 12px',
                      background: 'rgba(16, 185, 129, 0.2)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                      borderRadius: '20px',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#1a392d',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px'
                    }}>
                      ✓ Production
                    </span>
                  ) : (
                    <span style={{
                      padding: '6px 12px',
                      background: 'rgba(178, 168, 144, 0.2)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(251, 191, 36, 0.3)',
                      borderRadius: '20px',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#272315',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px'
                    }}>
                      ⚙️ Development
                    </span>
                  )}
                </div>

                <h3 style={{
                  margin: '0 0 8px 0',
                  fontSize: '28px',
                  fontWeight: '700',
                  color: '#ffffff',
                  textShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}>
                  {model.name}
                </h3>
                <p style={{
                  margin: 0,
                  fontSize: '14px',
                  color: 'rgba(255,255,255,0.9)',
                  fontWeight: '500'
                }}>
                  {model.tagline}
                </p>
              </div>

              <div style={{ padding: '24px' }}>
                <p style={{
                  margin: '0 0 20px 0',
                  color: '#cbd5e1',
                  fontSize: '14px',
                  lineHeight: '1.6'
                }}>
                  {model.description}
                </p>

                <div style={{ marginBottom: '24px' }}>
                  <h4 style={{
                    margin: '0 0 12px 0',
                    fontSize: '13px',
                    color: '#94a3b8',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    fontWeight: '600'
                  }}>
                    Key Features
                  </h4>
                  <ul style={{
                    margin: 0,
                    padding: 0,
                    listStyle: 'none',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}>
                    {model.features.map((feature, idx) => (
                      <li key={idx} style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        fontSize: '13px',
                        color: '#cbd5e1'
                      }}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" fill="#10b981"/>
                        </svg>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>

                <div style={{
                  background: '#0f172a',
                  borderRadius: '8px',
                  padding: '16px',
                  fontSize: '12px'
                }}>
                  <h4 style={{
                    margin: '0 0 12px 0',
                    fontSize: '13px',
                    color: '#94a3b8',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    fontWeight: '600'
                  }}>
                    Technical Specs
                  </h4>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '12px'
                  }}>
                    <div>
                      <div style={{ color: '#64748b', marginBottom: '4px' }}>Context</div>
                      <div style={{ color: '#e2e8f0', fontWeight: '500' }}>{model.specs.contextWindow}</div>
                    </div>
                    <div>
                      <div style={{ color: '#64748b', marginBottom: '4px' }}>Max Output</div>
                      <div style={{ color: '#e2e8f0', fontWeight: '500' }}>{model.specs.maxTokens}</div>
                    </div>
                    <div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>      
      </div>
    );
  };

  const renderAccountContent = () => (
    <div className="settings-content">
      <div className="account-section-modern">
        <div className="welcome-header">
          <h1 className="welcome-title">Welcome, {userData?.name?.split(' ')[0] || 'User'}.</h1>
          <p className="welcome-subtitle">Manage your Nexora account.</p>
        </div>
        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            color: '#fca5a5',
            padding: '12px 16px',
            borderRadius: '10px',
            marginBottom: '24px',
            borderLeft: '4px solid #ef4444',
            fontSize: '14px'
          }}>
            ⚠️ {error}
          </div>
        )}
        {successMessage && (
          <div style={{
            background: 'rgba(34, 197, 94, 0.15)',
            color: '#86efac',
            padding: '12px 16px',
            borderRadius: '10px',
            marginBottom: '24px',
            borderLeft: '4px solid #22c55e',
            fontSize: '14px'
          }}>
            ✓ {successMessage}
          </div>
        )}
        <div className="profile-row">
          <div className="profile-info-container">
            <div className="profile-avatar-container">
              <ProfileAvatar size={40} />
            </div>
            <div className="profile-details">
              <div className="profile-name-row">
                <div className="online-dot"></div>
                <h3 className="profile-name">{userData?.name || 'User'}</h3>
                {userData?.is_verified && (
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '12px',
                    color: '#22c55e',
                    background: 'rgba(34, 197, 94, 0.1)',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    marginLeft: '8px'
                  }}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                    </svg>
                    Verified
                  </span>
                )}
              </div>
              <p className="profile-email">{userData?.email || 'user@example.com'}</p>
            </div>
          </div>
        </div>
        <div className="account-info-grid">
          <div className="account-info-card">
            <div className="card-header">
              <h3>Full name</h3>
              <button className="edit-btn" onClick={() => setIsEditingName(!isEditingName)}>
                {isEditingName ? 'Cancel' : 'Edit name'}
              </button>
            </div>
            <div className="card-content">
              {isEditingName ? (
                <div className="edit-input-container">
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="edit-input"
                    placeholder="Enter your full name"
                  />
                  <button className="save-btn" onClick={handleSaveName}>Save</button>
                </div>
              ) : (
                <div className="display-value">
                  <span className="value-text">{userData?.name || 'User'}</span>
                </div>
              )}
            </div>
          </div>
          <div className="account-info-card">
            <div className="card-header">
              <h3>Email</h3>
            </div>
            <div className="card-content">
              <div className="display-value">
                <span className="value-text">{userData?.email || 'user@example.com'}</span>
              </div>
            </div>
          </div>
          <div className="account-info-card">
            <div className="card-header">
              <h3>Account ID</h3>
            </div>
            <div className="card-content">
              <div className="display-value">
                <span className="value-text" style={{ fontSize: '13px', fontFamily: 'monospace' }}>
                  {userData?.id || 'N/A'}
                </span>
              </div>
            </div>
          </div>
          <div className="account-info-card">
            <div className="card-header">
              <h3>Account created</h3>
            </div>
            <div className="card-content">
              <div className="display-value">
                <span className="value-text">{formatDate(userData?.created_at)}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="signin-methods-section">
          <h3>Sign-in methods</h3>
          <p className="section-description">Manage your ways of logging into Nexora.</p>
          <div className="signin-methods-list">
            <div className="signin-method-item">
              <div className="method-info">
                <ProfileAvatar size={32} />
                <span>{userData?.provider === 'google' ? 'Google' : 'Email & Password'}</span>
              </div>
              <div className="method-actions">
                <button className="method-btn primary">Primary</button>
              </div>
            </div>
          </div>
        </div>
        <div style={{ marginTop: '32px' }}>
          <button
            onClick={handleLogout}
            className="settings-btn danger full-width"
            style={{
              width: '100%',
              padding: '14px',
              fontSize: '15px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px'
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Sign out
          </button>
        </div>
        <button className="return-btn" onClick={onClose}>
          ← Return to Nexora
        </button>
      </div>
    </div>
  );

  const renderAppearanceContent = () => (
    <div className="settings-content">
      <div className="theme-section">
        <h3>Theme</h3>
        <p className="section-description">Choose your preferred color theme</p>
        <div className="theme-options">
          {[
            { id: 'light', name: 'Light', class: 'light-theme' },
            { id: 'dark', name: 'Dark', class: 'dark-theme' },
            { id: 'auto', name: 'Auto', class: 'auto-theme' }
          ].map((themeOption) => (
            <div
              key={themeOption.id}
              className={`theme-option ${theme === themeOption.id ? 'active' : ''}`}
              onClick={() => {
                const newTheme = themeOption.id;
                setTheme(newTheme);
                if (newTheme === 'auto') {
                  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                  document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
                } else {
                  document.documentElement.setAttribute('data-theme', newTheme);
                }
                setSuccessMessage(`Theme changed to ${themeOption.name}`);
                setTimeout(() => setSuccessMessage(''), 3000);
              }}
            >
              <div className={`theme-preview ${themeOption.class}`}></div>
              <div className="theme-info">
                <h4>{themeOption.name}</h4>
                {themeOption.id === 'auto' && <p>Follows system preference</p>}
                {themeOption.id === 'light' && <p>Bright and clean</p>}
                {themeOption.id === 'dark' && <p>Dark and easy on the eyes</p>}
              </div>
              {theme === themeOption.id && <div className="theme-checkmark">✓</div>}
            </div>
          ))}
        </div>
      </div>
      <div className="appearance-section" style={{ marginTop: '32px' }}>
        <h3>Chat Text Appearance</h3>
        <p className="section-description">Customize font size and line spacing</p>
        <div className="appearance-option">
          <h4>Font size</h4>
          <select value={fontSize} onChange={handleFontSizeChange}>
            <option value="small">Small</option>
            <option value="medium">Medium</option>
            <option value="large">Large</option>
          </select>
        </div>
        <div className="appearance-option">
          <h4>Line spacing</h4>
          <select value={lineSpacing} onChange={handleLineSpacingChange}>
            <option value="compact">Compact</option>
            <option value="normal">Normal</option>
            <option value="comfortable">Comfortable</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderBehaviorContent = () => (
    <div className="settings-content">
      <div className="behavior-section">
        <div className="behavior-option">
          <div>
            <h4>Response Style</h4>
            <p>Choose how the AI responds to you</p>
          </div>
          <select
            className="settings-select"
            value={responseStyle}
            onChange={(e) => handleResponseStyleChange(e.target.value)}
          >
            <option value="concise">Concise - Brief and to-the-point</option>
            <option value="balanced">Balanced - Moderate detail</option>
            <option value="detailed">Detailed - Comprehensive explanations</option>
          </select>
        </div>
        <div className="behavior-option">
          <div>
            <h4>Auto-scroll chat</h4>
            <p>Automatically scroll while responses are generated</p>
          </div>
          <button
            onClick={handleAutoScrollToggle}
            className={`toggle-btn ${autoScrollEnabled ? "on" : "off"}`}
          >
            {autoScrollEnabled ? "On" : "Off"}
          </button>
        </div>
        <div style={{
          background: 'rgba(14, 165, 233, 0.1)',
          border: '1px solid rgba(14, 165, 233, 0.2)',
          borderRadius: '10px',
          padding: '16px',
          marginTop: '16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'start', gap: '12px' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{ marginTop: '2px', flexShrink: 0 }}>
              <circle cx="12" cy="12" r="10" stroke="#0ea5e9" strokeWidth="2" />
              <path d="M12 16v-4M12 8h.01" stroke="#0ea5e9" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <div>
              <h4 style={{ margin: '0 0 8px 0', color: '#0ea5e9', fontSize: '14px', fontWeight: '600' }}>
                Current Style: {responseStyle.charAt(0).toUpperCase() + responseStyle.slice(1)}
              </h4>
              <p style={{ margin: 0, color: '#94a3b8', fontSize: '13px', lineHeight: '1.5' }}>
                {responseStyle === 'concise' && 'AI will provide brief, to-the-point answers without unnecessary elaboration.'}
                {responseStyle === 'balanced' && 'AI will provide well-rounded responses with appropriate detail and context.'}
                {responseStyle === 'detailed' && 'AI will provide comprehensive, thorough explanations with examples and analysis.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderCustomizeContent = () => (
    <div className="settings-content">
      <div className="customize-section">
        <div className="customize-option">
          <h4>Chat Sidebar</h4>
          <p>Reset chat sidebar menu</p>
          <button className="settings-btn outline">Reset Sidebar</button>
        </div>
      </div>
    </div>
  );

  const renderApiKeysContent = () => (
    <div style={{
      padding: '24px 32px',
      color: '#e2e8f0'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '32px'
      }}>
        <h2 style={{
          margin: 0,
          fontSize: '28px',
          fontWeight: '600'
        }}>
          API Keys ({apiKeys.length})
        </h2>
        <button
          onClick={() => setShowCreateModal(true)}
          style={{
            padding: '10px 20px',
            background: '#10b981',
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            fontWeight: '500',
            cursor: 'pointer'
          }}
        >
          + Create new secret key
        </button>
      </div>

      {justCreatedKey && (
        <div style={{
          background: 'rgba(16,185,129,0.15)',
          border: '1px solid #10b981',
          borderRadius: '12px',
          padding: '16px 20px',
          marginBottom: '32px'
        }}>
          <strong style={{ color: '#6ee7b7' }}>New secret key created!</strong><br />
          Copy it now — you will never see it again.
          <div style={{
            background: '#0f172a',
            padding: '12px',
            borderRadius: '8px',
            fontFamily: 'monospace',
            wordBreak: 'break-all',
            margin: '12px 0'
          }}>
            {justCreatedKey.api_key}
          </div>
          <button
            onClick={() => {
              navigator.clipboard.writeText(justCreatedKey.api_key);
              setApiKeySuccess('Copied!');
              setTimeout(() => setApiKeySuccess(''), 2500);
            }}
            style={{
              padding: '8px 16px',
              background: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Copy secret key
          </button>
        </div>
      )}

      <div style={{
        background: 'rgba(234,179,8,0.12)',
        border: '1px solid rgba(234,179,8,0.3)',
        borderRadius: '12px',
        padding: '16px 20px',
        marginBottom: '32px',
        fontSize: '14px',
        color: '#fde047'
      }}>
        <strong>Do not share your API key</strong> with others or expose it in the browser or other client-side code.
        Any leaked key may be automatically disabled for security reasons.
      </div>

      {showCreateModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
          onClick={() => setShowCreateModal(false)}
        >
          <div
            style={{
              background: '#111827',
              borderRadius: '12px',
              width: '480px',
              maxWidth: '90%',
              padding: '24px',
              boxShadow: '0 20px 40px rgba(0,0,0,0.6)'
            }}
            onClick={e => e.stopPropagation()}
          >
            <h3 style={{
              margin: '0 0 20px 0',
              fontSize: '20px',
              fontWeight: '600'
            }}>
              Create new secret key
            </h3>

            <div style={{ marginBottom: '24px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                color: '#94a3b8'
              }}>
                Owned by
              </label>
              <div style={{
                display: 'flex',
                gap: '12px'
              }}>
                <button
                  onClick={() => setOwnedBy('You')}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '8px',
                    border: ownedBy === 'You' ? '2px solid #10b981' : '1px solid #475569',
                    background: ownedBy === 'You' ? 'rgba(16,185,129,0.15)' : 'transparent',
                    color: ownedBy === 'You' ? '#6ee7b7' : '#e2e8f0',
                    cursor: 'pointer'
                  }}
                >
                  You
                </button>
              </div>
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                color: '#94a3b8'
              }}>
                Name <span style={{ color: '#94a3b8', fontSize: '12px' }}>(*)</span>
              </label>
              <input
                type="text"
                required
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="My Test Key"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: '1px solid #475569',
                  background: '#0f172a',
                  color: '#e2e8f0'
                }}
              />
            </div>

            <div style={{ marginBottom: '32px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                color: '#94a3b8'
              }}>
                Permissions
              </label>
              <div style={{
                display: 'flex',
                gap: '12px'
              }}>
                {['All'].map(perm => (
                  <button
                    key={perm}
                    onClick={() => setSelectedPermissions(perm)}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '8px',
                      border: selectedPermissions === perm ? '2px solid #10b981' : '1px solid #475569',
                      background: selectedPermissions === perm ? 'rgba(16,185,129,0.15)' : 'transparent',
                      color: selectedPermissions === perm ? '#6ee7b7' : '#e2e8f0',
                      cursor: 'pointer'
                    }}
                  >
                    {perm}
                  </button>
                ))}
              </div>
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '12px'
            }}>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{
                  padding: '10px 20px',
                  background: 'transparent',
                  border: '1px solid #475569',
                  color: '#e2e8f0',
                  borderRadius: '8px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={createNewApiKey}
                disabled={!newKeyName.trim()}
                style={{
                  padding: '10px 20px',
                  background: newKeyName.trim() ? '#10b981' : '#374151',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '500',
                  cursor: newKeyName.trim() ? 'pointer' : 'not-allowed'
                }}
              >
                Create secret key
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{
        overflowX: 'auto',
        border: '1px solid #334155',
        borderRadius: '12px',
        background: '#111827',
        marginTop: '32px'
      }}>
        <table style={{
          width: '100%',
          minWidth: '1000px',
          borderCollapse: 'collapse'
        }}>
          <thead>
            <tr style={{
              background: '#1e293b',
              borderBottom: '1px solid #334155'
            }}>
              <th style={{ padding: '14px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>NAME</th>
              <th style={{ padding: '14px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>STATUS</th>
              <th style={{ padding: '14px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>SECRET KEY</th>
              <th style={{ padding: '14px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>CREATED</th>
              <th style={{ padding: '14px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>LAST USED</th>
              <th style={{ padding: '14px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>USAGE</th>
              <th style={{ padding: '14px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>CREATED BY</th>
              <th style={{ padding: '14px 20px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {apiKeys.map(key => (
              <tr key={key.id} style={{
                borderBottom: '1px solid #334155',
                transition: 'background 0.2s'
              }}
                onMouseEnter={e => e.currentTarget.style.background = '#1e293b'}
                onMouseLeave={e => e.currentTarget.style.background = '#111827'}
              >
                <td style={{ padding: '16px 20px', fontWeight: '500' }}>{key.name}</td>
                <td style={{ padding: '16px 20px' }}>
                  <span style={{
                    padding: '4px 12px',
                    background: '#064e3b',
                    color: '#6ee7b7',
                    borderRadius: '999px',
                    fontSize: '12px'
                  }}>
                    Active
                  </span>
                </td>
                <td style={{ padding: '16px 20px', fontFamily: 'monospace', color: '#94a3b8' }}>
                  ne-a-••••••••••••••••••••••••••••••••
                </td>
                <td style={{ padding: '16px 20px', color: '#94a3b8' }}>
                  {new Date(key.created_at).toLocaleDateString('en-GB', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric'
                  })}
                </td>
                <td style={{ padding: '16px 20px', color: '#94a3b8' }}>—</td>
                <td style={{ padding: '16px 20px', color: '#94a3b8' }}>
                  {key.query_count || 0} / {key.max_queries || 100}
                </td>
                <td style={{ padding: '16px 20px', color: '#94a3b8' }}>You</td>
                <td style={{ padding: '16px 20px' }}>
                  <button
                    onClick={() => handleRevokeKey(key.id, key.name)}
                    style={{
                      background: 'transparent',
                      border: '1px solid #ef4444',
                      color: '#ef4444',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '13px'
                    }}
                  >
                    Revoke
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {apiKeySuccess && (
        <div style={{
          marginTop: '24px',
          padding: '12px 20px',
          background: 'rgba(16,185,129,0.2)',
          borderRadius: '10px',
          color: '#6ee7b7'
        }}>
          ✓ {apiKeySuccess}
        </div>
      )}
      {apiKeyError && (
        <div style={{
          marginTop: '24px',
          padding: '12px 20px',
          background: 'rgba(239,68,68,0.2)',
          borderRadius: '10px',
          color: '#fca5a5'
        }}>
          ⚠️ {apiKeyError}
        </div>
      )}
    </div>
  );

  const renderDataContent = () => (
    <div className="settings-content">
      <div className="data-section">
        <div className="data-option">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h4>Improve Model</h4>
              <p>Help improve responses by learning from your conversations</p>
            </div>
            <button
              onClick={handleKnowledgeMemoryToggle}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                background: knowledgeMemoryEnabled ? '#22c55e' : '#64748b',
                color: '#ffffff',
                cursor: 'pointer',
                fontWeight: '600',
                transition: 'all 0.2s'
              }}
            >
              {knowledgeMemoryEnabled ? 'Enabled' : 'Disabled'}
            </button>
          </div>
          {knowledgeMemoryEnabled && (
            <div style={{
              background: 'rgba(34, 197, 94, 0.1)',
              border: '1px solid rgba(34, 197, 94, 0.2)',
              borderRadius: '8px',
              padding: '12px',
              fontSize: '13px',
              color: '#86efac'
            }}>
              ✓ Your conversations are being used to improve response quality
            </div>
          )}
          {!knowledgeMemoryEnabled && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: '8px',
              padding: '12px',
              fontSize: '13px',
              color: '#fca5a5'
            }}>
              ⓘ Learning is disabled. Responses may be less personalized.
            </div>
          )}
        </div>

        <div className="data-option" style={{ marginTop: '24px' }}>
          <h4>Data Retention</h4>
          <p>Automatically delete old conversations</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              { value: '30days', label: '30 days' },
              { value: '90days', label: '90 days' },
              { value: 'forever', label: 'Forever' }
            ].map(option => (
              <label
                key={option.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  cursor: 'pointer',
                  padding: '12px',
                  borderRadius: '8px',
                  background: retentionPolicy === option.value ? 'rgba(14, 165, 233, 0.2)' : 'transparent',
                  border: '1px solid rgba(14, 165, 233, 0.3)',
                  transition: 'all 0.2s'
                }}
                onClick={() => handleRetentionPolicyChange(option.value)}
              >
                <input
                  type="radio"
                  name="retention"
                  value={option.value}
                  checked={retentionPolicy === option.value}
                  onChange={() => { }}
                  style={{ cursor: 'pointer' }}
                />
                <span style={{ color: '#e2e8f0' }}>
                  Keep conversations for <strong>{option.label}</strong>
                </span>
              </label>
            ))}
          </div>
          <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '12px' }}>
            Older chats will be automatically deleted in the background.
          </p>
        </div>

        <div className="data-option" style={{ marginTop: '24px' }}>
          <h4>Chat History</h4>
          <p>Manage your conversation history</p>
          <div className="data-actions">
            <button
              className="settings-btn outline"
              onClick={handleViewAllChats}
              disabled={isLoadingChats}
            >
              {isLoadingChats ? 'Loading...' : 'View All Chats'}
            </button>
            <button className="settings-btn danger" onClick={handleDeleteAllChats}>
              Delete All Chats
            </button>
          </div>
        </div>

        <div className="data-option" style={{ marginTop: '24px' }}>
          <h4>Export Chat History</h4>
          <p>Download your conversations for backup or sharing</p>
          <div className="data-actions" style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button className="settings-btn outline" onClick={() => exportChats('json')}>
              Export as JSON
            </button>
            <button className="settings-btn outline" onClick={() => exportChats('markdown')}>
              Export as Markdown
            </button>
            <button className="settings-btn outline" onClick={() => exportChats('txt')}>
              Export as Plain Text
            </button>
          </div>
        </div>

        <div className="data-option" style={{ marginTop: '24px' }}>
          <h4>Import Chat History</h4>
          <p>Restore conversations from a previous export</p>
          <label className="settings-btn outline" style={{ cursor: 'pointer', display: 'inline-block' }}>
            Choose File to Import
            <input
              type="file"
              accept=".json"
              style={{ display: 'none' }}
              onChange={handleImport}
            />
          </label>
          <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '8px' }}>
            Only JSON exports are supported for import
          </p>
        </div>
      </div>

      {showDeleteConfirm && (
        <div className="settings-modal-overlay" style={{ zIndex: 10001 }} onClick={() => setShowDeleteConfirm(false)}>
          <div style={{
            background: '#1e293b',
            borderRadius: '16px',
            padding: '32px',
            maxWidth: '420px',
            width: '90%',
            boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
            textAlign: 'center'
          }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: '0 0 16px 0', color: '#ffffff', fontSize: '20px' }}>
              Delete All Chats?
            </h3>
            <p style={{ color: '#cbd5e1', margin: '0 0 32px 0', lineHeight: '1.6', fontSize: '15px' }}>
              This action <strong>cannot be undone</strong>.<br />
              All your conversations will be permanently deleted.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                style={{
                  padding: '12px 28px',
                  borderRadius: '8px',
                  border: '1px solid #475569',
                  background: 'transparent',
                  color: '#cbd5e1',
                  cursor: 'pointer',
                  fontWeight: '500'
                }}
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteAllChats}
                style={{
                  padding: '12px 28px',
                  borderRadius: '8px',
                  border: 'none',
                  background: '#ef4444',
                  color: '#ffffff',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                Delete All
              </button>
            </div>
          </div>
        </div>
      )}

      {showChatsModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000
          }}
          onClick={() => {
            setShowChatsModal(false);
            setChatSearchQuery('');
          }}
        >
          <div
            style={{
              background: '#1e293b',
              borderRadius: '16px',
              padding: '24px',
              maxWidth: '640px',
              width: '90%',
              maxHeight: '85vh',
              overflow: 'auto',
              display: 'flex',
              flexDirection: 'column'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, color: '#ffffff' }}>
                All Chats ({filteredChats.length})
              </h3>
              <button
                onClick={() => {
                  setShowChatsModal(false);
                  setChatSearchQuery('');
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  fontSize: '24px'
                }}
              >
                ×
              </button>
            </div>
            <input
              type="text"
              placeholder="Search chats by title..."
              value={chatSearchQuery}
              onChange={(e) => setChatSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px',
                borderRadius: '8px',
                border: '1px solid #475569',
                background: '#0f172a',
                color: '#e2e8f0',
                fontSize: '15px',
                marginBottom: '20px',
                outline: 'none'
              }}
              autoFocus
            />
            {filteredChats.length === 0 ? (
              <p style={{ color: '#94a3b8', textAlign: 'center', padding: '40px 20px' }}>
                {chatSearchQuery ? 'No chats match your search' : 'No chats found'}
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {filteredChats.map((chat) => (
                  <div
                    key={chat.id}
                    style={{
                      background: '#334155',
                      padding: '16px',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      transition: 'background 0.2s'
                    }}
                    onClick={() => {
                      setShowChatsModal(false);
                      setChatSearchQuery('');
                      navigate(`/${chat.id}`);
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = '#475569'}
                    onMouseLeave={(e) => e.currentTarget.style.background = '#334155'}
                  >
                    <div style={{ color: '#ffffff', fontWeight: '600', marginBottom: '4px' }}>
                      {chat.title || 'Untitled Chat'}
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                      {new Date(chat.created_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'account':
        return renderAccountContent();
      case 'appearance':
        return renderAppearanceContent();
      case 'behavior':
        return renderBehaviorContent();
      case 'customize':
        return renderCustomizeContent();
      case 'data':
        return renderDataContent();
      case 'api-keys':
        return renderApiKeysContent();
      case 'docs':
        return renderDocsContent();
      default:
        return renderAccountContent();
    }
  };

  return (
    <div className="settings-modal-overlay">
      <div className="settings-modal">
        <div className="settings-header">
          <h2>Settings</h2>
          <button className="close-btn" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        <div className="settings-body">
          <div className="settings-sidebar">
            {[
              { id: 'account', label: 'Account', icon: 'user' },
              { id: 'appearance', label: 'Appearance', icon: 'appearance' },
              { id: 'behavior', label: 'Behavior', icon: 'behavior' },
              { id: 'customize', label: 'Customize', icon: 'customize' },
              { id: 'data', label: 'Data Controls', icon: 'data' },
              { id: 'api-keys', label: 'API Keys', icon: 'key' },
              { id: 'docs', label: 'Documentation', icon: 'docs' }
            ].map((tab) => (
              <div
                key={tab.id}
                className={`sidebar-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <div className="tab-icon">
                  {tab.icon === 'user' && (
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                      <circle cx="12" cy="7" r="4" />
                    </svg>
                  )}
                  {tab.icon === 'appearance' && (
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                  )}
                  {tab.icon === 'behavior' && (
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                    </svg>
                  )}
                  {tab.icon === 'customize' && (
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
                    </svg>
                  )}
                  {tab.icon === 'data' && (
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M4 6h18V4H4c-1.1 0-2 .9-2 2v11H0v3h14v-3H4V6zm19 2h-6c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h6c.55 0 1-.45 1-1V9c0-.55-.45-1-1-1zm-1 9h-4v-7h4v7z" />
                    </svg>
                  )}
                  {tab.icon === 'key' && (
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M21 10h-8.59l3.3-3.29-1.41-1.42L10 10H2v2h8l4.29 4.29 1.41-1.41L12.41 12H21v-2z" />
                    </svg>
                  )}
                  {tab.icon === 'docs' && (
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>
                    </svg>
                  )}
                </div>
                <span className="tab-label">{tab.label}</span>
              </div>
            ))}
          </div>

          <div className="settings-content-wrapper">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;