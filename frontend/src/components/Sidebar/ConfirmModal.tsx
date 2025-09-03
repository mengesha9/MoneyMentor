import React from 'react';
import '../../styles/sidebar.css';

interface ConfirmModalProps {
  open: boolean;
  title?: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmButtonText?: string;
  cancelButtonText?: string;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  open,
  title = 'Confirm',
  message,
  onConfirm,
  onCancel,
  confirmButtonText = 'Delete',
  cancelButtonText = 'Cancel',
}) => {
  if (!open) return null;

  return (
    <div className="mm-modal-overlay">
      <div className="mm-modal">
        {title && <div className="mm-modal-title">{title}</div>}
        <div className="mm-modal-message">{message}</div>
        <div className="mm-modal-actions">
          <button className="mm-modal-btn mm-modal-cancel" onClick={onCancel}>{cancelButtonText}</button>
          <button className="mm-modal-btn mm-modal-confirm" onClick={onConfirm}>{confirmButtonText}</button>
        </div>
      </div>
    </div>
  );
}; 