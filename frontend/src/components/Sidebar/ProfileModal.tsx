import React, { useEffect, useState } from 'react';
import { UserProfile } from '../../types';
import { 
  getUserInitials, 
  formatJoinDate, 
  formatProfileStats
} from '../../utils/profile';
import { 
  handleModalBackdropClick,
  handleModalEscapeKey,
  handleNameUpdate,
  handleEmailUpdate,
  handleThemeToggle
} from '../../logic/profileHandlers';
import { getUserProfile, updateUserProfile, getAllQuizHistory } from '../../utils/chatWidget/api';
import { ProfileSkeleton } from './ProfileSkeleton';

interface ProfileModalProps {
  isOpen: boolean;
  activeTab: 'profile' | 'settings' | 'quizzes';
  userProfile: UserProfile;
  onClose: () => void;
  onTabSwitch: (tab: 'profile' | 'settings' | 'quizzes') => void;
  onProfileUpdate: (profile: Partial<UserProfile>) => void;
  theme?: 'light' | 'dark';
  apiConfig?: any; // For API calls
}

export const ProfileModal: React.FC<ProfileModalProps> = ({
  isOpen,
  activeTab,
  userProfile,
  onClose,
  onTabSwitch,
  onProfileUpdate,
  theme = 'light',
  apiConfig
}) => {
  const [editingName, setEditingName] = useState(false);
  const [editingEmail, setEditingEmail] = useState(false);
  const [tempName, setTempName] = useState(userProfile.name);
  const [tempEmail, setTempEmail] = useState(userProfile.email);
  const [isLoading, setIsLoading] = useState(false);
  const [backendProfile, setBackendProfile] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Quiz history state
  const [quizHistory, setQuizHistory] = useState<any[]>([]);
  const [quizHistoryLoading, setQuizHistoryLoading] = useState(false);
  const [quizHistoryError, setQuizHistoryError] = useState<string | null>(null);

  // Fetch profile data when modal opens
  useEffect(() => {
    if (isOpen && activeTab === 'profile') {
      fetchProfileData();
    }
  }, [isOpen, activeTab]);

  // Fetch quiz history when quizzes tab is active
  useEffect(() => {
    if (isOpen && activeTab === 'quizzes') {
      fetchQuizHistory();
    }
  }, [isOpen, activeTab]);

  const fetchProfileData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await getUserProfile();
      setBackendProfile(response);
      
      // Update local profile with backend data
      if (response.user) {
        const updatedProfile = {
          name: `${response.user.first_name} ${response.user.last_name}`.trim(),
          email: response.user.email,
          joinDate: response.user.created_at ? new Date(response.user.created_at).toISOString() : userProfile.joinDate,
          preferences: userProfile.preferences, // Keep existing preferences
          avatar: userProfile.avatar, // Keep existing avatar
        };
        onProfileUpdate(updatedProfile);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile');
      console.error('Failed to fetch profile:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchQuizHistory = async () => {
    if (!apiConfig) return;
    
    setQuizHistoryLoading(true);
    setQuizHistoryError(null);
    
    try {
      const response = await getAllQuizHistory(apiConfig);
              // Debug logging removed - data structure is now fixed
      console.log("quize history",response)
      
      // Transform backend data to match frontend expectations
      const transformedHistory = (response.quiz_history || [])
        .map((quiz: any) => {
          // Process quiz data
          
          // Parse question_data if it's a string (JSON)
          let questionData = quiz.question_data;
          if (typeof questionData === 'string') {
            try {
              questionData = JSON.parse(questionData);
            } catch (e) {
              console.error('Failed to parse question_data:', e);
              questionData = {};
            }
          } else if (!questionData) {
            questionData = {};
          }
          
          // Extract question text - try multiple possible locations
          let questionText = questionData?.question || 
                            quiz.question || 
                            quiz.quiz_question;

          // Only process quizzes that have valid question data
          if (questionText && questionText.trim() !== '') {
            // Handle different formats of choices (array or object)
            let options = ['A', 'B', 'C', 'D'];
            if (questionData?.choices) {
              if (Array.isArray(questionData.choices)) {
                options = questionData.choices;
              } else if (typeof questionData.choices === 'object') {
                options = Object.values(questionData.choices);
              }
            } else if (quiz.choices) {
              if (Array.isArray(quiz.choices)) {
                options = quiz.choices;
              } else if (typeof quiz.choices === 'object') {
                options = Object.values(quiz.choices);
              }
            }
            
            // Convert correct answer from letter to index
            let correctAnswer = 0;
            if (questionData?.correct_answer) {
              const correctLetter = questionData.correct_answer;
              correctAnswer = correctLetter.charCodeAt(0) - 65; // 'A' -> 0, 'B' -> 1, etc.
            } else if (quiz.correct_answer) {
              const correctLetter = quiz.correct_answer;
              correctAnswer = correctLetter.charCodeAt(0) - 65;
            }
            
            // Convert user answer from letter to index
            let userAnswer = 0;
            if (quiz.selected) {
              const userLetter = quiz.selected;
              userAnswer = userLetter.charCodeAt(0) - 65; // 'A' -> 0, 'B' -> 1, etc.
            } else if (quiz.user_answer) {
              const userLetter = quiz.user_answer;
              userAnswer = userLetter.charCodeAt(0) - 65;
            }
            
            const transformedQuiz = {
              question: questionText,
              options: options,
              correctAnswer: correctAnswer,
              userAnswer: userAnswer,
              explanation: questionData?.explanation || 
                          quiz.explanation || 
                          quiz.quiz_explanation ||
                          'No explanation available',
              topicTag: quiz.topic || quiz.topic_tag || '',
              timestamp: quiz.created_at || quiz.timestamp,
              quizType: quiz.quiz_type || 'micro'
            };
            
            return transformedQuiz;
          }
          
          // Return null for quizzes without valid question data
          return null;
        })
        .filter((quiz: any) => quiz !== null); // Filter out null entries
      
      setQuizHistory(transformedHistory);
    } catch (err) {
      setQuizHistoryError(err instanceof Error ? err.message : 'Failed to load quiz history');
      console.error('Failed to fetch quiz history:', err);
    } finally {
      setQuizHistoryLoading(false);
    }
  };

  // Handle escape key
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      handleModalEscapeKey(event, {
        profileModalState: { isOpen, activeTab },
        setProfileModalState: ({ isOpen: newIsOpen }) => {
          if (!newIsOpen) onClose();
        },
        userProfile,
        onProfileUpdate,
      });
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyPress);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyPress);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, activeTab, onClose, userProfile, onProfileUpdate]);

  // Reset temp values when profile changes
  useEffect(() => {
    setTempName(userProfile.name);
    setTempEmail(userProfile.email);
  }, [userProfile.name, userProfile.email]);

  const handleSaveName = async () => {
    if (!backendProfile?.user) return;
    
    try {
      const [firstName, ...lastNameParts] = tempName.trim().split(' ');
      const lastName = lastNameParts.join(' ') || '';
      
      const response = await updateUserProfile({
        first_name: firstName,
        last_name: lastName
      });
      
      if (response) {
        // Update local state
        const updatedProfile = {
          ...userProfile,
          name: tempName.trim()
        };
        onProfileUpdate(updatedProfile);
        setEditingName(false);
        
        // Refresh backend data
        await fetchProfileData();
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update name';
      alert(errorMessage);
      console.error('Failed to update name:', err);
    }
  };

  const handleSaveEmail = async () => {
    if (!backendProfile?.user) return;
    
    try {
      const response = await updateUserProfile({
        email: tempEmail.trim()
      });
      
      if (response) {
        // Update local state
        const updatedProfile = {
          ...userProfile,
          email: tempEmail.trim()
        };
        onProfileUpdate(updatedProfile);
        setEditingEmail(false);
        
        // Refresh backend data
        await fetchProfileData();
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update email';
      alert(errorMessage);
      console.error('Failed to update email:', err);
    }
  };

  const handleToggleTheme = async () => {
    await handleThemeToggle({
      profileModalState: { isOpen, activeTab },
      setProfileModalState: () => {},
      userProfile,
      onProfileUpdate,
    });
  };

  if (!isOpen) return null;

  const initials = getUserInitials(userProfile.name);
  const stats = formatProfileStats(userProfile);

  const renderProfileTab = () => {
    if (isLoading) {
      return <ProfileSkeleton theme={theme} />;
    }

    if (error) {
      return (
        <div>
          <div className="profile-header">
            <div className="profile-avatar-large">
              {userProfile.avatar && userProfile.avatar !== '👤' ? (
                <span>{userProfile.avatar}</span>
              ) : (
                <span>{initials}</span>
              )}
            </div>
            <div className="profile-details">
              <h3>{userProfile.name}</h3>
              <p>{userProfile.email}</p>
              <p className="join-date">{formatJoinDate(userProfile.joinDate)}</p>
              <div className="profile-error-indicator">
                <span className="error-icon">⚠️</span>
                <span className="error-text">Couldn't load latest stats</span>
              </div>
            </div>
          </div>

          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-value">{stats.totalChats || '—'}</div>
              <div className="stat-label">Total Chats</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{stats.totalQuizzes || '—'}</div>
              <div className="stat-label">Quizzes Taken</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{stats.streakDays || '—'}</div>
              <div className="stat-label">Day Streak</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{stats.daysSinceJoining || '—'}</div>
              <div className="stat-label">Days Active</div>
            </div>
          </div>

          <div className="profile-error-actions">
            <button 
              className="btn btn-secondary" 
              onClick={fetchProfileData}
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    return (
      <div>
        <div className="profile-header">
          <div className="profile-avatar-large">
            {userProfile.avatar && userProfile.avatar !== '👤' ? (
              <span>{userProfile.avatar}</span>
            ) : (
              <span>{initials}</span>
            )}
          </div>
          <div className="profile-details">
            {editingName ? (
              <div className="form-group">
                <input
                  type="text"
                  className="form-input"
                  value={tempName}
                  onChange={(e) => setTempName(e.target.value)}
                  onBlur={handleSaveName}
                  onKeyPress={(e) => e.key === 'Enter' && handleSaveName()}
                  autoFocus
                />
              </div>
            ) : (
              <h3 onClick={() => setEditingName(true)} style={{ cursor: 'pointer' }}>
                {userProfile.name} ✏️
              </h3>
            )}
            
            {editingEmail ? (
              <div className="form-group">
                <input
                  type="email"
                  className="form-input"
                  value={tempEmail}
                  onChange={(e) => setTempEmail(e.target.value)}
                  onBlur={handleSaveEmail}
                  onKeyPress={(e) => e.key === 'Enter' && handleSaveEmail()}
                  autoFocus
                />
              </div>
            ) : (
              <p onClick={() => setEditingEmail(true)} style={{ cursor: 'pointer' }}>
                {userProfile.email} ✏️
              </p>
            )}
            
            <p className="join-date">{formatJoinDate(userProfile.joinDate)}</p>
          </div>
        </div>

        <div className="stats-grid">
          <div className="stat-item">
            <div className="stat-value">
              {backendProfile?.profile?.total_chats != null
                ? backendProfile.profile.total_chats
                : (userProfile.totalChats != null ? userProfile.totalChats : '—')}
            </div>
            <div className="stat-label">Total Chats</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">
              {backendProfile?.statistics?.statistics?.total_quiz_responses != null
                ? backendProfile.statistics.statistics.total_quiz_responses
                : (backendProfile?.profile?.quizzes_taken != null
                    ? backendProfile.profile.quizzes_taken
                    : (userProfile.totalQuizzes != null ? userProfile.totalQuizzes : '—'))}
            </div>
            <div className="stat-label">Quizzes Taken</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">
              {backendProfile?.profile?.day_streak != null
                ? backendProfile.profile.day_streak
                : (userProfile.streakDays != null ? userProfile.streakDays : '—')}
            </div>
            <div className="stat-label">Day Streak</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">
              {backendProfile?.profile?.days_active != null
                ? backendProfile.profile.days_active
                : (userProfile.joinDate ? Math.max(1, Math.floor((Date.now() - new Date(userProfile.joinDate).getTime()) / (1000 * 60 * 60 * 24))) : '—')}
            </div>
            <div className="stat-label">Days Active</div>
          </div>
        </div>
      </div>
    );
  };

  const renderSettingsTab = () => (
    <div>
      <div className="setting-item">
        <div className="setting-info">
          <h4>Dark Mode</h4>
          <p>Switch between light and dark themes</p>
        </div>
        <button
          className={`toggle-switch ${userProfile.preferences.theme === 'dark' ? 'active' : ''}`}
          onClick={handleToggleTheme}
        />
      </div>

      <div className="action-buttons">
        <button className="btn btn-danger">
          🗑️ Delete Account
        </button>
      </div>
    </div>
  );

  const renderQuizzesTab = () => {
    if (quizHistoryLoading) {
      return (
        <div className="quiz-history-loading">
          <div className="loading-spinner"></div>
          <p>Loading quiz history...</p>
        </div>
      );
    }

    if (quizHistoryError) {
      return (
        <div className="quiz-history-error">
          <div className="error-icon">⚠️</div>
          <p>{quizHistoryError}</p>
          <button 
            className="btn btn-secondary" 
            onClick={fetchQuizHistory}
          >
            Retry
          </button>
        </div>
      );
    }

    if (quizHistory.length === 0) {
      return (
        <div className="quiz-history-empty">
          <div className="empty-icon">📝</div>
          <h3>No Quizzes Taken Yet</h3>
          <p>Start chatting to generate quizzes and see your progress here!</p>
        </div>
      );
    }

    return (
      <div className="quiz-history-list">
        <div className="quiz-history-header">
          <h3>Quizzes Taken ({quizHistory.length})</h3>
        </div>
        
        {quizHistory.map((quiz, index) => (
          <div key={index} className="quiz-history-item">
            <div className="quiz-question">
              { quiz.question &&  (
              <>
              <h4>{quiz.question}</h4>
              <div className="quiz-topic">
                {quiz.topicTag && <span className="topic-tag">{quiz.topicTag}</span>}
                <span className="quiz-type">{quiz.quizType}</span>
                <span className="quiz-date">
                  {new Date(quiz.timestamp).toLocaleDateString()}
                </span>
              </div>
              </>
              
            )

              }
            
            </div>
            
            <div className="quiz-options">
              {quiz.question && quiz.options.map((option: string, optionIndex: number) => {
                const isCorrect = optionIndex === quiz.correctAnswer;
                const isUserAnswer = optionIndex === quiz.userAnswer;
                const isCorrectAnswer = isCorrect;
                const isWrongAnswer = isUserAnswer && !isCorrect;
                
                return (
                  <div
                    key={optionIndex}
                    className={`quiz-option ${
                      isCorrectAnswer ? 'correct' : 
                      isWrongAnswer ? 'incorrect' : 
                      isUserAnswer ? 'selected' : ''
                    }`}
                  >
                    <span className="option-letter">
                      {String.fromCharCode(65 + optionIndex)})
                    </span>
                    <span className="option-text">
                      {typeof option === 'string' && option.length > 0 ? option : `Option ${String.fromCharCode(65 + optionIndex)}`}
                    </span>
                    {isCorrectAnswer && <span className="correct-indicator">✓</span>}
                    {isWrongAnswer && <span className="incorrect-indicator">✗</span>}
                    {isUserAnswer && !isCorrect && <span className="user-indicator">(You)</span>}
                  </div>
                );
              })}
            </div>
            
            {quiz.explanation && quiz.explanation !== 'No explanation available' && (
              <div className="quiz-explanation">
                <strong>💡 Explanation:</strong> {quiz.explanation}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div 
      className={`profile-modal-overlay ${isOpen ? 'active' : ''}`}
      onClick={(e) => handleModalBackdropClick(e, {
        profileModalState: { isOpen, activeTab },
        setProfileModalState: ({ isOpen: newIsOpen }) => {
          if (!newIsOpen) onClose();
        },
        userProfile,
        onProfileUpdate,
      })}
    >
      <div className={`profile-modal ${theme}`}>
        <div className="modal-header">
          <div className="modal-header-content">
            <h2 className="modal-title">Profile</h2>
            <button className="modal-close-btn" onClick={onClose}>
              ✕
            </button>
          </div>
          
          <div className="modal-tabs">
            <button
              className={`modal-tab ${activeTab === 'profile' ? 'active' : ''}`}
              onClick={() => onTabSwitch('profile')}
            >
              👤 Profile
            </button>
            <button
              className={`modal-tab ${activeTab === 'quizzes' ? 'active' : ''}`}
              onClick={() => onTabSwitch('quizzes')}
            >
              📝 Quizzes Taken
            </button>
            <button
              className={`modal-tab ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => onTabSwitch('settings')}
            >
              ⚙️ Settings
            </button>
          </div>
        </div>

        <div className="modal-content">
          {activeTab === 'profile' && renderProfileTab()}
          {activeTab === 'settings' && renderSettingsTab()}
          {activeTab === 'quizzes' && renderQuizzesTab()}
        </div>
      </div>
    </div>
  );
}; 