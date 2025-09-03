import { ChatSession } from '../types';

// Generate mock chat sessions with hard-coded data
export const getMockChatSessions = (): ChatSession[] => [
  {
    id: 'session_001',
    title: 'Budgeting Basics',
    preview: 'Can you help me create a monthly budget for my finances?',
    timestamp: '2024-01-20T10:30:00Z',
    messageCount: 15,
    lastActivity: '2024-01-20T11:45:00Z',
    tags: ['budgeting', 'planning'],
    isActive: true,
  },
  {
    id: 'session_002',
    title: 'Investment Strategies',
    preview: 'What are some good investment options for beginners?',
    timestamp: '2024-01-19T14:20:00Z',
    messageCount: 23,
    lastActivity: '2024-01-19T15:30:00Z',
    tags: ['investing', 'stocks'],
  },
  {
    id: 'session_003',
    title: 'Emergency Fund Planning',
    preview: 'How much should I save for an emergency fund?',
    timestamp: '2024-01-18T09:15:00Z',
    messageCount: 12,
    lastActivity: '2024-01-18T09:45:00Z',
    tags: ['savings', 'emergency'],
  },
  {
    id: 'session_004',
    title: 'Debt Management',
    preview: 'I need help with paying off my credit card debt...',
    timestamp: '2024-01-17T16:00:00Z',
    messageCount: 18,
    lastActivity: '2024-01-17T16:30:00Z',
    tags: ['debt', 'credit'],
  },
  {
    id: 'session_005',
    title: 'Retirement Planning',
    preview: 'When should I start planning for retirement?',
    timestamp: '2024-01-16T13:45:00Z',
    messageCount: 9,
    lastActivity: '2024-01-16T14:15:00Z',
    tags: ['retirement', 'planning'],
  },
  {
    id: 'session_006',
    title: 'Tax Planning Tips',
    preview: 'What are some tax deductions I should know about?',
    timestamp: '2024-01-15T11:30:00Z',
    messageCount: 14,
    lastActivity: '2024-01-15T12:00:00Z',
    tags: ['taxes', 'deductions'],
  },
  {
    id: 'session_007',
    title: 'Side Hustle Ideas',
    preview: 'Looking for ways to earn extra income...',
    timestamp: '2024-01-14T19:20:00Z',
    messageCount: 21,
    lastActivity: '2024-01-14T20:15:00Z',
    tags: ['income', 'entrepreneurship'],
  },
  {
    id: 'session_008',
    title: 'College Savings Plan',
    preview: 'Best ways to save for my child\'s education?',
    timestamp: '2024-01-13T08:30:00Z',
    messageCount: 16,
    lastActivity: '2024-01-13T09:00:00Z',
    tags: ['education', 'savings'],
  },
];

// Format timestamp for display
export const formatSessionTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor(diffMs / (1000 * 60));

  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
};

// Format last activity
export const formatLastActivity = (lastActivity: string): string => {
  const date = new Date(lastActivity);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));

  if (diffMinutes < 1) return 'Active now';
  if (diffMinutes < 60) return `Active ${diffMinutes}m ago`;
  
  return `Last active ${formatSessionTimestamp(lastActivity)}`;
};

// Generate session title from preview
export const generateSessionTitle = (preview: string, maxLength: number = 30): string => {
  if (!preview || preview.trim().length === 0) return 'New Chat';
  
  const cleanPreview = preview.trim();
  if (cleanPreview.length <= maxLength) return cleanPreview;
  
  // Find the last space before maxLength to avoid cutting words
  const truncated = cleanPreview.substring(0, maxLength);
  const lastSpace = truncated.lastIndexOf(' ');
  
  if (lastSpace > maxLength * 0.6) {
    return truncated.substring(0, lastSpace) + '...';
  }
  
  return truncated + '...';
};

// Sort sessions by timestamp (newest first)
export const sortSessionsByTimestamp = (sessions: ChatSession[]): ChatSession[] => {
  return [...sessions].sort((a, b) => {
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });
};

// Group sessions by date
export const groupSessionsByDate = (sessions: ChatSession[]): Record<string, ChatSession[]> => {
  const grouped: Record<string, ChatSession[]> = {};
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const lastWeek = new Date(today);
  lastWeek.setDate(lastWeek.getDate() - 7);

  sessions.forEach(session => {
    const sessionDate = new Date(session.timestamp);
    let group: string;

    if (sessionDate.toDateString() === today.toDateString()) {
      group = 'Today';
    } else if (sessionDate.toDateString() === yesterday.toDateString()) {
      group = 'Yesterday';
    } else if (sessionDate > lastWeek) {
      group = 'Previous 7 days';
    } else {
      group = sessionDate.toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric',
      });
    }

    if (!grouped[group]) {
      grouped[group] = [];
    }
    grouped[group].push(session);
  });

  return grouped;
};

// Filter sessions by search term
export const filterSessions = (sessions: ChatSession[], searchTerm: string): ChatSession[] => {
  if (!searchTerm.trim()) return sessions;
  
  const term = searchTerm.toLowerCase().trim();
  
  return sessions.filter(session => 
    session.title.toLowerCase().includes(term) ||
    session.preview.toLowerCase().includes(term) ||
    session.tags.some(tag => tag.toLowerCase().includes(term))
  );
};

// Get session by ID
export const getSessionById = (sessions: ChatSession[], sessionId: string): ChatSession | null => {
  return sessions.find(session => session.id === sessionId) || null;
};

// Create new session
export const createNewSession = (preview: string = ''): ChatSession => ({
  id: `session_${Date.now()}`,
  title: generateSessionTitle(preview) || 'New Chat',
  preview: preview || 'New conversation started...',
  timestamp: new Date().toISOString(),
  messageCount: 0,
  lastActivity: new Date().toISOString(),
  tags: [],
  isActive: true,
}); 