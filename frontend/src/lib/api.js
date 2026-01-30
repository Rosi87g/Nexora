// frontend/src/lib/api.js
import axios from "axios";

export const API_BASE =
  import.meta.env.VITE_API_URL || "https://does-appointed-standards-sen.trycloudflare.com";

export const apiFetch = (path, options = {}) => {
  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",      
      ...(options.headers || {}),
    },
  });
};

export const apiAxios = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

// ✅ Add x-demo-key to every request
apiAxios.interceptors.request.use((config) => {
  config.headers["x-demo-key"] = "octopus-demo";

  // ✅ Automatically add Authorization Bearer token if exists
  const token = localStorage.getItem("authToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default apiAxios;