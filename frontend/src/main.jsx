// frontend/src/main.jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from './context/AuthContext' 
import { AppearanceProvider } from './context/AppearanceContext';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>   
      <AppearanceProvider>
        <App />
      </AppearanceProvider>
    </AuthProvider>
  </StrictMode>,
)
