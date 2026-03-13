import { useState, useEffect, createContext, useContext, type ReactNode } from 'react';
import { auth } from '../services/api';
import type { LoginResponse } from '../types';

interface AuthContextType {
  user: LoginResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<LoginResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    const role = localStorage.getItem('role');
    const expiresIn = localStorage.getItem('expires_in');

    if (token && username && role) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setUser({
        token,
        username,
        role,
        expires_in: parseInt(expiresIn || '0', 10),
      });
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    const response = await auth.login({ username, password });
    const data = response.data;

    localStorage.setItem('token', data.token);
    localStorage.setItem('username', data.username);
    localStorage.setItem('role', data.role);
    localStorage.setItem('expires_in', data.expires_in.toString());

    setUser(data);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    localStorage.removeItem('expires_in');
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
