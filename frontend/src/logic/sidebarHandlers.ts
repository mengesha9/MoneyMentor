import { SidebarHandlersProps } from '../types';
import { createNewSession } from '../utils/sessions';

// Handle session selection
export const handleSessionSelect = async (
  sessionId: string,
  props: SidebarHandlersProps
) => {
  const { sidebarState, setSidebarState, onSessionSelect } = props;
  
  try {
    // Update sidebar state with selected session
    setSidebarState({
      ...sidebarState,
      selectedSessionId: sessionId,
    });
    
    // Call the session select callback
    await onSessionSelect(sessionId);
    
    // On mobile, close sidebar after selection
    if (window.innerWidth <= 768) {
      setSidebarState({
        ...sidebarState,
        selectedSessionId: sessionId,
        isOpen: false,
      });
    }
  } catch (error) {
    console.error('Failed to select session:', error);
  }
};

// Handle new chat creation
export const handleNewChat = async (props: SidebarHandlersProps) => {
  const { sidebarState, setSidebarState, onNewChat } = props;
  
  try {
    // Create new session
    const newSession = createNewSession();
    
    // Update sidebar state
    setSidebarState({
      ...sidebarState,
      selectedSessionId: newSession.id,
    });
    
    // Call the new chat callback
    await onNewChat();
    
    // On mobile, close sidebar after creation
    if (window.innerWidth <= 768) {
      setSidebarState({
        ...sidebarState,
        selectedSessionId: newSession.id,
        isOpen: false,
      });
    }
  } catch (error) {
    console.error('Failed to create new chat:', error);
  }
};

// Handle sidebar toggle
export const handleSidebarToggle = (props: SidebarHandlersProps) => {
  const { sidebarState, setSidebarState } = props;
  
  setSidebarState({
    ...sidebarState,
    isOpen: !sidebarState.isOpen,
  });
};

// Handle sidebar collapse/expand
export const handleSidebarCollapse = (props: SidebarHandlersProps) => {
  const { sidebarState, setSidebarState } = props;
  
  setSidebarState({
    ...sidebarState,
    isCollapsed: !sidebarState.isCollapsed,
  });
};

// Handle sidebar close on mobile
export const handleMobileSidebarClose = (props: SidebarHandlersProps) => {
  const { sidebarState, setSidebarState } = props;
  
  if (window.innerWidth <= 768) {
    setSidebarState({
      ...sidebarState,
      isOpen: false,
    });
  }
};

// Handle outside click to close sidebar on mobile
export const handleOutsideClick = (
  event: MouseEvent,
  sidebarRef: React.RefObject<HTMLDivElement>,
  props: SidebarHandlersProps
) => {
  if (window.innerWidth <= 768) {
    if (sidebarRef.current && !sidebarRef.current.contains(event.target as Node)) {
      handleMobileSidebarClose(props);
    }
  }
};

// Handle escape key to close sidebar
export const handleEscapeKey = (
  event: KeyboardEvent,
  props: SidebarHandlersProps
) => {
  if (event.key === 'Escape') {
    const { sidebarState, setSidebarState } = props;
    setSidebarState({
      ...sidebarState,
      isOpen: false,
    });
  }
};

// Handle session deletion (if needed in the future)
export const handleSessionDelete = async (
  sessionId: string,
  props: SidebarHandlersProps
) => {
  const { sidebarState, setSidebarState } = props;
  
  try {
    // If deleting the currently selected session, clear selection
    if (sidebarState.selectedSessionId === sessionId) {
      setSidebarState({
        ...sidebarState,
        selectedSessionId: null,
      });
    }
    
    // Here you would typically call an API to delete the session
  
  } catch (error) {
    console.error('Failed to delete session:', error);
  }
}; 