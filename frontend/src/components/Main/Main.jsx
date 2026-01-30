import React, { useState, useContext, useRef, useEffect } from "react";
import "./Main.css";
import { assets } from "../../assets/assets";
import { apiAxios } from "@/lib/api";
import {
  ChevronDown, ArrowDown, Mic, Upload, Copy,
  ThumbsUp, ThumbsDown, Square, RotateCcw, Edit, Send, X, Check,
  FileText, Image as ImageIcon, File, Code, FileSpreadsheet
} from "lucide-react";
import AuthModal from "../AuthModal/AuthModal";
import { AuthContext } from "../../context/AuthContext";
import { useAppearance } from '../../context/AppearanceContext';
import { useLoading } from "../../context/LoadingContext";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeRaw from "rehype-raw";
import "katex/dist/katex.min.css";
import { useNavigate } from 'react-router-dom';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import responseStyleService from '../ResponseStyleService';
import { useParams } from "react-router-dom";

// Use environment variable for all API calls
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"; // fallback for local dev

const Main = ({
  onNewChat = () => { },
  currentChat = null,
  setCurrentChat = () => { },
  messages: messagesProp,
  setMessages: setMessagesProp
}) => {

  const { user: contextUser } = useContext(AuthContext);
  const { setLoading } = useLoading();
  const navigate = useNavigate();

  const { fontSize, lineSpacing, autoScrollEnabled } = useAppearance();

  const [localMessages, setLocalMessages] = useState([]);

  const [viewRegistered, setViewRegistered] = useState(false);

  const messages = messagesProp ?? localMessages;
  const setMessages = setMessagesProp ?? setLocalMessages;

  const { token } = useParams();
  const isShared = Boolean(token);

  const [user, setUser] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const MESSAGE_LIMIT = 10;

  const [selected, setSelected] = useState({
    id: "Nexora-1.1",
    label: "Nexora 1.1",
    desc: "Fast & basic daily tasks",
  });

  const [abortController, setAbortController] = useState(null);
  const [lastUserMessage, setLastUserMessage] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [lastFile, setLastFile] = useState(null);
  const [enableWebSearch, setEnableWebSearch] = useState(true);
  const [forceWebSearch, setForceWebSearch] = useState(false);
  const [ragCollectionId, setRagCollectionId] = useState(null);
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [viewerId] = useState(() => {
    return `viewer-${Math.random().toString(36).slice(2, 10)}`;
  });
  const [liveViewers, setLiveViewers] = useState(0);

  const [guestCount, setGuestCount] = useState(() => {
    const stored = localStorage.getItem("guestCount");
    return stored ? parseInt(stored) : 0;
  });

  const [guestId] = useState(() => {
    const stored = localStorage.getItem("guestId");
    if (stored) return stored;
    const id = `guest-${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem("guestId", id);
    return id;
  });

  const [isListening, setIsListening] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(null);
  const [editingIndex, setEditingIndex] = useState(null);
  const [editedText, setEditedText] = useState("");
  const [feedbackStates, setFeedbackStates] = useState(() => {
    const stored = localStorage.getItem("feedbackStates");
    return stored ? JSON.parse(stored) : {};
  });

  const [copiedIndex, setCopiedIndex] = useState(null);
  const [messagesLoaded, setMessagesLoaded] = useState(false);

  const chatEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const recognitionRef = useRef(null);
  const inputRef = useRef(null);
  const editTextareaRef = useRef(null);

  const chatStarted = Array.isArray(messages) && messages.length > 0;

  const adjustTextareaHeight = () => {
    const textarea = inputRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  };

  useEffect(() => {
    if (!isShared || !token || viewRegistered) return;

    fetch(`${API_BASE_URL}/shared/${token}`)
      .then(() => setViewRegistered(true))
      .catch(() => { });
  }, [isShared, token, viewRegistered]);

  useEffect(() => {
    if (!isShared || !token) return;

    const loadSharedChat = async () => {
      try {
        const fullUrl = `${API_BASE_URL}/shared/${token}`;

        const res = await fetch(fullUrl, {
          method: "GET",
          cache: "no-store",
          credentials: "omit",
          headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        });

        const responseText = await res.text();

        if (!res.ok) {
          throw new Error(`Server responded with ${res.status}: ${responseText.substring(0, 120)}...`);
        }

        if (!res.headers.get("content-type")?.includes("application/json")) {
          throw new Error("Response is not JSON (possibly HTML/index.html)");
        }

        let data;
        try {
          data = JSON.parse(responseText);
        } catch (parseErr) {
          throw new Error("Invalid JSON from server");
        }

        const transformed = [];

        (data.messages || []).forEach((m) => {
          if (m.user_message) {
            transformed.push({
              from: "user",
              text: m.user_message,
              isComplete: true,
              timestamp: new Date(m.created_at).getTime(),
            });
          }
          if (m.bot_reply) {
            transformed.push({
              from: "bot",
              text: m.bot_reply,
              isComplete: true,
              timestamp: new Date(m.created_at).getTime(),
            });
          }
        });

        setMessages(transformed);

      } catch (err) {
        console.error("Failed to load shared chat:", err);
      }
    };

    loadSharedChat();

    const interval = setInterval(loadSharedChat, 12000);

    return () => clearInterval(interval);
  }, [isShared, token, setMessages]);

  useEffect(() => {
    if (!isShared || !token) return;

    const interval = setInterval(() => {
      fetch(`${API_BASE_URL}/shared/${token}/heartbeat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ viewer_id: viewerId }),
      }).catch(() => { });
    }, 10000);

    return () => clearInterval(interval);
  }, [isShared, token, viewerId]);

  useEffect(() => {
    if (!isShared || !token) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/shared/${token}/viewers`);
        if (!res.ok) return;
        const data = await res.json();
        setLiveViewers(data.live_viewers || 0);
      } catch { }
    }, 3000);

    return () => clearInterval(interval);
  }, [isShared, token]);

  const isReadOnly = isShared && !contextUser;

  useEffect(() => {
    adjustTextareaHeight();
  }, [message]);

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    const iconMap = {
      jpg: <ImageIcon size={20} className="file-type-icon image" />,
      jpeg: <ImageIcon size={20} className="file-type-icon image" />,
      png: <ImageIcon size={20} className="file-type-icon image" />,
      gif: <ImageIcon size={20} className="file-type-icon image" />,
      webp: <ImageIcon size={20} className="file-type-icon image" />,
      pdf: <FileText size={20} className="file-type-icon pdf" />,
      doc: <FileText size={20} className="file-type-icon doc" />,
      docx: <FileText size={20} className="file-type-icon doc" />,
      txt: <FileText size={20} className="file-type-icon txt" />,
      py: <Code size={20} className="file-type-icon code" />,
      js: <Code size={20} className="file-type-icon code" />,
      jsx: <Code size={20} className="file-type-icon code" />,
      ts: <Code size={20} className="file-type-icon code" />,
      tsx: <Code size={20} className="file-type-icon code" />,
      html: <Code size={20} className="file-type-icon code" />,
      css: <Code size={20} className="file-type-icon code" />,
      java: <Code size={20} className="file-type-icon code" />,
      cpp: <Code size={20} className="file-type-icon code" />,
      c: <Code size={20} className="file-type-icon code" />,
      xlsx: <FileSpreadsheet size={20} className="file-type-icon sheet" />,
      xls: <FileSpreadsheet size={20} className="file-type-icon sheet" />,
      csv: <FileSpreadsheet size={20} className="file-type-icon sheet" />,
    };
    return iconMap[ext] || <File size={20} className="file-type-icon default" />;
  };

  const detectCode = (text) => {
    const codePatterns = [
      /```[\s\S]*```/,
      /`[^`]+`/,
      /function\s+\w+\s*\(/,
      /const\s+\w+\s*=/,
      /let\s+\w+\s*=/,
      /var\s+\w+\s*=/,
      /import\s+.*from/,
      /export\s+(default|const|function)/,
      /class\s+\w+/,
      /<\/?[a-z][\s\S]*>/i,
      /\{[\s\S]*\}/,
      /\[[\s\S]*\]/,
    ];
    return codePatterns.some(pattern => pattern.test(text));
  };

  const CodeBlock = ({ language, value, inline }) => {
    const [copied, setCopied] = useState(false);
    const handleCopyCode = () => {
      navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };
    if (inline) {
      return <code className="inline-code">{value}</code>;
    }
    return (
      <div className="code-block-wrapper">
        <div className="code-header">
          <span className="code-language">{language || 'text'}</span>
          <button
            className={`code-copy-btn ${copied ? 'copied' : ''}`}
            onClick={handleCopyCode}
          >
            {copied ? (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
                Copied!
              </>
            ) : (
              <>
                <Copy size={14} />
                Copy code
              </>
            )}
          </button>
        </div>
        <div className="code-content">
          <SyntaxHighlighter
            language={language || 'text'}
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              padding: 0,
              background: 'transparent',
            }}
          >
            {value}
          </SyntaxHighlighter>
        </div>
      </div>
    );
  };

  const TableComponent = ({ children }) => {
    const [copied, setCopied] = useState(false);
    const tableRef = useRef(null);
    const handleCopyTable = () => {
      if (tableRef.current) {
        const text = tableRef.current.innerText;
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    };
    return (
      <div className="table-wrapper">
        <div className="table-header">
          <span className="table-label">Table</span>
          <button
            className={`table-copy-btn ${copied ? 'copied' : ''}`}
            onClick={handleCopyTable}
          >
            {copied ? (
              <>
                <Check size={14} />
                Copied!
              </>
            ) : (
              <>
                <Copy size={14} />
                Copy table
              </>
            )}
          </button>
        </div>
        <div className="table-container" ref={tableRef}>
          <table>{children}</table>
        </div>
      </div>
    );
  };

  const preprocessMath = (text) => {
    if (!text) return text;

    if (text.includes('\\(') || text.includes('\\[')) {
      return text;
    }

    let processed = text;

    processed = processed.replace(/\[([^\[\]]+)\]/g, (match, content) => {
      const mathPattern = /^[\s]*[\d\w]*[\s]*[=+\-*/^_\\]|\\(frac|sum|int|pi|mu|nu|lambda|sigma|omega|alpha|beta|gamma|delta|theta|phi|psi|sqrt|lim|infty)/;
      if (mathPattern.test(content)) {
        return `\\(${content.trim()}\\)`;
      }
      return match;
    });

    return processed;
  };

  const scrollToBottom = (behavior = "smooth") => {
    chatEndRef.current?.scrollIntoView({ behavior });
  };

  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
    setShowScrollButton(!isAtBottom);
    setShouldAutoScroll(isAtBottom);
  };

  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    setLoading(true);
    setTimeout(() => setLoading(false), 800);
  }, []);

  useEffect(() => {
    setUser(contextUser);
    const storedModel = localStorage.getItem("model");
    if (storedModel) {
      try {
        setSelected(JSON.parse(storedModel));
      } catch (e) { }
    }
    if (contextUser) {
      setShowAuth(false);
      setGuestCount(0);
      localStorage.setItem("guestCount", "0");
      const currentStoredChat = localStorage.getItem("currentChat");
      if (currentStoredChat) {
        try {
          const chat = JSON.parse(currentStoredChat);
          const chatId = typeof chat === "string" ? chat : chat.id;
          if (chatId && chatId.startsWith("guest-")) {
            localStorage.removeItem("currentChat");
            localStorage.removeItem(`messages-${chatId}`);
            setMessages([]);
            setCurrentChat(null);
          }
        } catch (e) {
          localStorage.removeItem("currentChat");
        }
      }
    } else {
      const storedChat = localStorage.getItem("currentChat");
      if (storedChat) {
        try {
          const chat = JSON.parse(storedChat);
          const chatObj = typeof chat === "string" ? { id: chat } : chat;
          setCurrentChat(chatObj);
        } catch (e) {
          console.error("Failed to parse currentChat", e);
          localStorage.removeItem("currentChat");
        }
      }
    }
  }, [contextUser]);

  useEffect(() => {
    const chatId = currentChat?.id || currentChat?.chat_id || currentChat;
    if (!chatId) {
      setMessagesLoaded(true);
      return;
    }

    const storedMessages = localStorage.getItem(`messages-${chatId}`);
    if (storedMessages) {
      try {
        let parsed = JSON.parse(storedMessages);
        parsed = parsed.map(msg =>
          msg.from === "bot"
            ? { ...msg, text: msg.text || "", isComplete: true }
            : msg
        );
        setMessages(parsed);
      } catch (e) {
        console.error("Failed to parse stored messages", e);
        setMessages([]);
      }
    }
    setMessagesLoaded(true);
  }, [currentChat, isShared]);

  useEffect(() => {
    if (!messagesLoaded || messages.length === 0) return;
    const chatId = currentChat?.id || currentChat?.chat_id || currentChat || guestId;
    if (chatId) {
      const timeoutId = setTimeout(() => {
        localStorage.setItem(`messages-${chatId}`, JSON.stringify(messages));
      }, 500);
      return () => clearTimeout(timeoutId);
    }
  }, [messages, currentChat, guestId, messagesLoaded]);

  useEffect(() => {
    localStorage.setItem("model", JSON.stringify(selected));
  }, [selected]);

  useEffect(() => {
    localStorage.setItem("guestCount", String(guestCount));
  }, [guestCount]);

  useEffect(() => {
    localStorage.setItem("feedbackStates", JSON.stringify(feedbackStates));
  }, [feedbackStates]);

  useEffect(() => {
    if (messages.length > 0 && shouldAutoScroll) {
      scrollToBottom("smooth");
    }
  }, [messages]);

  useEffect(() => {
    const container = chatContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [chatStarted]);

  useEffect(() => {
    if (editingIndex !== null && editTextareaRef.current) {
      editTextareaRef.current.focus();
      editTextareaRef.current.setSelectionRange(
        editTextareaRef.current.value.length,
        editTextareaRef.current.value.length
      );
    }
  }, [editingIndex]);

  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setMessage(transcript);
      setIsListening(false);
    };
    recognition.onerror = () => {
      setIsListening(false);
    };
    recognition.onend = () => {
      setIsListening(false);
    };
    recognitionRef.current = recognition;
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const generateChatTitle = async (chatId, messageHistory) => {
    if (messageHistory.length < 3) return;
    try {
      const messagesToSend = messageHistory.slice(0, 10).map(m => m.text).filter(Boolean);
      const res = await apiAxios.post('/chat/generate-title',
        { messages: messagesToSend },
        { headers: contextUser?.token ? { Authorization: `Bearer ${contextUser.token}` } : {} }
      );
      if (res.data.title) {
        const updatedChat = {
          id: chatId,
          title: res.data.title
        };
        setCurrentChat(updatedChat);
        localStorage.setItem("currentChat", JSON.stringify(updatedChat));
        onNewChat(updatedChat);
      }
    } catch (err) {
      console.error("Failed to generate title:", err);
    }
  };

  useEffect(() => {
    const effectiveChatId = currentChat?.id || currentChat?.chat_id || currentChat || guestId;
    if (messages.length > 0 && effectiveChatId) {
      const expectedPath = `/chat/${effectiveChatId}`;
      if (window.location.pathname !== expectedPath) {
        navigate(expectedPath, { replace: true });
      }
    } else if (messages.length === 0 && window.location.pathname !== '/') {
      navigate('/', { replace: true });
    }
  }, [currentChat, messages.length, navigate, guestId]);

  const toggleVoice = () => {
    if (!recognitionRef.current) return;
    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      alert("File too large. Maximum size is 10MB.");
      e.target.value = null;
      return;
    }
    setSelectedFile(file);
    e.target.value = null;
  };

  const handleRagUpload = async () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append("files", selectedFile);
    try {
      const res = await apiAxios.post("/files/upload-rag", formData);
      setRagCollectionId(res.data.collection_id);
      alert(`Documents ready! Collection ID: ${res.data.collection_id}\nNow ask questions about them.`);
      setSelectedFile(null);
    } catch (err) {
      alert("RAG upload failed: " + (err.response?.data?.detail || err.message));
    }
  };

  const sendMessage = async (overrideText) => {
    const currentMessage = overrideText ?? message.trim();
    if (!currentMessage && !selectedFile) return;
    if (currentMessage.length > 4096) {
      alert("Message too long. Maximum 4096 characters.");
      return;
    }

    setLastUserMessage(currentMessage);
    setLastFile(selectedFile);
    setShouldAutoScroll(true);

    const baseUserMessage = {
      from: "user",
      text: currentMessage,
      file: selectedFile ? {
        name: selectedFile.name,
        size: selectedFile.size,
        type: selectedFile.type
      } : null,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, baseUserMessage]);

    if (!overrideText) {
      setMessage("");
      if (inputRef.current) {
        inputRef.current.style.height = 'auto';
      }
    }

    if (selectedFile) {
      setUploadingFile(selectedFile.name);
      const formData = new FormData();
      formData.append("file", selectedFile);
      if (currentMessage) formData.append("query", currentMessage);
      if (currentChat?.id) {
        formData.append("chat_id", currentChat.id);
      }
      setIsGenerating(true);
      setMessages(prev => [...prev, { from: "bot", text: "Analyzing file...", isComplete: false, timestamp: Date.now() }]);
      try {
        const res = await apiAxios.post("/files/upload", formData, {
          headers: { Authorization: contextUser?.token ? `Bearer ${contextUser.token}` : "" },
          timeout: 180000
        });
        setUploadingFile(null);
        const aiResponse = res.data.message || res.data.answer || "File processed successfully!";
        if (res.data.file_id || res.data.chat_id) {
          setMessages(prev => {
            const updated = [...prev];
            const lastMsg = updated[updated.length - 2];
            if (lastMsg.from === "user" && lastMsg.file) {
              updated[updated.length - 2] = {
                ...lastMsg,
                file: {
                  ...lastMsg.file,
                  file_id: res.data.file_id,
                  chat_id: res.data.chat_id || currentChat?.id
                }
              };
            }
            updated[updated.length - 1] = { from: "bot", text: aiResponse, isComplete: true, timestamp: Date.now() };
            return updated;
          });
        }
        if (!currentChat && res.data.chat_id) {
          const preview = currentMessage.substring(0, 30) + (currentMessage.length > 30 ? "..." : "") || selectedFile.name;
          const newChatData = { id: res.data.chat_id, title: preview };
          setCurrentChat(newChatData);
          localStorage.setItem("currentChat", JSON.stringify(newChatData));
          navigate(`/chat/${res.data.chat_id}`, { replace: true });
          setTimeout(() => onNewChat?.(newChatData), 50);
        }
        setIsGenerating(false);
        if (contextUser && (res.data.chat_id || currentChat?.id) && messages.length === 0) {
          setTimeout(() => {
            generateChatTitle(res.data.chat_id || currentChat.id, [
              { from: 'user', text: currentMessage || selectedFile.name },
              { from: 'bot', text: aiResponse }
            ]);
          }, 1000);
        }
        if (!contextUser) setGuestCount(prev => prev + 1);
        setSelectedFile(null);
      } catch (err) {
        setIsGenerating(false);
        setUploadingFile(null);
        const errorMessage = err.response?.data?.detail || err.message || "Upload failed";
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { from: "bot", text: `Error: ${errorMessage}\n\nPlease try again.`, isComplete: true, timestamp: Date.now() };
          return updated;
        });
      }
    } else {
      setIsGenerating(true);
      const controller = new AbortController();
      setAbortController(controller);

      const timeoutId = setTimeout(() => {
        if (!controller.signal.aborted) {
          console.log("Request timeout - aborting");
          controller.abort();
        }
      }, 300000);

      try {
        const payload = {
          message: currentMessage,
          chat_id: currentChat?.id || currentChat?.chat_id || currentChat,
          collection_id: ragCollectionId,
          conversation_history: messages.slice(-6).map(m => m.text).filter(Boolean),
          enable_web_search: !ragCollectionId,
          response_style: responseStyleService.getCurrentStyle()
        };

        const response = await fetch(`${API_BASE_URL}/send`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-demo-key': 'octopus-demo',
            ...(contextUser?.token && { 'Authorization': `Bearer ${contextUser.token}` })
          },
          body: JSON.stringify(payload),
          signal: controller.signal,
          keepalive: true
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errText = await response.text();
          throw new Error(`Streaming failed: ${response.status} ${errText}`);
        }

        if (!response.body) {
          throw new Error('Response body is null');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        setMessages(prev => [...prev, { 
          from: "bot", 
          text: "", 
          isComplete: false, 
          timestamp: Date.now() 
        }]);

        let accumulatedText = '';
        let receivedChatId = null;
        let lastUpdateTime = Date.now();

        while (true) {
          if (controller.signal.aborted) {
            console.log('Stream aborted by user');
            break;
          }

          let readResult;
          try {
            readResult = await reader.read();
          } catch (readError) {
            console.error('Stream read error:', readError);
            break;
          }

          const { done, value } = readResult;
          
          if (done) {
            console.log('Stream complete');
            break;
          }

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;

            try {
              const data = JSON.parse(line.substring(6));

              if (data.type === 'metadata') {
                if (data.chat_id) {
                  receivedChatId = data.chat_id;
                  if (!currentChat) {
                    const preview = currentMessage.substring(0, 30) + 
                      (currentMessage.length > 30 ? "..." : "");
                    const newChatData = { 
                      id: receivedChatId, 
                      title: preview || "New Chat" 
                    };
                    setCurrentChat(newChatData);
                    localStorage.setItem("currentChat", JSON.stringify(newChatData));
                    navigate(`/chat/${receivedChatId}`, { replace: true });
                    setTimeout(() => onNewChat?.(newChatData), 50);
                  }
                }
              }

              if (data.type === 'token' && data.content) {
                accumulatedText += data.content;
                lastUpdateTime = Date.now();

                setMessages(prev => {
                  const updated = [...prev];
                  const lastIndex = updated.length - 1;
                  if (updated[lastIndex]?.from === 'bot') {
                    updated[lastIndex] = {
                      ...updated[lastIndex],
                      text: accumulatedText,
                      isComplete: false
                    };
                  }
                  return updated;
                });

                if (shouldAutoScroll) {
                  scrollToBottom("auto");
                }
              }

              if (data.type === 'done') {
                setMessages(prev => {
                  const updated = [...prev];
                  const lastIndex = updated.length - 1;
                  if (updated[lastIndex]?.from === 'bot') {
                    updated[lastIndex] = {
                      ...updated[lastIndex],
                      text: accumulatedText,
                      isComplete: true
                    };
                  }
                  return updated;
                });

                setIsGenerating(false);
                setAbortController(null);

                if (contextUser && receivedChatId && messages.length <= 2) {
                  setTimeout(() => {
                    generateChatTitle(receivedChatId, [
                      ...messages, 
                      { from: 'bot', text: accumulatedText }
                    ]);
                  }, 1000);
                }

                break;
              }

              if (data.type === 'error') {
                throw new Error(data.content || 'Generation error');
              }

            } catch (parseError) {
              console.error('JSON parse error:', parseError, 'Line:', line);
              continue;
            }
          }

          if (Date.now() - lastUpdateTime > 60000) {
            console.warn('No updates for 60s - assuming stall');
            break;
          }
        }

        clearTimeout(timeoutId);
        reader.releaseLock();

        if (!contextUser) setGuestCount(prev => prev + 1);

      } catch (err) {
        clearTimeout(timeoutId);
        setAbortController(null);

        if (err.name === 'AbortError') {
          console.log('Generation stopped by user');
          setIsGenerating(false);
          return;
        }

        setIsGenerating(false);
        
        const errorText = err.message || "Error occurred. Please try again.";
        
        setMessages(prev => {
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          
          if (updated[lastIndex]?.from === 'bot') {
            updated[lastIndex] = {
              ...updated[lastIndex],
              text: `Error: ${errorText}\n\nPlease try again.`,
              isComplete: true,
              showActions: true
            };
          } else {
            updated.push({
              from: "bot",
              text: `Error: ${errorText}`,
              isComplete: true,
              timestamp: Date.now()
            });
          }
          
          return updated;
        });
      }
    }
  };

  const stopGeneration = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
    }
    setIsGenerating(false);
    setMessages(prev => {
      const updated = [...prev];
      const lastIndex = updated.length - 1;
      if (updated[lastIndex] && updated[lastIndex].from === 'bot') {
        updated[lastIndex] = {
          from: "bot",
          text: "Generation stopped by user. Please try again.",
          isComplete: true,
          timestamp: Date.now(),
          showActions: true
        };
      }
      return updated;
    });
  };

  const retryLastMessage = () => {
    if (!lastUserMessage) return;
    if (lastFile) {
      setSelectedFile(lastFile);
    }
    sendMessage(lastUserMessage);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getMessageKey = (index) => {
    const chatId = currentChat?.id || currentChat?.chat_id || currentChat || guestId;
    return `${chatId}-${index}`;
  };

  const handleCopy = (text, index) => {
    navigator.clipboard.writeText(text);
    const key = getMessageKey(index);
    setCopiedIndex(key);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleFeedback = async (index, rating) => {
    const key = getMessageKey(index);
    setFeedbackStates(prev => ({
      ...prev,
      [key]: rating > 0 ? "up" : "down"
    }));

    if (!contextUser?.token) return;

    const message = messages[index];
    if (!message?.id) return;

    try {
      await apiAxios.post("/feedback/submit-answer", {
        message_id: message.id,
        rating: rating,
        comment: ""
      }, {
        headers: { Authorization: `Bearer ${contextUser.token}` }
      });
      console.log("Message feedback saved");
    } catch (err) {
      console.error("Feedback error:", err);
    }
  };

  const startEditing = (index, text) => {
    setEditingIndex(index);
    setEditedText(text);
  };

  const cancelEdit = () => {
    setEditingIndex(null);
    setEditedText("");
  };

  const saveEdit = async () => {
    if (!editedText.trim() || editingIndex === null) {
      cancelEdit();
      return;
    }
    const updatedMessages = [...messages];
    updatedMessages[editingIndex] = {
      ...updatedMessages[editingIndex],
      text: editedText.trim()
    };
    const messagesToKeep = updatedMessages.slice(0, editingIndex + 1);
    setMessages(messagesToKeep);
    setEditingIndex(null);
    setEditedText("");
    await sendMessage(editedText.trim());
  };

  const handleEditKeyDown = (e) => {
    if (e.key === "Enter" && e.ctrlKey) {
      e.preventDefault();
      saveEdit();
    } else if (e.key === "Escape") {
      cancelEdit();
    }
  };

  const hasCode = detectCode(message);

  return (
    <div className="main">
      <div className="nav">
        <img className="logo" src={assets.octopus_logo} alt="logo" />
        <div className="nav-center">
          {contextUser && (
            <div className="model-selector">
              <button className="model-btn" onClick={() => setOpen(!open)}>
                {selected.label}
                <ChevronDown size={18} />
              </button>
              {open && (
                <div className="dropdown">
                  <div className="dropdown-item" onClick={() => setOpen(false)}>
                    <p className="model-title">{selected.label}</p>
                    <p className="model-desc">{selected.desc}</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        {!contextUser && (
          <button className="navbar-login-btn" onClick={() => {
            setLoading(true);
            setTimeout(() => {
              setShowAuth(true);
              setLoading(false);
            }, 200);
          }}>
            Login / SignUp
          </button>
        )}
      </div>
      <div className="main-container">
        <AuthModal open={showAuth} onClose={() => setShowAuth(false)} />

        {isShared && (
          <div className="shared-viewer-bar">
            👁️ {liveViewers} live viewer{liveViewers !== 1 ? "s" : ""}
          </div>
        )}

        {chatStarted ? (
          <div className="chat-wrapper">
            {isShared && (
              <div style={{
                background: '#e0f2fe',
                padding: '12px',
                marginBottom: '16px',
                borderRadius: '8px',
                textAlign: 'center',
                fontSize: '14px',
                color: '#1e40af'
              }}>
                This is a shared conversation • Read-only mode • {liveViewers} live viewer{liveViewers !== 1 ? 's' : ''}
              </div>
            )}
            <div className={`chat-container font-${fontSize} spacing-${lineSpacing}`} ref={chatContainerRef}>
              {messages.map((m, i) => (
                <div key={`${m.timestamp}-${i}`} className={`chat-message ${m.from}`}>
                  {m.from === "bot" ? (
                    <>
                      <div className="message-content">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[
                            [rehypeKatex, {
                              throwOnError: false,
                              strict: false,
                              trust: true,
                              output: 'html'
                            }],
                            rehypeRaw
                          ]}
                          components={{
                            code({ node, inline, className, children, ...props }) {
                              const match = /language-(\w+)/.exec(className || '');
                              const codeString = String(children).replace(/\n$/, '');

                              if (!inline && !match) {
                                const trimmed = codeString.trim();

                                if (
                                  trimmed.startsWith('$$') ||
                                  trimmed.endsWith('$$') ||
                                  /^\\[\[\(]/.test(trimmed) ||
                                  (/\\(frac|sum|int|sqrt|begin|end)/.test(trimmed) && !trimmed.includes('import') && !trimmed.includes('function'))
                                ) {
                                  return <div className="math-display">{children}</div>;
                                }
                              }

                              if (!inline && match) {
                                return (
                                  <CodeBlock
                                    language={match[1]}
                                    value={codeString}
                                    inline={false}
                                  />
                                );
                              }
                              return <code className="inline-code" {...props}>{children}</code>;
                            },
                            table({ children }) {
                              return <TableComponent>{children}</TableComponent>;
                            }
                          }}
                        >
                          {preprocessMath(m.text)}
                        </ReactMarkdown>
                        {m.searchUsed && (
                          <div className="search-badge">
                            Powered by {m.searchSource}
                          </div>
                        )}
                      </div>
                      {(m.isComplete || m.showActions) && m.text && (
                        <div className="bot-actions">
                          <button className="action-icon" onClick={() => handleCopy(m.text, i)} title="Copy">
                            {copiedIndex === getMessageKey(i) ? (
                              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="3">
                                <path d="M20 6L9 17l-5-5" />
                              </svg>
                            ) : (
                              <Copy size={18} />
                            )}
                          </button>
                          <button className={`action-icon thumbs-btn ${feedbackStates[getMessageKey(i)] === "up" ? "active" : ""}`} onClick={() => handleFeedback(i, 1)} title="Helpful">
                            <ThumbsUp size={18} />
                          </button>
                          <button className={`action-icon thumbs-btn ${feedbackStates[getMessageKey(i)] === "down" ? "active" : ""}`} onClick={() => handleFeedback(i, -1)} title="Not helpful">
                            <ThumbsDown size={18} />
                          </button>
                          <button className="action-icon" onClick={retryLastMessage} title="Regenerate">
                            <RotateCcw size={18} />
                          </button>
                        </div>
                      )}
                    </>
                  ) : (
                    <>
                      {editingIndex === i ? (
                        <div className="edit-message-container">
                          <textarea ref={editTextareaRef} className="edit-textarea" value={editedText} onChange={(e) => setEditedText(e.target.value)} onKeyDown={handleEditKeyDown} rows={3} />
                          <div className="edit-actions">
                            <button className="edit-btn save" onClick={saveEdit} title="Save & Resend (Ctrl+Enter)">
                              <Check size={16} /> Save & Resend
                            </button>
                            <button className="edit-btn cancel" onClick={cancelEdit} title="Cancel (Esc)">
                              <X size={16} /> Cancel
                            </button>
                          </div>
                          <div className="edit-hint">Press Ctrl+Enter to save, Esc to cancel</div>
                        </div>
                      ) : (
                        <>
                          {m.file ? (
                            <div className="user-message-with-file" style={{ display: 'flex', flexDirection: 'column' }}>
                              <div className="file-attachment">
                                {getFileIcon(m.file.name)}
                                <div className="file-info">
                                  <span className="file-name">{m.file.name}</span>
                                  <span className="file-size">{(m.file.size / 1024).toFixed(1)} KB</span>
                                </div>
                              </div>
                              {m.text && <div className="file-query">{m.text}</div>}
                            </div>
                          ) : (
                            <div className="user-text">{m.text}</div>
                          )}

                          {!isReadOnly && !m.file && (
                            <Edit size={18} className="action-icon user-edit" onClick={() => startEditing(i, m.text)} title="Edit message" />
                          )}
                        </>
                      )}
                    </>
                  )}
                </div>
              ))}
              {isGenerating && !uploadingFile && messages.length > 0 && messages[messages.length - 1].from === 'bot' && !messages[messages.length - 1].isComplete && (
                <div className="chat-message bot typing-indicator">
                  <div className="typing-indicator">
                    <div className="octopus-tentacles">
                      <div className="tentacle"></div>
                      <div className="tentacle"></div>
                      <div className="tentacle"></div>
                      <div className="tentacle"></div>
                      <div className="tentacle"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </div>
        ) : (
          <div className="greet">
            {contextUser ? (
              <>
                <p><span>Hello, {contextUser.name.split(" ")[0]}.</span></p>
                <p style={{ fontSize: '34px' }}>I'm <strong style={{ fontSize: '34px' }}>Nexora 1.1</strong> — your AI with memory.</p>
                <p style={{ fontSize: '20px', opacity: 0.8 }}>Now with semantic caching for instant answers.</p>
              </>
            ) : (
              <>
                <p><span>Hello! I'm Nexora 1.1</span></p>
                <p style={{ fontSize: '34px' }}>Your personal AI that learns and remembers.</p>
                <p style={{ fontSize: '20px', opacity: 0.7 }}>Free to try • No login needed (10 messages)</p>
              </>
            )}
          </div>
        )}

        {chatStarted && showScrollButton && (
          <button className="scroll-to-bottom-btn" onClick={() => {
            scrollToBottom("smooth");
            setShouldAutoScroll(true);
          }}>
            <ArrowDown size={20} />
          </button>
        )}

        {!isReadOnly && (
          <div className="main-bottom">
            <div className={`search-box ${hasCode ? 'has-code' : ''}`}>
              {selectedFile && (
                <div className="file-preview-container" style={{ marginBottom: '12px' }}>
                  <div
                    className="file-attachment preview"
                    style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}
                  >
                    {getFileIcon(selectedFile.name)}
                    <div className="file-info">
                      <span className="file-name">{selectedFile.name}</span>
                      <span className="file-size">
                        {(selectedFile.size / 1024).toFixed(1)} KB
                      </span>
                    </div>
                    <button
                      className="remove-file"
                      onClick={() => setSelectedFile(null)}
                    >
                      <X size={16} />
                    </button>
                  </div>
                </div>
              )}

              <textarea
                ref={inputRef}
                rows={1}
                placeholder={
                  isShared
                    ? "This is a shared conversation — read only"
                    : (!contextUser && guestCount >= MESSAGE_LIMIT)
                      ? "Message limit reached — login to continue"
                      : "Ask anything or upload a file..."
                }
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                readOnly={isShared}
                disabled={isShared || (!contextUser && guestCount >= MESSAGE_LIMIT)}
                className={`message-textarea ${hasCode ? 'has-code-content' : ''}`}
              />

              <div className="action-icons">
                <label htmlFor="file-upload" className="icon-btn" title="Upload file">
                  <Upload size={20} />
                </label>

                <input
                  id="file-upload"
                  type="file"
                  style={{ display: 'none' }}
                  onChange={handleFileSelect}
                  accept=".pdf,.doc,.docx,.txt,.md,.jpg,.jpeg,.png,.py,.js,.jsx,.ts,.tsx,.html,.css,.json"
                  disabled={!contextUser && guestCount >= MESSAGE_LIMIT}
                />

                {!message.trim() && !isGenerating && (
                  <button
                    className={`icon-btn ${isListening ? 'listening' : ''}`}
                    onClick={toggleVoice}
                    title="Voice input"
                  >
                    <Mic size={20} />
                    {isListening && <span className="pulse-ring"></span>}
                  </button>
                )}

                {isGenerating && (
                  <button
                    className="icon-btn stop-generating"
                    onClick={stopGeneration}
                    title="Stop generation"
                  >
                    <Square size={20} />
                  </button>
                )}

                {(message.trim() || selectedFile) &&
                  !isGenerating &&
                  !(!contextUser && guestCount >= MESSAGE_LIMIT) && (
                    <button
                      className="icon-btn send-btn"
                      onClick={sendMessage}
                      title="Send message"
                    >
                      <Send size={20} />
                    </button>
                  )}
              </div>
            </div>

            <div className="bottom-info">
              <p style={{ opacity: 0.7, fontSize: '13px', margin: '0 0 8px 0' }}>
                Nexora 1.1 can make mistakes. Check important info.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Main;