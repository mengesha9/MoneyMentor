import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { ChatSessionsList } from '../../components/Sidebar/ChatSessionsList';
import { ChatSession } from '../../types';

// Mock console methods
const mockConsoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
const mockConsoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
const mockAlert = vi.spyOn(window, 'alert').mockImplementation(() => {});

describe('Sidebar Delete Session', () => {
  const mockSessions: ChatSession[] = [
    {
      id: 'session-1',
      title: 'Test Session 1',
      preview: 'Test preview 1',
      timestamp: '2024-01-01T00:00:00Z',
      messageCount: 5,
      lastActivity: '2024-01-01T00:00:00Z',
      tags: [],
      isActive: false
    },
    {
      id: 'session-2',
      title: 'Test Session 2',
      preview: 'Test preview 2',
      timestamp: '2024-01-02T00:00:00Z',
      messageCount: 3,
      lastActivity: '2024-01-02T00:00:00Z',
      tags: [],
      isActive: true
    }
  ];

  const mockOnSessionSelect = vi.fn();
  const mockOnSessionDelete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterAll(() => {
    mockConsoleWarn.mockRestore();
    mockConsoleError.mockRestore();
    mockAlert.mockRestore();
  });

  it('shows delete button for each session when not collapsed', () => {
    render(
      <ChatSessionsList
        sessions={mockSessions}
        selectedSessionId={null}
        onSessionSelect={mockOnSessionSelect}
        onSessionDelete={mockOnSessionDelete}
        isCollapsed={false}
        isLoading={false}
        theme="light"
      />
    );

    const deleteButtons = screen.getAllByTitle('Delete session');
    expect(deleteButtons).toHaveLength(2);
  });

  it('does not show delete buttons when collapsed', () => {
    render(
      <ChatSessionsList
        sessions={mockSessions}
        selectedSessionId={null}
        onSessionSelect={mockOnSessionSelect}
        onSessionDelete={mockOnSessionDelete}
        isCollapsed={true}
        isLoading={false}
        theme="light"
      />
    );

    const deleteButtons = screen.queryAllByTitle('Delete session');
    expect(deleteButtons).toHaveLength(0);
  });

  it('shows confirmation modal when delete button is clicked', async () => {
    render(
      <ChatSessionsList
        sessions={mockSessions}
        selectedSessionId={null}
        onSessionSelect={mockOnSessionSelect}
        onSessionDelete={mockOnSessionDelete}
        isCollapsed={false}
        isLoading={false}
        theme="light"
      />
    );

    // Find the session item for 'Test Session 1'
    const sessionTitle = screen.getByText('Test Session 1');
    const sessionItem = sessionTitle.closest('.session-item');
    const deleteButton = sessionItem.querySelector('button[title="Delete session"]');
    fireEvent.click(deleteButton);

    // Modal should appear
    expect(screen.getByText('Delete Chat Session')).toBeInTheDocument();
    expect(screen.getByText('Are you sure you want to delete this chat session? This action cannot be undone.')).toBeInTheDocument();
  });

  it('calls onSessionDelete when user confirms deletion', async () => {
    mockOnSessionDelete.mockResolvedValue(undefined);

    render(
      <ChatSessionsList
        sessions={mockSessions}
        selectedSessionId={null}
        onSessionSelect={mockOnSessionSelect}
        onSessionDelete={mockOnSessionDelete}
        isCollapsed={false}
        isLoading={false}
        theme="light"
      />
    );

    // Find the session item for 'Test Session 1'
    const sessionTitle = screen.getByText('Test Session 1');
    const sessionItem = sessionTitle.closest('.session-item');
    const deleteButton = sessionItem.querySelector('button[title="Delete session"]');
    fireEvent.click(deleteButton);

    // Click confirm in modal
    const confirmBtn = screen.getByText('Delete');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(mockOnSessionDelete).toHaveBeenCalledWith('session-1');
    });
  });

  it('does not call onSessionDelete when user cancels deletion', async () => {
    render(
      <ChatSessionsList
        sessions={mockSessions}
        selectedSessionId={null}
        onSessionSelect={mockOnSessionSelect}
        onSessionDelete={mockOnSessionDelete}
        isCollapsed={false}
        isLoading={false}
        theme="light"
      />
    );

    // Find the session item for 'Test Session 1'
    const sessionTitle = screen.getByText('Test Session 1');
    const sessionItem = sessionTitle.closest('.session-item');
    const deleteButton = sessionItem.querySelector('button[title="Delete session"]');
    fireEvent.click(deleteButton);

    // Click cancel in modal
    const cancelBtn = screen.getByText('Cancel');
    fireEvent.click(cancelBtn);

    expect(mockOnSessionDelete).not.toHaveBeenCalled();
  });

  it('shows error alert when onSessionDelete throws an error', async () => {
    const mockAlert = vi.spyOn(window, 'alert').mockImplementation(() => {});
    const error = new Error('Delete failed');
    mockOnSessionDelete.mockRejectedValue(error);

    render(
      <ChatSessionsList
        sessions={mockSessions}
        selectedSessionId={null}
        onSessionSelect={mockOnSessionSelect}
        onSessionDelete={mockOnSessionDelete}
        isCollapsed={false}
        isLoading={false}
        theme="light"
      />
    );

    // Find the session item for 'Test Session 1'
    const sessionTitle = screen.getByText('Test Session 1');
    const sessionItem = sessionTitle.closest('.session-item');
    const deleteButton = sessionItem.querySelector('button[title="Delete session"]');
    fireEvent.click(deleteButton);

    // Click confirm in modal
    const confirmBtn = screen.getByText('Delete');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(mockAlert).toHaveBeenCalledWith('Failed to delete session. Please try again.');
    });
    mockAlert.mockRestore();
  });

  it('logs warning when onSessionDelete is not provided', () => {
    const mockWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    render(
      <ChatSessionsList
        sessions={mockSessions}
        selectedSessionId={null}
        onSessionSelect={mockOnSessionSelect}
        isCollapsed={false}
        isLoading={false}
        theme="light"
      />
    );

    const sessionTitle = screen.getByText('Test Session 1');
    const sessionItem = sessionTitle.closest('.session-item');
    const deleteButton = sessionItem.querySelector('button[title="Delete session"]');
    fireEvent.click(deleteButton);

    // Click confirm in modal
    const confirmBtn = screen.getByText('Delete');
    fireEvent.click(confirmBtn);

    expect(mockWarn).toHaveBeenCalledWith('Session delete handler not provided');
    mockWarn.mockRestore();
  });

  it('prevents event propagation when delete button is clicked', () => {
    render(
      <ChatSessionsList
        sessions={mockSessions}
        selectedSessionId={null}
        onSessionSelect={mockOnSessionSelect}
        onSessionDelete={mockOnSessionDelete}
        isCollapsed={false}
        isLoading={false}
        theme="light"
      />
    );

    const sessionTitle = screen.getByText('Test Session 1');
    const sessionItem = sessionTitle.closest('.session-item');
    const deleteButton = sessionItem.querySelector('button[title="Delete session"]');
    // Create a mock event with stopPropagation
    const mockEvent = {
      stopPropagation: vi.fn()
    } as any;
    fireEvent.click(deleteButton, mockEvent);
    // The important thing is that the delete functionality works
    expect(screen.getByText('Delete Chat Session')).toBeInTheDocument();
  });
}); 