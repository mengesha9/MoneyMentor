import { 
  ApiConfig,
  createQuizFeedback,
  logQuizAnswer
} from '../utils/chatWidget';
import { QuizQuestion } from '../types';

export interface QuizHandlersProps {
  apiConfig: ApiConfig;
  setLastQuizAnswer: (feedback: any) => void;
  setShowQuizFeedback: (show: boolean) => void;
  setCurrentQuiz: (quiz: QuizQuestion | null) => void;
  setQuizSubmitting?: (loading: boolean) => void;
}

export const handleQuizAnswer = async (
  selectedOption: number,
  correct: boolean,
  currentQuiz: QuizQuestion | null,
  props: QuizHandlersProps
) => {
  const {
    apiConfig,
    setLastQuizAnswer,
    setShowQuizFeedback,
    setCurrentQuiz,
    setQuizSubmitting
  } = props;

  if (!currentQuiz) return;

  try {
    // Show shimmer loading for quiz submission
    if (setQuizSubmitting) {
      setQuizSubmitting(true);
    }
    
    await logQuizAnswer(
      apiConfig,
      currentQuiz.id,
      selectedOption,
      correct,
      currentQuiz.topicTag
    );

    const feedback = createQuizFeedback(selectedOption, currentQuiz.correctAnswer, currentQuiz.explanation);
    setLastQuizAnswer(feedback);
    setShowQuizFeedback(true);
    
    // Auto-hide feedback after 3 seconds
    setTimeout(() => {
      setShowQuizFeedback(false);
      setCurrentQuiz(null);
      setLastQuizAnswer(null);
    }, 3000);
  } catch (error) {
    console.error('Quiz logging error:', error);
  } finally {
    if (setQuizSubmitting) {
      setQuizSubmitting(false);
    }
  }
}; 