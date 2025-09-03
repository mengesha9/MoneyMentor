import React from 'react';
import '../../styles/ChatWidget.css';

interface CommandInputProps {
  showCommandMenu: boolean;
  availableCommands: { command: string; description: string; }[];
  activeMode: string;
  onCommandSelect: (command: string) => void;
  onToggleCommandMenu: () => void;
  disabled?: boolean;
}

export const CommandInput: React.FC<CommandInputProps> = ({
  showCommandMenu,
  availableCommands,
  activeMode,
  onCommandSelect,
  onToggleCommandMenu,
  disabled = false
}) => {
  return (
    <div className="chat-input">
      <div className="input-container">
        
        
        {/* Command Menu as MessageButtons */}
        {true && (
          <div className="message-buttons command-menu">
            {availableCommands.map((cmd, index) => (
              <button
                key={index}
                onClick={() => onCommandSelect(cmd.command)}
                className={`message-button ${cmd.command === activeMode ? 'active' : ''}`}
              >
                {cmd.command}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}; 