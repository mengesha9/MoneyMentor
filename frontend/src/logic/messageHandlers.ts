import { ChatMessage } from '../types';
import { 
  ApiConfig,
  sendChatMessageStream,
  createSystemMessage,
  createUserMessage,
  createAssistantMessage,
  convertCalculationResult,
} from '../utils/chatWidget';

export interface MessageHandlersProps {
  apiConfig: ApiConfig;
  sessionIds: { userId: string; sessionId: string };
  addMessage: (message: ChatMessage) => void;
  setInputValue: (value: string) => void;
  setShowCommandSuggestions: (show: boolean) => void;
  setCommandSuggestions: (suggestions: string[]) => void;
  setShowCommandMenu: (show: boolean) => void;
  setIsLoading: (loading: boolean) => void;
  closeCurrentDisplays: () => void;
  handleStartDiagnosticTestWrapper: () => Promise<void>;
  handleCoursesListWrapper: () => Promise<void>;
  setCurrentQuiz: (quiz: any) => void;
}

export const handleSendMessage = async (
  messageText: string,
  {
    apiConfig,
    sessionIds,
    addMessage,
    setInputValue,
    setShowCommandSuggestions,
    setCommandSuggestions,
    setShowCommandMenu,
    setIsLoading,
    closeCurrentDisplays,
    handleStartDiagnosticTestWrapper,
    handleCoursesListWrapper,
    setCurrentQuiz
  }: MessageHandlersProps
) => {
  try {
    setInputValue('');
    setShowCommandSuggestions(false);
    setCommandSuggestions([]);
    setShowCommandMenu(false);
    setIsLoading(true);

    // Handle diagnostic test command
    if (messageText === '/diagnostic' || messageText === 'diagnostic') {
      await handleStartDiagnosticTestWrapper();
      return;
    }

    // Handle courses command
    if (messageText === '/courses' || messageText === 'courses') {
      await handleCoursesListWrapper();
      return;
    }

    // Handle learn command
    if (messageText === '/learn' || messageText === 'learn') {
      closeCurrentDisplays();
      setIsLoading(false);
      const learnMessage = createSystemMessage(
        '📚 **Learn Mode**\n\nChoose from these learning options:\n\n🎯 **Diagnostic Test** - Take a quick assessment to identify your knowledge gaps\n🎓 **Browse Courses** - Explore our comprehensive financial courses\n\nType `/diagnostic` to start the assessment or `/courses` to browse available courses.',
        sessionIds.sessionId,
        sessionIds.userId
      );
      addMessage(learnMessage);
      return;
    }

    if (messageText === 'chat') {
      closeCurrentDisplays();
      setIsLoading(false);
      const chatMessage = createSystemMessage(
        '💬 **Chat Mode**\n\nI\'m ready to answer your financial questions! Ask me about budgeting, investing, debt management, and more.',
        sessionIds.sessionId,
        sessionIds.userId
      );
      addMessage(chatMessage);
      return;
    }

    // Add user message to chat
    const userMessage = createUserMessage(
      messageText,
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(userMessage);

    // Send to chat API using streaming
    let fullResponse: any = null;
    let streamingContent = '';
    let assistantMessage: ChatMessage | null = null;
    
    await sendChatMessageStream(
      apiConfig,
      messageText,
      (chunk: string) => {
        // Update the streaming content
        streamingContent += chunk;
        
        if (!assistantMessage) {
          // Create the assistant message on first chunk
          assistantMessage = createAssistantMessage(
            streamingContent,
            sessionIds.sessionId,
            sessionIds.userId
          );
          addMessage(assistantMessage);
        } else {
          // Update the assistant message with streaming content
          assistantMessage.content = streamingContent;
          
          // Update the message in the list
          addMessage(assistantMessage);
        }
      },
      (response: any) => {
        fullResponse = response;
      },
      (error: Error) => {
        console.error('Streaming error:', error);
        const errorMessage = createSystemMessage(
          'Network error. Please check your connection.',
          sessionIds.sessionId,
          sessionIds.userId
        );
        addMessage(errorMessage);
      }
    );
    
    // Handle backend response after streaming is complete
    if (fullResponse && fullResponse.message) {
      // Check if this is a calculation response
      if (fullResponse.is_calculation && fullResponse.calculation_result) {
        // Convert snake_case to camelCase for calculation result
        const calculationResult = convertCalculationResult(fullResponse.calculation_result);

        // Add calculation result to message metadata
        if (assistantMessage) {
          assistantMessage.metadata = {
            ...assistantMessage.metadata,
            calculationResult: calculationResult
          };
        }
      }
      
      // Handle quiz if present
      if (fullResponse.quiz) {
        setCurrentQuiz(fullResponse.quiz);
      }
    } else if (!fullResponse) {
      const errorMessage = createSystemMessage(
        'Sorry, I encountered an error. Please try again.',
        sessionIds.sessionId,
        sessionIds.userId
      );
      addMessage(errorMessage);
    }
  } catch (error) {
    console.error('Chat error:', error);
    const errorMessage = createSystemMessage(
      'Network error. Please check your connection.',
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(errorMessage);
  } finally {
    setIsLoading(false);
  }
}; 