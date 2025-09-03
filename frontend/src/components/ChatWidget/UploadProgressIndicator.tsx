import React from 'react';
import '../../styles/ChatWidget.css';
import { UploadProgress } from '../../utils/chatWidget';

interface UploadProgressIndicatorProps {
  uploadProgress: UploadProgress;
}

export const UploadProgressIndicator: React.FC<UploadProgressIndicatorProps> = ({
  uploadProgress
}) => {
  if (!uploadProgress.isUploading) {
    return null;
  }

  return (
    <div className="upload-progress-indicator">
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${uploadProgress.progress}%` }}
        ></div>
      </div>
      <span>Uploading... {uploadProgress.progress}%</span>
    </div>
  );
}; 