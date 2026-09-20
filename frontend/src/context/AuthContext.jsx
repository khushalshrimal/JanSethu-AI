import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('jansethu_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('jansethu_token') || null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('jansethu_token');
      if (storedToken) {
        try {
          const userData = await authService.getMe();
          setUser(userData);
          localStorage.setItem('jansethu_user', JSON.stringify(userData));
        } catch (err) {
          console.error("Session verification failed:", err);
          logout();
        }
      }
      setLoading(false);
    };
    initializeAuth();
  }, []);

  const login = async (phone_number, password) => {
    setAuthError(null);
    try {
      const data = await authService.login(phone_number, password);
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('jansethu_token', data.access_token);
      localStorage.setItem('jansethu_user', JSON.stringify(data.user));
      return data.user;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Login failed';
      setAuthError(msg);
      throw new Error(msg);
    }
  };

  const register = async (customerData) => {
    setAuthError(null);
    try {
      const newUser = await authService.register(customerData);
      return newUser;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Registration failed';
      setAuthError(msg);
      throw new Error(msg);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('jansethu_token');
    localStorage.removeItem('jansethu_user');
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      isAuthenticated: !!token && !!user,
      loading,
      authError,
      login,
      register,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
