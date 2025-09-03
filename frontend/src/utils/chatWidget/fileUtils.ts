export interface FileValidationResult {
  validFiles: File[];
  invalidFiles: File[];
  errors: string[];
}

export interface UploadProgress {
  isUploading: boolean;
  progress: number;
  currentFile?: string;
}

/**
 * Validate uploaded files
 */
export const validateFiles = (files: FileList): FileValidationResult => {
  const validTypes = ['application/pdf', 'text/plain', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'];
  const validExtensions = ['.pdf', '.txt', '.ppt', '.pptx'];
  const maxSize = 10 * 1024 * 1024; // 10MB
  
  const validFiles: File[] = [];
  const invalidFiles: File[] = [];
  const errors: string[] = [];
  
  Array.from(files).forEach(file => {
    const hasValidType = validTypes.includes(file.type);
    const hasValidExtension = validExtensions.some(ext => 
      file.name.toLowerCase().endsWith(ext)
    );
    const isValidSize = file.size <= maxSize;
    
    if ((hasValidType || hasValidExtension) && isValidSize) {
      validFiles.push(file);
    } else {
      invalidFiles.push(file);
      
      if (!hasValidType && !hasValidExtension) {
        errors.push(`${file.name}: Invalid file type. Only PDF, TXT, PPT, PPTX files are allowed.`);
      }
      if (!isValidSize) {
        errors.push(`${file.name}: File too large. Maximum size is 10MB.`);
      }
    }
  });
  
  return { validFiles, invalidFiles, errors };
};

/**
 * Format file size for display
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

/**
 * Get file extension
 */
export const getFileExtension = (fileName: string): string => {
  return fileName.slice((fileName.lastIndexOf('.') - 1 >>> 0) + 2);
};

/**
 * Check if file type is supported
 */
export const isSupportedFileType = (file: File): boolean => {
  const validTypes = ['application/pdf', 'text/plain', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'];
  const validExtensions = ['.pdf', '.txt', '.ppt', '.pptx'];
  
  const hasValidType = validTypes.includes(file.type);
  const hasValidExtension = validExtensions.some(ext => 
    file.name.toLowerCase().endsWith(ext)
  );
  
  return hasValidType || hasValidExtension;
};

/**
 * Initialize upload progress
 */
export const initializeUploadProgress = (): UploadProgress => ({
  isUploading: false,
  progress: 0
});

/**
 * Update upload progress
 */
export const updateUploadProgress = (
  current: number,
  total: number,
  currentFile?: string
): UploadProgress => ({
  isUploading: true,
  progress: Math.round((current / total) * 100),
  currentFile
});

/**
 * Complete upload progress
 */
export const completeUploadProgress = (): UploadProgress => ({
  isUploading: false,
  progress: 100
});

/**
 * Reset upload progress
 */
export const resetUploadProgress = (): UploadProgress => ({
  isUploading: false,
  progress: 0
}); 