import React from 'react';
import { FileText, X } from 'lucide-react';
import '../../styles/ChatWidget.css';
import { formatFileSize } from '../../utils/chatWidget';

interface UploadedFilesDisplayProps {
  uploadedFiles: File[];
  onRemoveFile: (fileIndex: number) => void;
}

export const UploadedFilesDisplay: React.FC<UploadedFilesDisplayProps> = ({
  uploadedFiles,
  onRemoveFile
}) => {
  // Safety check - don't render if no files or invalid files array
  if (!uploadedFiles || uploadedFiles.length === 0) {
    return null;
  }

  const handleRemoveFile = (index: number) => {
    // Additional safety checks before calling the remove function
    if (!uploadedFiles || !Array.isArray(uploadedFiles)) {
      console.error('uploadedFiles is not a valid array:', uploadedFiles);
      return;
    }
    
    if (index < 0 || index >= uploadedFiles.length) {
      console.error('Invalid file index:', index, 'files length:', uploadedFiles.length);
      return;
    }
    
    const file = uploadedFiles[index];
    if (!file || !file.name) {
      console.error('Invalid file object at index:', index, 'file:', file);
      return;
    }
    
    // Call the remove function
    onRemoveFile(index);
  };

  return (
    <div className="uploaded-files">
      <div className="files-header">
        <FileText size={16} />
        <span>Your Content ({uploadedFiles.length})</span>
      </div>
      <div className="files-list">
        {uploadedFiles.map((file, index) => (
          <div key={index} className="file-item">
            <div className="file-info">
              <FileText size={14} />
              <span className="file-name">{file.name}</span>
              <span className="file-size">
                {formatFileSize(file.size)}
              </span>
            </div>
            <button 
              onClick={() => handleRemoveFile(index)}
              className="remove-file-btn"
              title="Remove file"
            >
              <X size={12} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}; 