const API_BASE = import.meta.env.VITE_API_BASE || 
                 (import.meta.env.DEV 
                   ? "http://localhost:8000" 
                   : window.location.origin);

const DEMO_SECRET = import.meta.env.VITE_DEMO_SECRET || "octopus-demo";

console.log("[API] Base URL:", API_BASE);
console.log("[API] Environment:", import.meta.env.DEV ? "Development" : "Production");

/**
 * Get auth header with token
 */
function authHeader() {
  const token = localStorage.getItem("token"); // ← Make sure you save token with key "token"
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Get demo protection header
 */
function demoHeader() {
  return { "x-demo-key": DEMO_SECRET };
}

/**
 * Combine all headers
 */
function allHeaders(extraHeaders = {}) {
  return {
    "Content-Type": "application/json",
    ...demoHeader(),
    ...authHeader(),
    ...extraHeaders,
  };
}

/**
 * POST request with JSON body
 */
export async function postJSON(path, body) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: allHeaders(),
      body: JSON.stringify(body),
      credentials: "include",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ 
        detail: `Request failed with status ${res.status}` 
      }));
      
      if (res.status === 401) {
        console.warn("[API] Unauthorized - clearing token");
        localStorage.removeItem("token");
        window.location.href = "/"; // or wherever your login is
      }
      
      throw new Error(err.detail || JSON.stringify(err));
    }
    
    return res.json();
  } catch (error) {
    console.error("[API] POST error:", path, error);
    throw error;
  }
}

/**
 * GET request - Now sends token correctly
 */
export async function getJSON(path) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "GET",
      headers: allHeaders(), // ← This now includes Authorization Bearer token
      credentials: "include",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ 
        detail: `Request failed with status ${res.status}` 
      }));
      
      if (res.status === 401) {
        console.warn("[API] Unauthorized - clearing token");
        localStorage.removeItem("token");
        window.location.href = "/";
      }
      
      throw new Error(err.detail || "Request failed");
    }
    
    return res.json();
  } catch (error) {
    console.error("[API] GET error:", path, error);
    throw error;
  }
}

/**
 * POST with FormData
 */
export async function postFormData(path, formData) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        ...demoHeader(),
        ...authHeader(),
      },
      body: formData,
      credentials: "include",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ 
        detail: `Upload failed with status ${res.status}` 
      }));
      throw new Error(err.detail || JSON.stringify(err));
    }
    
    return res.json();
  } catch (error) {
    console.error("[API] FormData error:", path, error);
    throw error;
  }
}

/**
 * DELETE request
 */
export async function deleteJSON(path) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "DELETE",
      headers: allHeaders(),
      credentials: "include",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ 
        detail: `Delete failed with status ${res.status}` 
      }));
      throw new Error(err.detail || "Delete failed");
    }
    
    return res.json();
  } catch (error) {
    console.error("[API] DELETE error:", path, error);
    throw error;
  }
}

export const API_CONFIG = {
  BASE_URL: API_BASE,
  DEMO_SECRET: DEMO_SECRET,
};