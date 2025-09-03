import React, { useState } from 'react';
import { ChatSession } from '../../types';
import { 
  groupSessionsByDate, 
  sortSessionsByTimestamp, 
  formatSessionTimestamp 
} from '../../utils/sessions';
import { ChatSessionsSkeleton } from './ChatSessionsSkeleton';
import { ConfirmModal } from './ConfirmModal';

interface ChatSessionsListProps {
  sessions: ChatSession[];
  selectedSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onSessionDelete?: (sessionId: string) => Promise<void>;
  isCollapsed: boolean;
  isLoading?: boolean;
  theme?: 'light' | 'dark';
}

export const ChatSessionsList: React.FC<ChatSessionsListProps> = ({
  sessions,
  selectedSessionId,
  onSessionSelect,
  onSessionDelete,
  isCollapsed,
  isLoading = false,
  theme = 'light'
}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);

  const handleSessionDeleteClick = (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setSessionToDelete(sessionId);
    setModalOpen(true);
  };

  const handleModalConfirm = async () => {
    if (onSessionDelete && sessionToDelete) {
      try {
        await onSessionDelete(sessionToDelete);
      } catch (error) {
        console.error('Failed to delete session:', error);
        alert('Failed to delete session. Please try again.');
      }
    } else {
      console.warn('Session delete handler not provided');
    }
    setModalOpen(false);
    setSessionToDelete(null);
  };

  const handleModalCancel = () => {
    setModalOpen(false);
    setSessionToDelete(null);
  };

  // Show shimmer skeleton while loading
  if (isLoading) {
    return <ChatSessionsSkeleton theme={theme} isCollapsed={isCollapsed} />;
  }

  // Sort sessions by timestamp and group by date
  const sortedSessions = sortSessionsByTimestamp(sessions);
  const groupedSessions = groupSessionsByDate(sortedSessions);

  return (
    <div className="chat-sessions">
      <ConfirmModal
        open={modalOpen}
        title="Delete Chat Session"
        message="Are you sure you want to delete this chat session? This action cannot be undone."
        onConfirm={handleModalConfirm}
        onCancel={handleModalCancel}
        confirmButtonText="Delete"
        cancelButtonText="Cancel"
      />
      {Object.entries(groupedSessions).map(([groupTitle, groupSessions]) => (
        <div key={groupTitle} className="session-group">
          {!isCollapsed && (
            <div className="session-group-title">{groupTitle}</div>
          )}
          
          {groupSessions.map((session) => (
            <div key={session.id} className="session-item">
              <div
                className={`session-link ${session.id === selectedSessionId ? 'active' : ''}`}
                onClick={() => onSessionSelect(session.id)}
              >
                <div className="session-icon">
                  {session.isActive ? '💬' : '📝'}
                </div>
                
                {!isCollapsed && (
                  <div className="session-content">
                    <div className="session-title">{session.title}</div>
                    <div className="session-preview">{session.preview}</div>
                  </div>
                )}
              </div>
              
              {!isCollapsed && (
                <div className="session-actions">
                  <button
                    className="session-action-btn"
                    onClick={(e) => handleSessionDeleteClick(session.id, e)}
                    title="Delete session"
                  >
                    🗑️
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      ))}
      
      {sessions.length === 0 && !isLoading && (
        <div className="empty-sessions">
          {!isCollapsed && (
            <div style={{ 
              textAlign: 'center', 
              padding: '40px 20px', 
              color: '#64748b',
              fontSize: '14px'
            }}>
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>💭</div>
              <div>No chat sessions yet</div>
              <div style={{ fontSize: '12px', marginTop: '4px' }}>
                Start a new conversation to begin
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}; 