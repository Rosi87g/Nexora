import React, { useState, useEffect } from "react";
import "./Feedback.css";
import { apiFetch } from "@/lib/api";


const Feedback = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [rating, setRating] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Nuclear scroll fix (your strict index.css safe)
  useEffect(() => {
    const origHtmlOverflow = document.documentElement.style.overflow;
    const origHtmlHeight = document.documentElement.style.height;
    const origBodyOverflow = document.body.style.overflow;
    const origBodyHeight = document.body.style.height;
    const origRootOverflow = document.getElementById('root')?.style.overflow;
    const origRootHeight = document.getElementById('root')?.style.height;

    document.documentElement.style.overflow = 'visible';
    document.documentElement.style.height = 'auto';
    document.body.style.overflow = 'visible';
    document.body.style.height = 'auto';
    if (document.getElementById('root')) {
      document.getElementById('root').style.overflow = 'visible';
      document.getElementById('root').style.height = 'auto';
    }

    return () => {
      document.documentElement.style.overflow = origHtmlOverflow;
      document.documentElement.style.height = origHtmlHeight;
      document.body.style.overflow = origBodyOverflow;
      document.body.style.height = origBodyHeight;
      if (document.getElementById('root')) {
        document.getElementById('root').style.overflow = origRootOverflow || '';
        document.getElementById('root').style.height = origRootHeight || '';
      }
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    if (rating === 0) {
      setError("Please give a star rating!");
      setLoading(false);
      return;
    }

    try {
      const res = await apiFetch("/feedback/submit", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          rating,
          message: message.trim(),
        }),
      });

      if (!res.ok) throw new Error("Failed to send feedback");

      setSubmitted(true);

      // Auto-redirect back to main app after 3 seconds
      setTimeout(() => {
        // If opened via window.open(), close tab
        if (window.opener) {
          window.close();
        } else {
          // Otherwise redirect to home
          window.location.href = "/";  // or your main route, e.g. "/chat"
        }
      }, 3000);

    } catch (err) {
      setError("Failed to send feedback. Try again later.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const stars = [1, 2, 3, 4, 5];

  if (submitted) {
    return (
      <div className="feedback-page">
        <div className="success-card">
          <h2>🎉 Thanks bro!</h2>
          <p>Your feedback was sent successfully.</p>
          <p>We're reading every word — this helps us make Nexora legendary 🐙</p>
          <p><small>Redirecting you back in 3 seconds...</small></p>
        </div>
      </div>
    );
  }

  return (
    <div className="feedback-page">
      <div className="feedback-card">
        <h1>🐙 Nexora Feedback</h1>
        <p className="subtitle">Your honest opinion = our fuel. Go all in.</p>

        {error && <p className="error-msg">{error}</p>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>
              Name <span className="required">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              required
            />
          </div>

          <div className="form-group">
            <label>
              Email <span className="required">*</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="So we can thank you personally"
              required
            />
          </div>

          <div className="form-group">
            <label>
              Rate Nexora <span className="required">*</span>
            </label>
            <div className="stars">
              {stars.map((star) => (
                <span
                  key={star}
                  className={`star ${rating >= star ? "filled" : ""}`}
                  onClick={() => setRating(star)}
                >
                  ★
                </span>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>
              Your Feedback <span className="required">*</span>
            </label>
            <textarea
              rows="8"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Be raw. What’s fire? What’s trash? Bugs? Missing features? AI too slow? Chat history broken? New ideas? Lay it all out — we read EVERYTHING."
              required
            />
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? "Sending..." : "Send Feedback"}
          </button>
        </form>

        <p className="footer-note">
          Real talk builds real products. Thanks for being part of it. 💙
        </p>
      </div>
    </div>
  );
};

export default Feedback;