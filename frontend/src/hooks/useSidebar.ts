import { useState, useCallback, useEffect } from 'react';
import { SidebarState } from '../types';

const SIDEBAR_STORAGE_KEY = 'moneymentor_sidebar_state';

export const useSidebar = () => {
  const [sidebarState, setSidebarState] = useState<SidebarState>(() => {
    const saved = localStorage.getItem(SIDEBAR_STORAGE_KEY);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // Fall back to default if parsing fails
      }
    }
    return {
      isOpen: true,
      isCollapsed: false,
      selectedSessionId: null,
    };
  });

  // Save to localStorage whenever state changes
  useEffect(() => {
    localStorage.setItem(SIDEBAR_STORAGE_KEY, JSON.stringify(sidebarState));
  }, [sidebarState]);

  const toggleSidebar = useCallback(() => {
    setSidebarState(prev => ({
      ...prev,
      isOpen: !prev.isOpen,
    }));
  }, []);

  const collapseSidebar = useCallback(() => {
    setSidebarState(prev => ({
      ...prev,
      isCollapsed: true,
    }));
  }, []);

  const expandSidebar = useCallback(() => {
    setSidebarState(prev => ({
      ...prev,
      isCollapsed: false,
    }));
  }, []);

  const closeSidebar = useCallback(() => {
    setSidebarState(prev => ({
      ...prev,
      isOpen: false,
    }));
  }, []);

  const openSidebar = useCallback(() => {
    setSidebarState(prev => ({
      ...prev,
      isOpen: true,
    }));
  }, []);

  const selectSession = useCallback((sessionId: string | null) => {
    setSidebarState(prev => ({
      ...prev,
      selectedSessionId: sessionId,
    }));
  }, []);

  return {
    sidebarState,
    setSidebarState,
    toggleSidebar,
    collapseSidebar,
    expandSidebar,
    closeSidebar,
    openSidebar,
    selectSession,
  };
}; 