// src/components/GoogleCallback/GoogleCallback.jsx
import React, { useEffect, useContext } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { AuthContext } from '../../context/AuthContext';
import { useLoading } from '../../context/LoadingContext';
import { apiFetch } from "@/lib/api";





const GoogleCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);
  const { setLoading } = useLoading();

  useEffect(() => {
    const handleGoogleCallback = async () => {
      const token = searchParams.get('token');
      const userEmail = searchParams.get('user');
      const error = searchParams.get('error');
      const provider = searchParams.get('provider');

      console.log('🔍 Google Callback Params:', { token: token ? 'YES' : 'NO', userEmail, error, provider });

      if (error) {
        alert(`Google login failed: ${error}`);
        setLoading(false);
        navigate('/'); // or your main route
        return;
      }

      if (token && userEmail) {
        try {
          setLoading(true);

          // ✅ Verify token with backend
          const response = await apiFetch("/auth/me", {
            headers: { Authorization: `Bearer ${token}` },
          });


          if (response.ok) {
            const userData = await response.json();
            await login({ ...userData, token });

            // ✅ Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);

            alert(`🎉 Welcome back, ${userData.name}!`);
            navigate('/chat'); // Your main app route
          } else {
            throw new Error('Token verification failed');
          }
        } catch (err) {
          console.error('Google login error:', err);
          alert('Google login failed. Please try again.');
          navigate('/');
        }
      } else {
        alert('Invalid Google login response');
        navigate('/');
      }

      setLoading(false);
    };

    handleGoogleCallback();
  }, [searchParams, navigate, login, setLoading]);

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white'
    }}>
      <div style={{
        textAlign: 'center',
        padding: '2rem',
        background: 'rgba(255,255,255,0.1)',
        borderRadius: '20px',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{
          width: '60px',
          height: '60px',
          border: '4px solid rgba(255,255,255,0.3)',
          borderTop: '4px solid #fff',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 20px'
        }}></div>
        <h2>Completing Google Login...</h2>
        <p>Please wait while we set up your account</p>
      </div>
    </div>
  );
};

export default GoogleCallback;