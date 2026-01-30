// frontend/src/components/Sidebar/ShareChatModal.jsx
import React, { useState, useEffect } from "react";
import "./ShareChatModal.css";
import { assets } from "../../assets/assets";

const ShareChatModal = ({ open, onClose, chatId, chatTitle, user }) => {
  const [shareUrl, setShareUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [expiryDays, setExpiryDays] = useState(null);
  const [shareToken, setShareToken] = useState("");
  const [totalViews, setTotalViews] = useState(0);

  useEffect(() => {
    if (!open || !shareToken) return;

    fetch(`${import.meta.env.VITE_API_URL}/shared/${shareToken}`)
      .then(res => res.json())
      .then(data => setTotalViews(data.view_count || 0))
      .catch(() => { });
  }, [open, shareToken]);

  useEffect(() => {
    if (open && chatId) {
      generateShareLink();
    }
  }, [open, chatId]);

  const generateShareLink = async () => {
    setLoading(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      console.log('Generating share link for chat:', chatId);
      console.log('API URL:', apiUrl);

      const response = await fetch(`${apiUrl}/${chatId}/share`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${user?.token}`,
        },
        body: JSON.stringify({
          expires_in_days: expiryDays,
        }),
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("Error response:", errorData);
        throw new Error(errorData.detail || "Failed to generate share link");
      }

      const data = await response.json();
      console.log('Share link generated:', data);
      setShareUrl(data.share_url);
      setShareToken(data.share_token);
    } catch (error) {
      console.error("Error generating share link:", error);
      alert(`Failed to generate share link: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const revokeLink = async () => {
    if (!confirm("Are you sure you want to revoke this share link?")) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/${chatId}/share`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${user?.token}`,
        },
      });

      if (!response.ok) throw new Error("Failed to revoke link");

      alert("Share link revoked successfully");
      onClose();
    } catch (error) {
      console.error("Error revoking link:", error);
      alert("Failed to revoke link");
    }
  };

  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="share-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Share Chat</h2>
          <img
            src={assets.close_icon}
            alt="close"
            className="close-btn"
            onClick={onClose}
          />
        </div>

        <div className="modal-body">
          <div className="chat-info">
            <img src={assets.message_icon} alt="chat" />
            <p className="chat-title">{chatTitle || "Untitled Chat"}</p>
          </div>

          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Generating share link...</p>
            </div>
          ) : shareUrl ? (
            <>
              <div className="share-link-container">
                <input
                  type="text"
                  value={shareUrl}
                  readOnly
                  className="share-link-input"
                />
                <button
                  className={`copy-btn ${copied ? "copied" : ""}`}
                  onClick={copyToClipboard}
                >
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>

              <div className="share-options">
                <label>
                  <input
                    type="checkbox"
                    checked={expiryDays !== null}
                    onChange={(e) => setExpiryDays(e.target.checked ? 7 : null)}
                  />
                  <span>Link expires in 7 days</span>
                </label>
              </div>

              <div className="share-info">
                <p>🔗 Anyone with this link can view this conversation</p>
                <p>👁️ Total views: {totalViews}</p>
              </div>

              <div className="modal-actions">
                <button className="revoke-btn" onClick={revokeLink}>
                  Revoke Link
                </button>
                <button className="done-btn" onClick={onClose}>
                  Done
                </button>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default ShareChatModal;