import React, { createContext, useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isValidating, setIsValidating] = useState(true);


  // Validate session on mount and after page reload
  useEffect(() => {
    validateSession();
  }, []);

  // ✅ GOOGLE OAUTH TOKEN HANDLER - NEW!
  useEffect(() => {
    handleGoogleOAuthRedirect();
  }, []);

  const handleGoogleOAuthRedirect = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const userEmail = urlParams.get('user');
    const provider = urlParams.get('provider');
    const error = urlParams.get('error');

    // ✅ GOOGLE OAUTH SUCCESS
    if (token && userEmail && provider === 'google') {

      try {        
        
        const initialUserData = {
          email: userEmail,
          provider: 'google',
          token: token
        };

        // 3. Use existing login function (it will fetch complete user data)
        await login(initialUserData);

        // 4. Clean URL (remove query params)
        window.history.replaceState({}, document.title, window.location.pathname);

        // 5. Success message
        setTimeout(() => {
          alert(`Welcome, ${userEmail}! Google Sign-In successful!`);
        }, 500);

      } catch (err) {
        alert('Google Sign-In failed. Please try again.');
      }
    }

    // ✅ GOOGLE OAUTH ERROR
    if (error) {
      alert(`Google Sign-In failed: ${decodeURIComponent(error)}`);

      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  };

  const validateSession = async () => {
    setIsValidating(true);

    const stored = localStorage.getItem("user");
    if (!stored) {
      setIsValidating(false);
      return;
    }

    try {
      const userData = JSON.parse(stored);

      if (!userData.token) {
        clearSession();
        setIsValidating(false);
        return;
      }

      const response = await apiFetch("/auth/me", {
        headers: {
          Authorization: `Bearer ${userData.token}`,
        },
      });

      if (!response.ok) {
        clearSession();
        setIsValidating(false);
        return;
      }

      const freshUserData = await response.json();
      const fullUser = { ...freshUserData, token: userData.token };

      setUser(fullUser);
      localStorage.setItem("user", JSON.stringify(fullUser));
    } catch (err) {
      clearSession();
    } finally {
      setIsValidating(false);
    }
  };


  const clearSession = () => {
    // Clear user data
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    setUser(null);

    // Clear current chat
    localStorage.removeItem("currentChat");

    // Clear all chat messages
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith("messages-")) {
        localStorage.removeItem(key);
      }
    });

    // Clear recent chats
    localStorage.removeItem("recentChats");
  };

  // Fetch user info using token
  const fetchUser = async (token) => {
    try {
      const response = await apiFetch("/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch user");

      const data = await response.json();
      return data;
    } catch (err) {
      clearSession();
      return null;
    }
  };


  // ✅ ENHANCED LOGIN - WORKS PERFECTLY WITH GOOGLE OAUTH
  const login = async (userData) => {

    if (userData.token) {
      const freshUserData = await fetchUser(userData.token);
      if (freshUserData) {
        const fullUser = { ...freshUserData, token: userData.token };
        setUser(fullUser);
        localStorage.setItem("user", JSON.stringify(fullUser));

        // Clear guest data on login
        localStorage.removeItem("guestId");
        localStorage.setItem("guestCount", "0");

        return fullUser;
      }
    } else {
      const fullUser = { ...userData };
      setUser(fullUser);
      localStorage.setItem("user", JSON.stringify(fullUser));
      return fullUser;
    }

    throw new Error("Login failed");
  };

  const logout = () => {
    clearSession();

    // Reset guest count on logout
    localStorage.setItem("guestCount", "0");
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isValidating, validateSession }}>
      {children}
    </AuthContext.Provider>
  );
};