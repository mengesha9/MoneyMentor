import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ProfileModal } from '../../components/Sidebar/ProfileModal';
import { getUserProfile, updateUserProfile } from '../../utils/chatWidget/api';
import { UserProfile } from '../../types';

// Mock the API functions
vi.mock('../../utils/chatWidget/api', () => ({
  getUserProfile: vi.fn(),
  updateUserProfile: vi.fn(),
}));

// Mock the profile utilities
vi.mock('../../utils/profile', () => ({
  getUserInitials: vi.fn((name: string) => name.split(' ').map(n => n[0]).join('').slice(0, 2)),
  formatJoinDate: vi.fn((date: string) => 'January 15, 2024'),
  formatProfileStats: vi.fn(() => ({
    totalChats: '47',
    totalQuizzes: '156',
    streakDays: 12,
    daysSinceJoining: 30,
  })),
}));

// Mock the profile handlers
vi.mock('../../logic/profileHandlers', () => ({
  handleModalBackdropClick: vi.fn(),
  handleModalEscapeKey: vi.fn(),
  handleNameUpdate: vi.fn(),
  handleEmailUpdate: vi.fn(),
  handleThemeToggle: vi.fn(),
}));

describe('ProfileModal', () => {
  const mockUserProfile: UserProfile = {
    id: 'user_12345',
    name: 'Alex Johnson',
    email: 'alex.johnson@email.com',
    avatar: '👤',
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
  };

  const mockOnProfileUpdate = vi.fn();
  const mockOnClose = vi.fn();
  const mockOnTabSwitch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Data Fetching and Loading States', () => {
    it('should show shimmer skeleton when loading', async () => {
      // Mock a delayed response
      vi.mocked(getUserProfile).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({}), 100))
      );

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      // Should show skeleton initially
      expect(screen.getByTestId('profile-skeleton')).toBeInTheDocument();
      
      // Wait for loading to complete
      await waitFor(() => {
        expect(getUserProfile).toHaveBeenCalled();
      }, { timeout: 200 });
    });

    it('should fetch profile data when modal opens on profile tab', async () => {
      const mockBackendData = {
        user: { first_name: 'John', last_name: 'Doe', email: 'john.doe@example.com', created_at: '2024-01-15T00:00:00Z' },
        profile: {
          total_chats: 25,
          quizzes_taken: 15,
          day_streak: 5,
          days_active: 15,
        },
        statistics: {
          statistics: {
            total_quiz_responses: 15,
          },
        },
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        expect(getUserProfile).toHaveBeenCalled();
      });

      // Should update profile with backend data
      expect(mockOnProfileUpdate).toHaveBeenCalledWith({
        name: 'John Doe',
        email: 'john.doe@example.com',
        joinDate: '2024-01-15T00:00:00.000Z',
        preferences: mockUserProfile.preferences,
        avatar: mockUserProfile.avatar,
      });

      // Wait for loading to complete and check for updated data
      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument(); // Total Chats from backend
        expect(screen.getAllByText('15')).toHaveLength(2); // Quizzes Taken and Days Active from backend
        expect(screen.getByText('5')).toBeInTheDocument(); // Day Streak from backend
      });
    });

    it('should not fetch data when modal opens on settings tab', () => {
      render(
        <ProfileModal
          isOpen={true}
          activeTab="settings"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      expect(getUserProfile).not.toHaveBeenCalled();
    });

    it('should fetch data when switching to profile tab', async () => {
      const mockBackendData = {
        user: { first_name: 'John', last_name: 'Doe', email: 'john@example.com', created_at: '2024-01-15T00:00:00Z' },
        profile: { total_chats: 10 },
        statistics: { statistics: { total_quiz_responses: 5 } },
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);

      const { rerender } = render(
        <ProfileModal
          isOpen={true}
          activeTab="settings"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      // Simulate tab switch
      rerender(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        expect(getUserProfile).toHaveBeenCalled();
      });
    });
  });

  describe('Statistics Display Logic', () => {
    it('should display backend statistics when available', async () => {
      const mockBackendData = {
        user: { first_name: 'Alex', last_name: 'Johnson', email: 'alex.johnson@email.com' },
        profile: {
          total_chats: 25,
          quizzes_taken: 10,
          day_streak: 5,
          days_active: 15,
        },
        statistics: {
          statistics: {
            total_quiz_responses: 15,
          },
        },
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        expect(screen.getAllByText('25').length).toBeGreaterThan(0); // Total Chats
        expect(screen.getAllByText('15').length).toBeGreaterThan(0); // Quizzes Taken (from statistics)
        expect(screen.getAllByText('5').length).toBeGreaterThan(0); // Day Streak
        expect(screen.getAllByText('15').length).toBeGreaterThan(0); // Days Active
      });
    });

    it('should fallback to profile data when statistics not available', async () => {
      const mockBackendData = {
        user: { first_name: 'John', last_name: 'Doe', email: 'john@example.com' },
        profile: {
          total_chats: 25,
          quizzes_taken: 10,
          day_streak: 5,
          days_active: 15,
        },
        // No statistics object
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        expect(screen.getAllByText('10').length).toBeGreaterThan(0); // Quizzes Taken (from profile)
      });
    });

    it('should fallback to local data when backend data not available', async () => {
      vi.mocked(getUserProfile).mockResolvedValue({});

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        expect(screen.getAllByText('47').length).toBeGreaterThan(0); // Total Chats (local)
        expect(screen.getAllByText('156').length).toBeGreaterThan(0); // Quizzes Taken (local)
      });
    });

    it('should show placeholder when no data available', async () => {
      const emptyProfile = {
        ...mockUserProfile,
        totalChats: 0,
        totalQuizzes: 0,
        streakDays: 0,
        joinDate: '',
      };
      vi.mocked(getUserProfile).mockResolvedValue({});

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={emptyProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        // Check for the actual values shown when no data is available
        expect(screen.getAllByText('0')).toHaveLength(3); // Total Chats, Quizzes Taken, Day Streak
        expect(screen.getByText('—')).toBeInTheDocument(); // Days Active shows placeholder
      });
    });
  });

  describe('Error Handling', () => {
    it('should show elegant error state when API fails', async () => {
      vi.mocked(getUserProfile).mockRejectedValue(new Error('Network error'));

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        // Should still show user info
        expect(screen.getByText('Alex Johnson')).toBeInTheDocument();
        expect(screen.getByText('alex.johnson@email.com')).toBeInTheDocument();
        
        // Should show error indicator
        expect(screen.getByText('⚠️')).toBeInTheDocument();
        expect(screen.getByText('Couldn\'t load latest stats')).toBeInTheDocument();
        
        // Should show fallback stats
        expect(screen.getAllByText('47').length).toBeGreaterThan(0); // Total Chats
        expect(screen.getAllByText('156').length).toBeGreaterThan(0); // Quizzes Taken
        
        // Should show retry button
        expect(screen.getByText('Retry')).toBeInTheDocument();
      });
    });

    it('should retry data fetch when retry button is clicked', async () => {
      vi.mocked(getUserProfile)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          user: { first_name: 'John', last_name: 'Doe', email: 'john@example.com' },
          profile: { total_chats: 25 },
          statistics: { statistics: { total_quiz_responses: 15 } },
        });

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      // Wait for initial error
      await waitFor(() => {
        expect(screen.getByText('Couldn\'t load latest stats')).toBeInTheDocument();
      });

      // Click retry button
      const retryButton = screen.getByText('Retry');
      await userEvent.click(retryButton);

      // Should call API again
      await waitFor(() => {
        expect(getUserProfile).toHaveBeenCalledTimes(2);
      });
    });

    it('should handle different error types gracefully', async () => {
      const testCases = [
        new Error('Network error'),
        new Error('Unauthorized'),
        new Error('Server error'),
        { message: 'Custom error' },
      ];

      for (const error of testCases) {
        vi.mocked(getUserProfile).mockRejectedValue(error);

        const { unmount } = render(
          <ProfileModal
            isOpen={true}
            activeTab="profile"
            userProfile={mockUserProfile}
            onClose={mockOnClose}
            onTabSwitch={mockOnTabSwitch}
            onProfileUpdate={mockOnProfileUpdate}
          />
        );

        await waitFor(() => {
          expect(screen.getByText('Couldn\'t load latest stats')).toBeInTheDocument();
        });

        unmount();
      }
    });
  });

  describe('Name and Email Editing', () => {
    it('should allow editing name and save to backend', async () => {
      const mockBackendData = {
        user: { first_name: 'Alex', last_name: 'Johnson', email: 'alex.johnson@email.com' },
        profile: { total_chats: 25 },
        statistics: { statistics: { total_quiz_responses: 15 } },
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);
      vi.mocked(updateUserProfile).mockResolvedValue({ success: true });

      const { rerender } = render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Alex Johnson ✏️')).toBeInTheDocument();
      });

      // Click on name to edit
      const nameElement = screen.getByText('Alex Johnson ✏️');
      await userEvent.click(nameElement);

      // Should show input field
      const nameInput = screen.getByDisplayValue('Alex Johnson');
      expect(nameInput).toBeInTheDocument();

      // Change name
      await userEvent.clear(nameInput);
      await userEvent.type(nameInput, 'Jane Smith');

      // Save by pressing Enter
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(updateUserProfile).toHaveBeenCalledWith({
          first_name: 'Jane',
          last_name: 'Smith',
        });
      });

      // Simulate parent updating the prop
      rerender(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={{ ...mockUserProfile, name: 'Jane Smith' }}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      expect(screen.getByText('Jane Smith ✏️')).toBeInTheDocument();
    });

    it('should allow editing email and save to backend', async () => {
      const mockBackendData = {
        user: { first_name: 'Alex', last_name: 'Johnson', email: 'alex.johnson@email.com' },
        profile: { total_chats: 25 },
        statistics: { statistics: { total_quiz_responses: 15 } },
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);
      vi.mocked(updateUserProfile).mockResolvedValue({ success: true });

      const { rerender } = render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('alex.johnson@email.com ✏️')).toBeInTheDocument();
      });

      // Click on email to edit
      const emailElement = screen.getByText('alex.johnson@email.com ✏️');
      await userEvent.click(emailElement);

      // Should show input field
      const emailInput = screen.getByDisplayValue('alex.johnson@email.com');
      expect(emailInput).toBeInTheDocument();

      // Change email
      await userEvent.clear(emailInput);
      await userEvent.type(emailInput, 'jane@example.com');

      // Save by pressing Enter
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(updateUserProfile).toHaveBeenCalledWith({
          email: 'jane@example.com',
        });
      });

      // Simulate parent updating the prop
      rerender(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={{ ...mockUserProfile, email: 'jane@example.com' }}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      expect(screen.getByText('jane@example.com ✏️')).toBeInTheDocument();
    });

    it('should handle name update errors gracefully', async () => {
      const mockBackendData = {
        user: { first_name: 'Alex', last_name: 'Johnson', email: 'alex.johnson@email.com' },
        profile: { total_chats: 25 },
        statistics: { statistics: { total_quiz_responses: 15 } },
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);
      vi.mocked(updateUserProfile).mockRejectedValue(new Error('Update failed'));

      // Mock alert
      const mockAlert = vi.spyOn(window, 'alert').mockImplementation(() => {});

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        expect(
          screen.getAllByText((content, node) =>
            node?.textContent?.replace(/\s+/g, ' ').includes('Alex Johnson ✏️') || false
          ).length
        ).toBeGreaterThan(0);
      });

      // Click on name to edit
      const nameElement = screen.getByText('Alex Johnson ✏️');
      await userEvent.click(nameElement);

      // Change name
      const nameInput = screen.getByDisplayValue('Alex Johnson');
      await userEvent.clear(nameInput);
      await userEvent.type(nameInput, 'Jane Smith');

      // Save by pressing Enter
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Update failed');
      });

      mockAlert.mockRestore();
    });

    it('should handle email update errors gracefully', async () => {
      const mockBackendData = {
        user: { first_name: 'Alex', last_name: 'Johnson', email: 'alex.johnson@email.com' },
        profile: { total_chats: 25 },
        statistics: { statistics: { total_quiz_responses: 15 } },
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);
      vi.mocked(updateUserProfile).mockRejectedValue(new Error('Email update failed'));

      // Mock alert
      const mockAlert = vi.spyOn(window, 'alert').mockImplementation(() => {});

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        expect(
          screen.getAllByText((content, node) =>
            node?.textContent?.replace(/\s+/g, ' ').includes('alex.johnson@email.com ✏️') || false
          ).length
        ).toBeGreaterThan(0);
      });

      // Click on email to edit
      const emailElement = screen.getByText('alex.johnson@email.com ✏️');
      await userEvent.click(emailElement);

      // Change email
      const emailInput = screen.getByDisplayValue('alex.johnson@email.com');
      await userEvent.clear(emailInput);
      await userEvent.type(emailInput, 'jane@example.com');

      // Save by pressing Enter
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Email update failed');
      });

      mockAlert.mockRestore();
    });
  });

  describe('Theme Support', () => {
    it('should apply dark theme styles', async () => {
      const mockBackendData = {
        user: { first_name: 'John', last_name: 'Doe', email: 'john@example.com' },
        profile: { total_chats: 25 },
        statistics: { statistics: { total_quiz_responses: 15 } },
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
          theme="dark"
        />
      );

      await waitFor(() => {
        const modal = screen.getByText('Profile').closest('.profile-modal');
        expect(modal).toHaveClass('dark');
      });
    });

    it('should apply light theme styles by default', async () => {
      const mockBackendData = {
        user: { first_name: 'Alex', last_name: 'Johnson', email: 'alex.johnson@email.com' },
        profile: { total_chats: 25 },
        statistics: { statistics: { total_quiz_responses: 15 } },
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        const modal = screen.getByText('Profile').closest('.profile-modal');
        expect(modal).toHaveClass('light');
      });
    });
  });

  describe('Modal Interactions', () => {
    it('should close modal when close button is clicked', async () => {
      const mockBackendData = {
        user: { first_name: 'Alex', last_name: 'Johnson', email: 'alex.johnson@email.com' },
        profile: { total_chats: 25 },
        statistics: { statistics: { total_quiz_responses: 15 } },
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Alex Johnson ✏️')).toBeInTheDocument();
      });

      const closeButton = screen.getByText('✕');
      await userEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should switch tabs when tab buttons are clicked', async () => {
      const mockBackendData = {
        user: { first_name: 'Alex', last_name: 'Johnson', email: 'alex.johnson@email.com' },
        profile: { total_chats: 25 },
        statistics: { statistics: { total_quiz_responses: 15 } },
      };

      vi.mocked(getUserProfile).mockResolvedValue(mockBackendData);

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Alex Johnson ✏️')).toBeInTheDocument();
      });

      const settingsTab = screen.getByText('⚙️ Settings');
      await userEvent.click(settingsTab);

      expect(mockOnTabSwitch).toHaveBeenCalledWith('settings');
    });

    it('should not render when isOpen is false', () => {
      render(
        <ProfileModal
          isOpen={false}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      expect(screen.queryByText('Profile')).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty backend response', async () => {
      vi.mocked(getUserProfile).mockResolvedValue({});

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        // Should show local data as fallback when backend is empty
        expect(screen.getAllByText('47').length).toBeGreaterThan(0); // Total Chats
        expect(screen.getAllByText('156').length).toBeGreaterThan(0); // Quizzes Taken
      });
    });

    it('should handle partial backend response', async () => {
      const partialData = {
        user: { first_name: 'Alex', last_name: 'Johnson', email: 'alex.johnson@email.com' },
        // Missing profile and statistics
      };

      vi.mocked(getUserProfile).mockResolvedValue(partialData);

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        // Should show local data as fallback when profile/statistics are missing
        expect(screen.getAllByText('47').length).toBeGreaterThan(0); // Total Chats
        expect(screen.getAllByText('156').length).toBeGreaterThan(0); // Quizzes Taken
      });
    });

    it('should handle null values in backend response', async () => {
      const nullData = {
        user: { first_name: 'Alex', last_name: 'Johnson', email: 'alex.johnson@email.com' },
        profile: {
          total_chats: null,
          quizzes_taken: null,
          day_streak: null,
          days_active: null,
        },
        statistics: {
          statistics: {
            total_quiz_responses: null,
          },
        },
      };

      vi.mocked(getUserProfile).mockResolvedValue(nullData);

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        // Should show local data as fallback when backend values are null
        expect(screen.getAllByText('47').length).toBeGreaterThan(0); // Total Chats
        expect(screen.getAllByText('156').length).toBeGreaterThan(0); // Quizzes Taken
      });
    });

    it('should handle undefined values in backend response', async () => {
      const undefinedData = {
        user: { first_name: 'John', last_name: 'Doe', email: 'john@example.com' },
        profile: {
          total_chats: undefined,
          quizzes_taken: undefined,
          day_streak: undefined,
          days_active: undefined,
        },
        statistics: {
          statistics: {
            total_quiz_responses: undefined,
          },
        },
      };

      vi.mocked(getUserProfile).mockResolvedValue(undefinedData);

      render(
        <ProfileModal
          isOpen={true}
          activeTab="profile"
          userProfile={mockUserProfile}
          onClose={mockOnClose}
          onTabSwitch={mockOnTabSwitch}
          onProfileUpdate={mockOnProfileUpdate}
        />
      );

      await waitFor(() => {
        // Should show local data as fallback
        expect(screen.getAllByText('47').length).toBeGreaterThan(0); // Total Chats
        expect(screen.getAllByText('156').length).toBeGreaterThan(0); // Quizzes Taken
      });
    });
  });
}); 