import React, { useState, useContext, useEffect, useRef, useCallback, useMemo } from "react";
import "./AuthModal.css";
import { AuthContext } from "../../context/AuthContext";
import { useLoading } from "../../context/LoadingContext";

const AuthModal = ({ open, onClose }) => {
  const { login } = useContext(AuthContext);
  const { setLoading, loading } = useLoading();

  const [step, setStep] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [resetPassword, setResetPassword] = useState("");
  const [resetConfirmPassword, setResetConfirmPassword] = useState("");

  const [otpBoxes, setOtpBoxes] = useState(['', '', '', '', '', '']);
  const [canResend, setCanResend] = useState(true);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [showResetConfirmPassword, setShowResetConfirmPassword] = useState(false);
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [btnLoading, setBtnLoading] = useState(false);
  const [error, setError] = useState("");

  const inputRefs = useRef([]);

  const API = useMemo(() => {
    const viteApiUrl = import.meta.env?.VITE_API_URL;
    const craApiUrl = import.meta.env?.REACT_APP_API_URL;

    if (viteApiUrl) return viteApiUrl;
    if (craApiUrl) return craApiUrl;

    const isProduction = import.meta.env?.MODE === 'production' ||
      import.meta.env?.PROD === 'true';

    return isProduction
      ? 'https://your-production-api.com'
      : 'http://127.0.0.1:8000';
  }, []);

  useEffect(() => {
    if (!open) return;

    const urlParams = new URLSearchParams(window.location.search);
    const resetTokenParam = urlParams.get("token");

    if (resetTokenParam) {
      setResetToken(resetTokenParam);
      setStep("reset-password");
      setError("");
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;

    let dedicatedLoader = document.getElementById('auth-modal-loading-overlay');

    if (!dedicatedLoader) {
      dedicatedLoader = document.createElement('div');
      dedicatedLoader.id = 'auth-modal-loading-overlay';
      dedicatedLoader.style.position = 'fixed';
      dedicatedLoader.style.inset = '0';
      dedicatedLoader.style.background = 'rgba(0, 0, 0, 0.65)';
      dedicatedLoader.style.backdropFilter = 'blur(6px)';
      dedicatedLoader.style.display = 'none';
      dedicatedLoader.style.alignItems = 'center';
      dedicatedLoader.style.justifyContent = 'center';
      dedicatedLoader.style.zIndex = '30000';
      dedicatedLoader.style.pointerEvents = 'none';
      dedicatedLoader.style.transition = 'opacity 0.3s ease';
      dedicatedLoader.style.opacity = '0';

      const spinner = document.createElement('div');
      spinner.style.width = '60px';
      spinner.style.height = '60px';
      spinner.style.border = '6px solid rgba(255, 255, 255, 0.3)';
      spinner.style.borderTopColor = '#ffffff';
      spinner.style.borderRadius = '50%';
      spinner.style.animation = 'spin 1s linear infinite';

      dedicatedLoader.appendChild(spinner);
      document.body.appendChild(dedicatedLoader);

      if (!document.getElementById('auth-modal-spinner-style')) {
        const style = document.createElement('style');
        style.id = 'auth-modal-spinner-style';
        style.textContent = `
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `;
        document.head.appendChild(style);
      }
    }

    if (loading) {
      dedicatedLoader.style.display = 'flex';
      setTimeout(() => {
        dedicatedLoader.style.opacity = '1';
      }, 10);
    } else {
      dedicatedLoader.style.opacity = '0';
      setTimeout(() => {
        dedicatedLoader.style.display = 'none';
      }, 300);
    }

    return () => {
      dedicatedLoader.style.opacity = '0';
      setTimeout(() => {
        if (dedicatedLoader && dedicatedLoader.parentNode) {
        }
      }, 300);
    };
  }, [open, loading]);

  const handleGoogleSignIn = () => {
    console.log("Starting Google OAuth flow...");
    setBtnLoading(true);
    setLoading(true);

    try {
      const googleAuthUrl = `${API}/auth/google`;
      console.log("Redirecting to:", googleAuthUrl);
      window.location.href = googleAuthUrl;
    } catch (error) {
      console.error("Google SignIn error:", error);
      setError("Failed to start Google SignIn");
      setBtnLoading(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    let interval;
    if (resendCooldown > 0) {
      interval = setInterval(() => {
        setResendCooldown(prev => {
          if (prev <= 1) {
            clearInterval(interval);
            setCanResend(true);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [resendCooldown]);

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (pwd) => {
    if (pwd.length < 8) return "Password must be at least 8 characters";
    if (!/[A-Z]/.test(pwd)) return "One uppercase letter required";
    if (!/[a-z]/.test(pwd)) return "One lowercase letter required";
    if (!/[0-9]/.test(pwd)) return "One number required";
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) return "One special character required";
    return "";
  };

  const handleInputChange = useCallback((setter, value) => {
    setter(value);
    if (error) setError("");
  }, [error]);

  const handleOtpChange = useCallback((index, value) => {
    if (!/^\d*$/.test(value)) return;

    const newOtp = [...otpBoxes];
    newOtp[index] = value.slice(-1);

    setOtpBoxes(newOtp);
    const newCode = newOtp.join('');
    setCode(newCode);

    if (error && newCode.length === 6) setError('');

    if (value && index < 5) {
      setTimeout(() => inputRefs.current[index + 1]?.focus(), 10);
    }
  }, [otpBoxes, error]);

  const handleOtpKeyDown = useCallback((index, e) => {
    if (e.key === 'Backspace' && !otpBoxes[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    if (e.key === 'ArrowRight' && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
    if (e.key === 'Enter' && code.length === 6) {
      handleVerify();
    }
  }, [otpBoxes, code]);

  const handleOtpPaste = useCallback((e) => {
    e.preventDefault();
    const paste = e.clipboardData.getData('text').replace(/\D/g, '');
    if (paste.length <= 6) {
      const newOtp = paste.padEnd(6, '').slice(0, 6).split('');
      setOtpBoxes(newOtp);
      setCode(newOtp.join(''));
      if (error) setError('');

      const lastIndex = Math.min(paste.length - 1, 5);
      setTimeout(() => inputRefs.current[lastIndex]?.focus(), 10);
    }
  }, [error]);

  const apiCall = useCallback(async (url, options = {}) => {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
          "x-demo-key": "octopus-demo",
          ...options.headers,
        },
      });

      if (!response.ok) {
        let errorData = {};
        try {
          errorData = await response.json();
        } catch {}
        throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API call failed for ${url}:`, error);
      throw error;
    }
  }, []);

  const handleResendCode = async () => {
    if (resendCooldown > 0 || resendLoading) return;

    setResendLoading(true);
    setCanResend(false);
    setError('');

    try {
      await apiCall(`${API}/auth/resend`, {
        method: "POST",
        body: JSON.stringify({ email: email.trim() }),
      });

      alert("New verification code sent to your email!");
      setResendCooldown(60);
      setOtpBoxes(['', '', '', '', '', '']);
      setCode('');
      setTimeout(() => inputRefs.current[0]?.focus(), 100);
    } catch (err) {
      setError(err.message);
    } finally {
      setResendLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }

    if (!validateEmail(email)) {
      setError("Please enter a valid email address");
      return;
    }

    setBtnLoading(true);
    setLoading(true);
    setError("");

    try {
      const data = await apiCall(`${API}/auth/login`, {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });

      localStorage.setItem("authToken", data.token);

      const userData = await apiCall(`${API}/auth/me`, {
        headers: { "Authorization": `Bearer ${data.token}` },
        "x-demo-key": "octopus-demo",
      });

      await login({ ...userData, token: data.token });

      resetForm();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setBtnLoading(false);
      setLoading(false);
    }
  };

  const handleSignup = async () => {
    if (!name?.trim() || !email || !password || !confirmPassword) {
      setError("Please fill in all fields");
      return;
    }

    if (!validateEmail(email)) {
      setError("Please enter a valid email address");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    const pwdError = validatePassword(password);
    if (pwdError) {
      setError(pwdError);
      return;
    }

    if (!agreeTerms) {
      setError("You must agree to the Terms and Conditions");
      return;
    }

    setBtnLoading(true);
    setLoading(true);
    setError("");

    try {
      const data = await apiCall(`${API}/auth/signup`, {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          password
        }),
      });

      alert(data.message || "Verification code sent to your email!");
      setStep("verify");
      setOtpBoxes(['', '', '', '', '', '']);
      setCode('');
      setTimeout(() => inputRefs.current[0]?.focus(), 100);
    } catch (err) {
      setError(err.message);
    } finally {
      setBtnLoading(false);
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (code.length !== 6) {
      setError("Please enter a valid 6-digit code");
      return;
    }

    setBtnLoading(true);
    setLoading(true);
    setError("");

    try {
      const data = await apiCall(`${API}/auth/verify-code`, {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), code }),
      });

      localStorage.setItem("authToken", data.token);

      const userData = await apiCall(`${API}/auth/me`, {
        headers: { "Authorization": `Bearer ${data.token}` },
        "x-demo-key": "octopus-demo",
      });

      await login({ ...userData, token: data.token });

      resetForm();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setBtnLoading(false);
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (step === "reset-password") return;

    if (!email) {
      setError("Please enter your email address");
      return;
    }

    setBtnLoading(true);
    setLoading(true);
    setError("");

    try {
      const data = await apiCall(`${API}/auth/forgot-password`, {
        method: "POST",
        body: JSON.stringify({ email: email.trim() }),
      });

      alert(data.message || "Password reset link sent to your email!, If it exists!");
      setStep("login");
    } catch (err) {
      setError(err.message);
    } finally {
      setBtnLoading(false);
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!resetPassword || !resetConfirmPassword) {
      setError("Please fill in all fields");
      return;
    }

    if (resetPassword !== resetConfirmPassword) {
      setError("Passwords do not match");
      return;
    }

    const pwdError = validatePassword(resetPassword);
    if (pwdError) {
      setError(pwdError);
      return;
    }

    if (!resetToken) {
      setError("Invalid reset token");
      return;
    }

    setBtnLoading(true);
    setLoading(true);
    setError("");

    try {
      const data = await apiCall(`${API}/auth/reset-password`, {
        method: "POST",
        body: JSON.stringify({
          token: resetToken,
          password: resetPassword,
          confirm_password: resetConfirmPassword
        }),
      });

      alert(data.message || "Password reset successfully!");

      window.history.replaceState({}, document.title, window.location.pathname);
      setStep("login");
      resetForm();
    } catch (err) {
      setError(err.message);
    } finally {
      setBtnLoading(false);
      setLoading(false);
    }
  };

  const resetForm = useCallback(() => {
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setName("");
    setCode("");
    setOtpBoxes(['', '', '', '', '', '']);
    setResetPassword("");
    setResetConfirmPassword("");
    setResetToken("");
    setError("");
    setAgreeTerms(false);
    setShowPassword(false);
    setShowConfirmPassword(false);
    setShowResetPassword(false);
    setShowResetConfirmPassword(false);
    setResendCooldown(0);
    setCanResend(true);
    setResendLoading(false);
  }, []);

  const handleClose = () => {
    if (step === "reset-password") {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    resetForm();
    onClose();
  };

  useEffect(() => {
    if (!open) return;

    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };

    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [open]);

  if (!open) return null;

  return (
    <div className="auth-overlay">
      <div className="auth-card">
        <button
          className="close-btn"
          onClick={handleClose}
          aria-label="Close modal"
          disabled={btnLoading}
        >
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
          </svg>
        </button>

        {step === "login" && (
          <div className="auth-step">
            <div className="auth-header">
              <h2>Welcome Back</h2>
              <p className="subtitle">Sign in to continue your conversation</p>
            </div>

            <button
              className="social-btn google-btn"
              onClick={handleGoogleSignIn}
              disabled={btnLoading}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: "10px" }}>
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Continue with Google/ Ignore Temporary Issue              
            </button>        

            <div className="divider">
              <span>or</span>
            </div>

            <div className="form-group">
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => handleInputChange(setEmail, e.target.value)}
                disabled={btnLoading}
                autoComplete="email"
                className={error && !email ? "error" : ""}
              />
            </div>

            <div className="form-group">
              <div className="password-input-container">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Password"
                  value={password}
                  onChange={(e) => handleInputChange(setPassword, e.target.value)}
                  disabled={btnLoading}
                  autoComplete="current-password"
                  className="password-input"
                />
                <button
                  type="button"
                  className="eye-btn"
                  onClick={() => setShowPassword(prev => !prev)}
                  disabled={btnLoading}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-4 1.08L7.24 4.55C7.74 4.32 8.28 4.15 8.86 4.15 9.24 4.15 9.62 4.18 10 4.26L10 4.22c2.97 0 5.46.98 7.28 2.66l-3.57 2.77z" />
                      <path d="M2 4.27l2.28 2.28.45.45C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42V19.23l2.44 2.44 1.42-1.41L3.41 3.86l-1.41 1.41zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            <button
              className={`loading-btn ${btnLoading ? "loading" : ""}`}
              onClick={handleLogin}
              disabled={btnLoading || !email || !password}
            >
              {btnLoading ? (
                <>
                  <span className="spinner"></span>
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </button>

            <div className="link-container">
              <button
                className="link-btn"
                onClick={handleForgotPassword}
                disabled={btnLoading}
              >
                Forgot Password?
              </button>
            </div>

            <p className="switch-text">
              Don't have an account?{" "}
              <button
                className="link-text"
                onClick={() => {
                  setStep("signup");
                  setError("");
                }}
                disabled={btnLoading}
              >
                Create one
              </button>
            </p>
          </div>
        )}

        {step === "signup" && (
          <div className="auth-step">
            <div className="auth-header">
              <h2>Create Account</h2>
              <p className="subtitle">Join us today</p>
            </div>

            <div className="form-group">
              <input
                type="text"
                placeholder="Full Name"
                value={name}
                onChange={(e) => handleInputChange(setName, e.target.value)}
                disabled={btnLoading}
                autoComplete="name"
              />
            </div>

            <div className="form-group">
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => handleInputChange(setEmail, e.target.value)}
                disabled={btnLoading}
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <div className="password-input-container">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Password"
                  value={password}
                  onChange={(e) => handleInputChange(setPassword, e.target.value)}
                  disabled={btnLoading}
                  autoComplete="new-password"
                  className="password-input"
                />
                <button
                  type="button"
                  className="eye-btn"
                  onClick={() => setShowPassword(prev => !prev)}
                  disabled={btnLoading}
                >
                  {showPassword ? (
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-4 1.08L7.24 4.55C7.74 4.32 8.28 4.15 8.86 4.15 9.24 4.15 9.62 4.18 10 4.26L10 4.22c2.97 0 5.46.98 7.28 2.66l-3.57 2.77z" />
                      <path d="M2 4.27l2.28 2.28.45.45C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42V19.23l2.44 2.44 1.42-1.41L3.41 3.86l-1.41 1.41zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <div className="form-group">
              <div className="password-input-container">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="Confirm Password"
                  value={confirmPassword}
                  onChange={(e) => handleInputChange(setConfirmPassword, e.target.value)}
                  disabled={btnLoading}
                  autoComplete="new-password"
                  className="password-input"
                />
                <button
                  type="button"
                  className="eye-btn"
                  onClick={() => setShowConfirmPassword(prev => !prev)}
                  disabled={btnLoading}
                >
                  {showConfirmPassword ? (
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-4 1.08L7.24 4.55C7.74 4.32 8.28 4.15 8.86 4.15 9.24 4.15 9.62 4.18 10 4.26L10 4.22c2.97 0 5.46.98 7.28 2.66l-3.57 2.77z" />
                      <path d="M2 4.27l2.28 2.28.45.45C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42V19.23l2.44 2.44 1.42-1.41L3.41 3.86l-1.41 1.41zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <label className="terms-checkbox">
              <input
                type="checkbox"
                id="terms"
                checked={agreeTerms}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                disabled={btnLoading}
              />
              <span className="checkmark"></span>
              <span className="terms-text">
                I agree to the{" "}
                <a href="/terms" target="_blank" rel="noopener noreferrer" className="terms-link">
                  Terms of Service
                </a>{" "}
                and{" "}
                <a href="/privacy" target="_blank" rel="noopener noreferrer" className="terms-link">
                  Privacy Policy
                </a>
              </span>
            </label>

            {error && <div className="error-message">{error}</div>}

            <button
              className={`loading-btn ${btnLoading ? "loading" : ""}`}
              onClick={handleSignup}
              disabled={btnLoading || !name?.trim() || !email || !password || !confirmPassword || !agreeTerms}
            >
              {btnLoading ? (
                <>
                  <span className="spinner"></span>
                  Creating Account...
                </>
              ) : (
                "Create Account"
              )}
            </button>

            <p className="switch-text">
              Already have an account?{" "}
              <button
                className="link-text"
                onClick={() => {
                  setStep("login");
                  setError("");
                }}
                disabled={btnLoading}
              >
                Sign in
              </button>
            </p>
          </div>
        )}

        {step === "verify" && (
          <div className="auth-step">
            <div className="auth-header">
              <h2>Verify Your Email</h2>
              <p className="subtitle">Enter the 6-digit code sent to</p>
              <p className="verify-email">{email}</p>
            </div>

            <div className="form-group">
              <div
                className="otp-container"
                onPaste={handleOtpPaste}
              >
                <div className="otp-inputs">
                  {otpBoxes.map((digit, index) => (
                    <input
                      key={index}
                      ref={el => inputRefs.current[index] = el}
                      type="text"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpChange(index, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(index, e)}
                      onFocus={(e) => e.target.select()}
                      className={`otp-input ${digit ? 'filled' : ''
                        } ${error && code.length !== 6 ? 'error' : ''
                        }`}
                      disabled={btnLoading}
                      autoComplete="one-time-code"
                    />
                  ))}
                </div>
              </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            <button
              className={`loading-btn ${btnLoading ? "loading" : ""}`}
              onClick={handleVerify}
              disabled={btnLoading || code.length !== 6}
            >
              {btnLoading ? (
                <>
                  <span className="spinner"></span>
                  Verifying...
                </>
              ) : (
                "Verify Email"
              )}
            </button>

            <div className="resend-container">
              <p className="resend-text">
                Didn't receive the code?
              </p>
              <button
                className={`resend-btn ${resendCooldown > 0 || resendLoading ? 'disabled' : ''
                  }`}
                onClick={handleResendCode}
                disabled={resendCooldown > 0 || resendLoading}
              >
                {resendLoading ? (
                  <>
                    <span className="spinner small"></span>
                    Sending...
                  </>
                ) : resendCooldown > 0 ? (
                  `Resend (${resendCooldown}s)`
                ) : (
                  "Resend Code"
                )}
              </button>
            </div>

            <p className="switch-text">
              Back to{" "}
              <button
                className="link-text"
                onClick={() => {
                  setStep("signup");
                  setCode("");
                  setOtpBoxes(['', '', '', '', '', '']);
                  setError("");
                }}
                disabled={btnLoading}
              >
                Sign up
              </button>
            </p>
          </div>
        )}

        {step === "reset-password" && (
          <div className="auth-step">
            <div className="auth-header">
              <h2>Reset Your Password</h2>
              <p className="subtitle">Create a new password for your account</p>
            </div>

            <div className="form-group">
              <div className="password-input-container">
                <input
                  type={showResetPassword ? "text" : "password"}
                  placeholder="New Password"
                  value={resetPassword}
                  onChange={(e) => handleInputChange(setResetPassword, e.target.value)}
                  disabled={btnLoading}
                  autoComplete="new-password"
                  className="password-input"
                />
                <button
                  type="button"
                  className="eye-btn"
                  onClick={() => setShowResetPassword(prev => !prev)}
                  disabled={btnLoading}
                >
                  {showResetPassword ? (
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-4 1.08L7.24 4.55C7.74 4.32 8.28 4.15 8.86 4.15 9.24 4.15 9.62 4.18 10 4.26L10 4.22c2.97 0 5.46.98 7.28 2.66l-3.57 2.77z" />
                      <path d="M2 4.27l2.28 2.28.45.45C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42V19.23l2.44 2.44 1.42-1.41L3.41 3.86l-1.41 1.41zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <div className="form-group">
              <div className="password-input-container">
                <input
                  type={showResetConfirmPassword ? "text" : "password"}
                  placeholder="Confirm New Password"
                  value={resetConfirmPassword}
                  onChange={(e) => handleInputChange(setResetConfirmPassword, e.target.value)}
                  disabled={btnLoading}
                  autoComplete="new-password"
                  className="password-input"
                />
                <button
                  type="button"
                  className="eye-btn"
                  onClick={() => setShowResetConfirmPassword(prev => !prev)}
                  disabled={btnLoading}
                >
                  {showResetConfirmPassword ? (
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-4 1.08L7.24 4.55C7.74 4.32 8.28 4.15 8.86 4.15 9.24 4.15 9.62 4.18 10 4.26L10 4.22c2.97 0 5.46.98 7.28 2.66l-3.57 2.77z" />
                      <path d="M2 4.27l2.28 2.28.45.45C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42V19.23l2.44 2.44 1.42-1.41L3.41 3.86l-1.41 1.41zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            <button
              className={`loading-btn ${btnLoading ? "loading" : ""}`}
              onClick={handleResetPassword}
              disabled={btnLoading || !resetPassword || !resetConfirmPassword}
            >
              {btnLoading ? (
                <>
                  <span className="spinner"></span>
                  Resetting Password...
                </>
              ) : (
                "Reset Password"
              )}
            </button>

            <p className="switch-text">
              Back to{" "}
              <button
                className="link-text"
                onClick={() => {
                  window.history.replaceState({}, document.title, window.location.pathname);
                  setStep("login");
                  setError("");
                }}
                disabled={btnLoading}
              >
                Sign in
              </button>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthModal;