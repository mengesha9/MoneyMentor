import { UserProfile } from '../types';

// Default user profile with hard-coded data
export const getDefaultUserProfile = (): UserProfile => ({
  id: 'user_12345',
  name: 'Alex Johnson',
  email: 'alex.johnson@email.com',
  avatar: '👤', // Using emoji as placeholder avatar
  joinDate: '2024-01-15',
  subscription: 'premium',
  totalChats: 47,
  totalQuizzes: 156,
  streakDays: 12,
  preferences: {
    theme: 'light',
    notifications: true,
    autoSave: true,
  },
});

// Format join date for display
export const formatJoinDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};

// Calculate days since joining
export const getDaysSinceJoining = (joinDate: string): number => {
  const join = new Date(joinDate);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - join.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
};

// Format subscription type
export const formatSubscriptionType = (subscription: 'free' | 'premium'): string => {
  return subscription === 'premium' ? 'Premium Member' : 'Free Member';
};

// Get subscription badge color
export const getSubscriptionBadgeColor = (subscription: 'free' | 'premium'): string => {
  return subscription === 'premium' ? '#FFD700' : '#6B7280';
};

// Generate user initials from name
export const getUserInitials = (name: string): string => {
  return name
    .split(' ')
    .map(part => part.charAt(0).toUpperCase())
    .join('')
    .slice(0, 2);
};

// Format stats for display
export const formatProfileStats = (profile: UserProfile) => ({
  totalChats: profile.totalChats.toLocaleString(),
  totalQuizzes: profile.totalQuizzes.toLocaleString(),
  streakDays: profile.streakDays,
  daysSinceJoining: getDaysSinceJoining(profile.joinDate),
});

// Validate email format
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Get achievement based on stats
export const getUserAchievements = (profile: UserProfile): string[] => {
  const achievements: string[] = [];
  
  if (profile.totalChats >= 50) achievements.push('💬 Chat Master');
  if (profile.totalQuizzes >= 100) achievements.push('🎯 Quiz Champion');
  if (profile.streakDays >= 7) achievements.push('🔥 Week Warrior');
  if (profile.streakDays >= 30) achievements.push('⭐ Monthly Master');
  if (getDaysSinceJoining(profile.joinDate) >= 30) achievements.push('🏆 Veteran Learner');
  
  return achievements;
}; 