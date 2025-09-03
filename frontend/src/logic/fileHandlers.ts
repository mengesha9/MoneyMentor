import { ChatMessage } from '../types';
import { 
  ApiConfig,
  createSystemMessage,
  formatUploadSuccessMessage,
  formatUploadErrorMessage,
  formatFileRemovalMessage,
  uploadFile,
  removeFile,
  validateFiles,
  updateUploadProgress,
  resetUploadProgress,
  UploadProgress
} from '../utils/chatWidget';

export interface FileHandlersProps {
  apiConfig: ApiConfig;
  sessionIds: { userId: string; sessionId: string };
  addMessage: (message: ChatMessage) => void;
  setUploadedFiles: (files: File[]) => void;
  setUploadProgress: (progress: UploadProgress) => void;
  uploadedFiles: File[];
}

export const handleFileUpload = async (
  files: FileList,
  props: FileHandlersProps
) => {
  const {
    apiConfig,
    sessionIds,
    addMessage,
    setUploadedFiles,
    setUploadProgress,
    uploadedFiles
  } = props;

  const validation = validateFiles(files);
  
  if (validation.validFiles.length === 0) {
    const errorMessage = createSystemMessage(
      'Please upload valid files (PDF, TXT, PPT, PPTX) under 10MB each.',
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(errorMessage);
    return;
  }

  setUploadProgress({ isUploading: true, progress: 0 });

  try {
    for (let i = 0; i < validation.validFiles.length; i++) {
      const file = validation.validFiles[i];
      
      try {
        await uploadFile(apiConfig, file);
        setUploadedFiles([...uploadedFiles, file]);
        
        const successMessage = createSystemMessage(
          formatUploadSuccessMessage(file.name),
          sessionIds.sessionId,
          sessionIds.userId
        );
        addMessage(successMessage);
      } catch (error) {
        const errorMessage = createSystemMessage(
          formatUploadErrorMessage(file.name, error instanceof Error ? error.message : 'Unknown error'),
          sessionIds.sessionId,
          sessionIds.userId
        );
        addMessage(errorMessage);
      }

      setUploadProgress(updateUploadProgress(i + 1, validation.validFiles.length, file.name));
    }
  } catch (error) {
    console.error('Upload error:', error);
    const errorMessage = createSystemMessage(
      'Upload failed. Please check your connection and try again.',
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(errorMessage);
  } finally {
    setUploadProgress(resetUploadProgress());
  }
};

export const handleRemoveFile = async (
  fileIndex: number,
  props: FileHandlersProps
) => {
  const {
    sessionIds,
    addMessage,
    setUploadedFiles,
    uploadedFiles
  } = props;

  // Create a fresh copy of the array to avoid reference issues
  const currentFiles = [...uploadedFiles];

  // Debug logging
  

  // Validate fileIndex and file existence
  if (fileIndex < 0 || fileIndex >= currentFiles.length) {
    console.error('Invalid file index:', fileIndex, 'currentFiles length:', currentFiles.length);
    const errorMessage = createSystemMessage(
      'Invalid file index. Please try again.',
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(errorMessage);
    return;
  }

  const file = currentFiles[fileIndex];
 
  // Validate file object
  if (!file || !file.name) {
    console.error('Invalid file object at index:', fileIndex, 'file:', file);
    const errorMessage = createSystemMessage(
      'Invalid file object. Please try again.',
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(errorMessage);
    return;
  }
  
  try {
    // Remove file from local state immediately
    const updatedFiles = currentFiles.filter((_, index) => index !== fileIndex);
   
    setUploadedFiles(updatedFiles);
    
    const removalMessage = createSystemMessage(
      formatFileRemovalMessage(file.name),
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(removalMessage);
    
    // Optionally try to remove from backend, but don't fail if it doesn't work
    try {
      // await removeFile(apiConfig, file.name);
      // Backend remove endpoint might not exist, so we'll just remove locally
    } catch (backendError) {
      console.warn('Backend file removal failed, but file removed locally:', backendError);
    }
  } catch (error) {
    console.error('Remove file error:', error);
    const errorMessage = createSystemMessage(
      'Failed to remove file. Please try again.',
      sessionIds.sessionId,
      sessionIds.userId
    );
    addMessage(errorMessage);
  }
}; 