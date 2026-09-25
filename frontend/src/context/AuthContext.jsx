import { createContext, useContext, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { login as loginRequest } from "../services/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("current_user");
    return raw ? JSON.parse(raw) : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user) {
      localStorage.setItem("current_user", JSON.stringify(user));
    } else {
      localStorage.removeItem("current_user");
    }
  }, [user]);

  async function login(email, password) {
    setLoading(true);
    setError(null);
    try {
      const data = await loginRequest(email, password);
      // Server data is per-user; never let a previous session's cache leak into this one.
      queryClient.clear();
      localStorage.setItem("access_token", data.access_token);
      setUser(data.user);
      return data.user;
    } catch (err) {
      setError(err.response?.data?.error || "Login failed.");
      throw err;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("access_token");
    queryClient.clear();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, error }}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
