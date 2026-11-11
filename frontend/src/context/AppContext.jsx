// The only state shared across pages: who is logged in. Every page loads its own data
// from the Flask API, so nothing here can drift away from the database.
import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { flaskApi } from '../services/api';
import { publicUser, registrationPayload, unauthenticatedMessage } from '../utils/auth';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authMessage, setAuthMessage] = useState('');
  const authVersion = useRef(0);
  const authBusy = useRef(false);
  const identity = useRef(null);

  function clearUser() {
    identity.current = null;
    setUser(null);
  }

  useEffect(() => {
    let active = true;
    async function restoreSession() {
      if (authBusy.current) return;
      const version = ++authVersion.current;
      try {
        const response = await flaskApi.getCurrentUser();
        if (active && version === authVersion.current) {
          const restored = publicUser(response.data.user);
          identity.current = restored.id;
          setUser(restored);
          setAuthMessage('');
        }
      } catch (error) {
        if (!active || version !== authVersion.current) return;
        if (error.status === 401) {
          const wasAuthenticated = identity.current !== null;
          clearUser();
          setAuthMessage(current => unauthenticatedMessage(wasAuthenticated, current));
        } else {
          setAuthMessage(error.message);
        }
      } finally {
        if (active && version === authVersion.current) setAuthLoading(false);
      }
    }
    restoreSession();
    // Recheck when returning to the tab, so expired or suspended sessions are cleared.
    window.addEventListener('focus', restoreSession);
    return () => { active = false; window.removeEventListener('focus', restoreSession); };
  }, []);

  async function login(email, password) {
    ++authVersion.current;
    authBusy.current = true;
    try {
      const response = await flaskApi.login({ email, password });
      const account = publicUser(response.data.user);
      identity.current = account.id;
      setAuthMessage('');
      setUser(account);
      return account;
    } finally {
      authBusy.current = false;
    }
  }

  async function registerCustomer(data) {
    const response = await flaskApi.registerCustomer(registrationPayload(data));
    setAuthMessage('Account created. Please log in with your email and password.');
    return response.data.user;
  }

  async function logout() {
    ++authVersion.current;
    authBusy.current = true;
    try {
      await flaskApi.logout();
      clearUser();
      setAuthMessage('You have been logged out.');
    } finally {
      authBusy.current = false;
    }
  }

  const clearAuthMessage = () => setAuthMessage('');

  const value = useMemo(() => ({ user, authLoading, authMessage, login, registerCustomer, logout, clearAuthMessage }),
    [user, authLoading, authMessage]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const value = useContext(AppContext);
  if (!value) throw new Error('useApp must be used inside AppProvider');
  return value;
}
