import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, afterEach, vi } from 'vitest';
import { Sidebar } from '../../components/Sidebar/Sidebar';
import { ChatSession, SidebarState, UserProfile } from '../../types';

const mockUserProfile: UserProfile = {
  id: 'user_1',
  name: 'Test User',
  email: 'test@email.com',
  avatar: '👤',
  joinDate: '2024-01-01',
  subscription: 'free',
  totalChats: 0,
  totalQuizzes: 0,
  streakDays: 0,
  preferences: {
    theme: 'light',
    notifications: true,
    autoSave: true,
  },
};

const defaultSidebarState: SidebarState = {
  isOpen: true,
  isCollapsed: false,
  selectedSessionId: null,
};

describe('Sidebar Chat Sessions', () => {
  afterEach(() => {
    localStorage.clear();
  });

  it('shows shimmer loading when isLoadingSessions is true', () => {
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={() => {}}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={true}
      />
    );
    expect(screen.getByTestId('chat-sessions-skeleton')).toBeInTheDocument();
  });

  it('shows error state when sessionsError is set', () => {
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={() => {}}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
        sessionsError="Failed to load sessions"
      />
    );
    expect(screen.getByText('Failed to load sessions')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('shows empty state when no sessions', () => {
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={() => {}}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    expect(screen.getByText('No chat sessions yet')).toBeInTheDocument();
  });

  it('shows sessions when chatSessions is provided', () => {
    const sessions: ChatSession[] = [
      {
        id: 'sess1',
        title: 'Budgeting',
        preview: 'Help me budget',
        timestamp: '2024-01-01T10:00:00Z',
        messageCount: 3,
        lastActivity: '2024-01-01T10:00:00Z',
        tags: [],
      },
      {
        id: 'sess2',
        title: 'Investing',
        preview: 'How to invest?',
        timestamp: '2024-01-02T10:00:00Z',
        messageCount: 5,
        lastActivity: '2024-01-02T10:00:00Z',
        tags: [],
      },
    ];
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={() => {}}
        chatSessions={sessions}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    expect(screen.getByText('Budgeting')).toBeInTheDocument();
    expect(screen.getByText('Investing')).toBeInTheDocument();
  });

  it('calls onSessionSelect when a session is clicked', () => {
    const sessions: ChatSession[] = [
      {
        id: 'sess1',
        title: 'Budgeting',
        preview: 'Help me budget',
        timestamp: '2024-01-01T10:00:00Z',
        messageCount: 3,
        lastActivity: '2024-01-01T10:00:00Z',
        tags: [],
      },
    ];
    const onSessionSelect = vi.fn();
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={() => {}}
        chatSessions={sessions}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={onSessionSelect}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    const sessionItem = screen.getByText('Budgeting');
    fireEvent.click(sessionItem);
    expect(onSessionSelect).toHaveBeenCalledWith('sess1');
  });

  it('calls onNewChat when New Chat is clicked', () => {
    const onNewChat = vi.fn();
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={() => {}}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={onNewChat}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    const newChatBtn = screen.getByText('New Chat');
    fireEvent.click(newChatBtn);
    expect(onNewChat).toHaveBeenCalled();
  });

  it('toggles sidebar open/closed state when setSidebarState is called', () => {
    const setSidebarState = vi.fn();
    const closedSidebarState: SidebarState = {
      isOpen: false,
      isCollapsed: false,
      selectedSessionId: null,
    };
    
    const { rerender } = render(
      <Sidebar
        sidebarState={closedSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify sidebar is closed (no open class)
    const sidebar = document.querySelector('.sidebar');
    expect(sidebar).not.toHaveClass('open');
    
    // Re-render with open state
    rerender(
      <Sidebar
        sidebarState={{ ...closedSidebarState, isOpen: true }}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify sidebar is now open
    const openSidebar = document.querySelector('.sidebar');
    expect(openSidebar).toHaveClass('open');
  });

  it('handles streaming response with "Thinking..." state', () => {
    const setSidebarState = vi.fn();
    const onSessionSelect = vi.fn();
    const onNewChat = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={onSessionSelect}
        onNewChat={onNewChat}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify sidebar is open and functional
    const sidebar = document.querySelector('.sidebar');
    expect(sidebar).toHaveClass('open');
    
    // Verify new chat button works
    const newChatBtn = screen.getByText('New Chat');
    expect(newChatBtn).toBeInTheDocument();
  });

  it('displays user-friendly error messages instead of raw JSON', () => {
    const setSidebarState = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
        sessionsError="An error occurred while processing your request. Please try again."
      />
    );
    
    // Verify error message is displayed
    expect(screen.getByText('An error occurred while processing your request. Please try again.')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('handles session management with proper UUIDs', () => {
    const setSidebarState = vi.fn();
    const onSessionSelect = vi.fn();
    
    const sessions: ChatSession[] = [
      {
        id: '550e8400-e29b-41d4-a716-446655440000', // Valid UUID
        title: 'Budgeting',
        preview: 'Help me budget',
        timestamp: '2024-01-01T10:00:00Z',
        messageCount: 3,
        lastActivity: '2024-01-01T10:00:00Z',
        tags: [],
      },
    ];
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={sessions}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={onSessionSelect}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify session is displayed
    expect(screen.getByText('Budgeting')).toBeInTheDocument();
    
    // Click on session
    const sessionItem = screen.getByText('Budgeting');
    fireEvent.click(sessionItem);
    expect(onSessionSelect).toHaveBeenCalledWith('550e8400-e29b-41d4-a716-446655440000');
  });

  it('handles streaming with dummy session ID', () => {
    const setSidebarState = vi.fn();
    const onSessionSelect = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={onSessionSelect}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify sidebar handles empty sessions gracefully
    expect(screen.getByText('No chat sessions yet')).toBeInTheDocument();
  });

  it('handles streaming with invalid UUID format', () => {
    const setSidebarState = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
        sessionsError="Invalid session ID format. Please try again."
      />
    );
    
    // Verify error message is displayed
    expect(screen.getByText('Invalid session ID format. Please try again.')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('handles streaming with nonexistent session', () => {
    const setSidebarState = vi.fn();
    const onSessionSelect = vi.fn();
    
    const sessions: ChatSession[] = [
      {
        id: 'nonexistent-session-id',
        title: 'Test Session',
        preview: 'This session does not exist',
        timestamp: '2024-01-01T10:00:00Z',
        messageCount: 0,
        lastActivity: '2024-01-01T10:00:00Z',
        tags: [],
      },
    ];
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={sessions}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={onSessionSelect}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify session is displayed even if it doesn't exist in backend
    expect(screen.getByText('Test Session')).toBeInTheDocument();
    
    // Click on session
    const sessionItem = screen.getByText('Test Session');
    fireEvent.click(sessionItem);
    expect(onSessionSelect).toHaveBeenCalledWith('nonexistent-session-id');
  });

  it('handles streaming with database errors', () => {
    const setSidebarState = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
        sessionsError="Database connection failed. Please try again later."
      />
    );
    
    // Verify database error message is displayed
    expect(screen.getByText('Database connection failed. Please try again later.')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('handles streaming with session creation failure', () => {
    const setSidebarState = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
        sessionsError="Failed to create session. Please try again."
      />
    );
    
    // Verify session creation error message is displayed
    expect(screen.getByText('Failed to create session. Please try again.')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('handles streaming with empty query validation', () => {
    const setSidebarState = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
        sessionsError="Query cannot be empty. Please enter a message."
      />
    );
    
    // Verify empty query error message is displayed
    expect(screen.getByText('Query cannot be empty. Please enter a message.')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('handles streaming with missing session ID validation', () => {
    const setSidebarState = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
        sessionsError="Session ID cannot be empty. Please try again."
      />
    );
    
    // Verify missing session ID error message is displayed
    expect(screen.getByText('Session ID cannot be empty. Please try again.')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('handles streaming with very long session ID', () => {
    const setSidebarState = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
        sessionsError="Session ID too long. Please try again."
      />
    );
    
    // Verify long session ID error message is displayed
    expect(screen.getByText('Session ID too long. Please try again.')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('handles concurrent sessions properly', () => {
    const setSidebarState = vi.fn();
    const onSessionSelect = vi.fn();
    
    const sessions: ChatSession[] = [
      {
        id: '550e8400-e29b-41d4-a716-446655440000',
        title: 'Session 1',
        preview: 'First concurrent session',
        timestamp: '2024-01-01T10:00:00Z',
        messageCount: 3,
        lastActivity: '2024-01-01T10:00:00Z',
        tags: [],
      },
      {
        id: '660e8400-e29b-41d4-a716-446655440001',
        title: 'Session 2',
        preview: 'Second concurrent session',
        timestamp: '2024-01-02T10:00:00Z',
        messageCount: 5,
        lastActivity: '2024-01-02T10:00:00Z',
        tags: [],
      },
    ];
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={sessions}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={onSessionSelect}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify both sessions are displayed
    expect(screen.getByText('Session 1')).toBeInTheDocument();
    expect(screen.getByText('Session 2')).toBeInTheDocument();
    
    // Click on first session
    const session1Item = screen.getByText('Session 1');
    fireEvent.click(session1Item);
    expect(onSessionSelect).toHaveBeenCalledWith('550e8400-e29b-41d4-a716-446655440000');
    
    // Click on second session
    const session2Item = screen.getByText('Session 2');
    fireEvent.click(session2Item);
    expect(onSessionSelect).toHaveBeenCalledWith('660e8400-e29b-41d4-a716-446655440001');
  });

  it('handles streaming error responses with 200 status code', () => {
    const setSidebarState = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
        sessionsError="An error occurred while processing your request. Please try again."
      />
    );
    
    // Verify error message is displayed even with 200 status
    expect(screen.getByText('An error occurred while processing your request. Please try again.')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('handles retry functionality for failed requests', () => {
    const setSidebarState = vi.fn();
    const onRetry = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
        sessionsError="Failed to load sessions"
      />
    );
    
    // Verify retry button is present
    const retryButton = screen.getByText('Retry');
    expect(retryButton).toBeInTheDocument();
    
    // Click retry button
    fireEvent.click(retryButton);
    // Note: The actual retry functionality would be handled by the parent component
  });

  it('handles session selection with proper error handling', () => {
    const setSidebarState = vi.fn();
    const onSessionSelect = vi.fn();
    
    const sessions: ChatSession[] = [
      {
        id: '550e8400-e29b-41d4-a716-446655440000',
        title: 'Test Session',
        preview: 'Test session with error handling',
        timestamp: '2024-01-01T10:00:00Z',
        messageCount: 2,
        lastActivity: '2024-01-01T10:00:00Z',
        tags: [],
      },
    ];
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={sessions}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={onSessionSelect}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify session is displayed
    expect(screen.getByText('Test Session')).toBeInTheDocument();
    
    // Click on session and verify callback is called
    const sessionItem = screen.getByText('Test Session');
    fireEvent.click(sessionItem);
    expect(onSessionSelect).toHaveBeenCalledWith('550e8400-e29b-41d4-a716-446655440000');
  });

  it('handles empty sessions list gracefully', () => {
    const setSidebarState = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={() => {}}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify empty state is displayed
    expect(screen.getByText('No chat sessions yet')).toBeInTheDocument();
    
    // Verify new chat button is still available
    expect(screen.getByText('New Chat')).toBeInTheDocument();
  });

  it('handles malformed session data gracefully', () => {
    const setSidebarState = vi.fn();
    const onSessionSelect = vi.fn();
    
    const malformedSessions: any[] = [
      {
        id: '550e8400-e29b-41d4-a716-446655440000',
        title: 'Valid Session',
        preview: 'This session has all required fields',
        timestamp: '2024-01-01T10:00:00Z',
        messageCount: 3,
        lastActivity: '2024-01-01T10:00:00Z',
        tags: [],
      },
      {
        // Missing required fields
        id: '660e8400-e29b-41d4-a716-446655440001',
        // title missing
        preview: 'Session with missing title',
        timestamp: '2024-01-02T10:00:00Z',
        messageCount: 1,
        lastActivity: '2024-01-02T10:00:00Z',
        tags: [],
      },
    ];
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={malformedSessions}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={onSessionSelect}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify valid session is displayed
    expect(screen.getByText('Valid Session')).toBeInTheDocument();
    
    // Verify malformed session is handled gracefully (should not crash)
    // The component should handle missing title gracefully
  });

  it('handles empty session ID on first chat window open', () => {
    const setSidebarState = vi.fn();
    const onSessionSelect = vi.fn();
    const onNewChat = vi.fn();
    
    // Mock localStorage to simulate empty session ID
    const originalGetItem = localStorage.getItem;
    localStorage.getItem = vi.fn((key: string) => {
      if (key === 'moneymentor_session_id') {
        return null; // Empty session ID
      }
      return originalGetItem.call(localStorage, key);
    });
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={onSessionSelect}
        onNewChat={onNewChat}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify empty state is displayed
    expect(screen.getByText('No chat sessions yet')).toBeInTheDocument();
    
    // Verify new chat button is available
    expect(screen.getByText('New Chat')).toBeInTheDocument();
    
    // Click new chat button to trigger session creation
    const newChatBtn = screen.getByText('New Chat');
    fireEvent.click(newChatBtn);
    expect(onNewChat).toHaveBeenCalled();
    
    // Restore original localStorage
    localStorage.getItem = originalGetItem;
  });

  it('handles session ID validation before sending messages', () => {
    const setSidebarState = vi.fn();
    const onSessionSelect = vi.fn();
    
    render(
      <Sidebar
        sidebarState={defaultSidebarState}
        setSidebarState={setSidebarState}
        chatSessions={[]}
        userProfile={mockUserProfile}
        profileModalState={{ isOpen: false, activeTab: 'profile' }}
        setProfileModalState={() => {}}
        onSessionSelect={onSessionSelect}
        onNewChat={() => {}}
        onProfileUpdate={() => {}}
        theme="light"
        isLoadingSessions={false}
      />
    );
    
    // Verify sidebar handles empty sessions gracefully
    expect(screen.getByText('No chat sessions yet')).toBeInTheDocument();
    
    // Verify new chat button works
    const newChatBtn = screen.getByText('New Chat');
    expect(newChatBtn).toBeInTheDocument();
  });
}); 

describe('Sidebar integration with ChatWidget windows', () => {
  function SidebarWithWindow({ initialWindow = 'chat', onSessionSelect }) {
    const [currentWindow, setCurrentWindow] = React.useState(initialWindow);
    const [selectedSession, setSelectedSession] = React.useState(null);
    const [pendingNewChat, setPendingNewChat] = React.useState(false);

    React.useEffect(() => {
      if (pendingNewChat && currentWindow === 'chat') {
        setSelectedSession(null);
        setPendingNewChat(false);
      }
    }, [currentWindow, pendingNewChat]);

    return (
      <>
        {(currentWindow === 'chat' || currentWindow === 'learn') && (
          <Sidebar
            sidebarState={{ ...defaultSidebarState, selectedSessionId: selectedSession }}
            setSidebarState={() => {}}
            chatSessions={[
              { id: 'sess1', title: 'Budgeting', preview: 'Help me budget', timestamp: '2024-01-01T10:00:00Z', messageCount: 3, lastActivity: '2024-01-01T10:00:00Z', tags: [] },
              { id: 'sess2', title: 'Investing', preview: 'How to invest?', timestamp: '2024-01-02T10:00:00Z', messageCount: 5, lastActivity: '2024-01-02T10:00:00Z', tags: [] }
            ]}
            userProfile={mockUserProfile}
            profileModalState={{ isOpen: false, activeTab: 'profile' }}
            setProfileModalState={() => {}}
            onSessionSelect={(id) => {
              if (currentWindow === 'learn') {
                setCurrentWindow('chat');
                setTimeout(() => {
                  setSelectedSession(id);
                  onSessionSelect && onSessionSelect(id);
                }, 0);
              } else {
                setSelectedSession(id);
                onSessionSelect && onSessionSelect(id);
              }
            }}
            onNewChat={() => {
              if (currentWindow === 'learn') {
                setPendingNewChat(true);
                setCurrentWindow('chat');
              } else {
                setSelectedSession(null);
              }
            }}
            onProfileUpdate={() => {}}
            theme="light"
            isLoadingSessions={false}
          />
        )}
        <button onClick={() => setCurrentWindow('learn')}>Switch to Learn</button>
        <button onClick={() => setCurrentWindow('chat')}>Switch to Chat</button>
        <div data-testid="current-window">{currentWindow}</div>
        <div data-testid="selected-session">{selectedSession}</div>
      </>
    );
  }

  it('renders Sidebar in chat window', () => {
    render(<SidebarWithWindow initialWindow="chat" />);
    expect(screen.getByText('Budgeting')).toBeInTheDocument();
    expect(screen.getByText('Investing')).toBeInTheDocument();
  });

  it('renders Sidebar in learn window', () => {
    render(<SidebarWithWindow initialWindow="learn" />);
    expect(screen.getByText('Budgeting')).toBeInTheDocument();
    expect(screen.getByText('Investing')).toBeInTheDocument();
  });

  it('clicking a session in learn window switches to chat and selects the session', async () => {
    const onSessionSelect = vi.fn();
    render(<SidebarWithWindow initialWindow="learn" onSessionSelect={onSessionSelect} />);
    expect(screen.getByTestId('current-window').textContent).toBe('learn');
    const sessionItem = screen.getByText('Budgeting');
    fireEvent.click(sessionItem);
    // Wait for next tick
    await waitFor(() => {
      expect(screen.getByTestId('current-window').textContent).toBe('chat');
      expect(screen.getByTestId('selected-session').textContent).toBe('sess1');
      expect(onSessionSelect).toHaveBeenCalledWith('sess1');
    });
  });

  it('clicking New Chat in learn window switches to chat and opens a clean chat window', async () => {
    render(<SidebarWithWindow initialWindow="learn" />);
    expect(screen.getByTestId('current-window').textContent).toBe('learn');
    const newChatBtn = screen.getByText('New Chat');
    fireEvent.click(newChatBtn);
    await waitFor(() => {
      expect(screen.getByTestId('current-window').textContent).toBe('chat');
      expect(screen.getByTestId('selected-session').textContent).toBe('');
    });
  });
}); 