import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api/authApi';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('oil_user_data');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('oil_auth_token'));
  const [isLoading, setIsLoading] = useState(true);

  const role = user?.role || null;
  const isAuthenticated = !!token && !!user;

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('oil_auth_token');
      if (storedToken) {
        try {
          const response = await authApi.getMe();
          if (response?.data) {
            setUser(response.data);
            localStorage.setItem('oil_user_data', JSON.stringify(response.data));
          }
        } catch (err) {
          localStorage.removeItem('oil_auth_token');
          localStorage.removeItem('oil_user_data');
          setUser(null);
          setToken(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    const response = await authApi.login(email, password);
    if (response?.success && response?.data) {
      const { access_token, user: userData } = response.data;
      localStorage.setItem('oil_auth_token', access_token);
      localStorage.setItem('oil_user_data', JSON.stringify(userData));
      setToken(access_token);
      setUser(userData);
      return response;
    }
    throw new Error(response?.message || 'Login failed');
  };

  const signup = async (userData) => {
    const response = await authApi.signup(userData);
    return response;
  };

  const logout = async () => {
    await authApi.logout();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        token,
        isAuthenticated,
        isLoading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
