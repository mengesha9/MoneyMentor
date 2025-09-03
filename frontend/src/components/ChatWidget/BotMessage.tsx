import React, { memo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeKatex from 'rehype-katex';
import rehypeHighlight from 'rehype-highlight';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import { ContentCopy, Refresh, Edit, Delete, Check, Close } from '@mui/icons-material';
import ContentCopyOutlinedIcon from '@mui/icons-material/ContentCopyOutlined';
import ThumbUpOutlinedIcon from '@mui/icons-material/ThumbUpOutlined';
import ThumbDownOutlinedIcon from '@mui/icons-material/ThumbDownOutlined';
import 'katex/dist/katex.min.css';

interface BotMessageProps {
  content: string;
  messageId: string;
  onCopy?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  onRefresh?: () => void;
  isLastMessage?: boolean;
  isGenerating?: boolean;
  showActions?: boolean;
}

// Utility to fix LaTeX % comments in math blocks
function fixLatexComments(markdown: string): string {
  // Replace % with %\n only inside math blocks ($...$ or $$...$$)
  // This is a simple regex and may not cover all edge cases, but works for most LLM output
  return markdown.replace(/(\$[^\$\n]*?)%([^\n]*)/g, '$1%\n$2');
}

// Utility to escape $ before numbers (currency), so KaTeX doesn't treat as math
function escapeCurrencyDollars(markdown: string): string {
  // Replace $ with \\$ only when it is followed by a digit, but do not consume the digit
  return markdown.replace(/(^|[^\\$\w])\$(?=\d)/g, '$1\\$');
}



const BotMessage: React.FC<BotMessageProps> = ({
  content,
  messageId,
  onCopy,
  onEdit,
  onDelete,
  onRefresh,
  isLastMessage = false,
  isGenerating = false,
  showActions = true,
}) => {
  const [isDelete, setIsDelete] = useState<boolean>(false);
  const [markdownMode, setMarkdownMode] = useState<boolean>(true);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    onCopy?.();
  };

  const handleDelete = () => {
    onDelete?.();
  };

  const handleRefresh = () => {
    onRefresh?.();
  };

  const handleEdit = () => {
    onEdit?.();
  };

  const codeLanguageSubset = [
    'javascript',
    'typescript',
    'python',
    'java',
    'cpp',
    'csharp',
    'php',
    'ruby',
    'go',
    'rust',
    'swift',
    'kotlin',
    'scala',
    'html',
    'css',
    'sql',
    'json',
    'xml',
    'yaml',
    'markdown',
    'bash',
    'shell',
    'powershell',
    'dockerfile',
    'gitignore',
    'plaintext',
    'text',
  ];

  const code = memo((props: any) => {
    const { inline, className, children } = props;
    const match = /language-(\w+)/.exec(className || '');
    const lang = match && match[1];

    if (inline) {
      return <code className={`${className} bg-gray-100 dark:bg-gray-800 px-1 py-0-5 rounded text-sm`}>{children}</code>;
    } else {
      return (
        <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 my-2 overflow-x-auto">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-gray-500 dark:text-gray-400 uppercase font-medium">
              {lang || 'text'}
            </span>
            <button
              onClick={() => navigator.clipboard.writeText(String(children))}
              className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              Copy
            </button>
          </div>
          <pre className="text-sm">
            <code className={`language-${lang || 'text'}`}>{children}</code>
          </pre>
        </div>
      );
    }
  });

  // Simple paragraph component that preserves original content
  const p = memo((props: any) => {
    const content = props?.children;
    const isThinking = typeof content === 'string' && content.includes('**Thinking...**');
    
    if (isThinking) {
      return (
        <p className="whitespace-pre-wrap mb-2 leading-relaxed">
          <span className="thinking-shimmer">Thinking...</span>
        </p>
      );
    }
    
    return <p className="whitespace-pre-wrap mb-2 leading-relaxed">{content}</p>;
  });

  return (
    <div className="bot-message">
      <div className="markdown prose w-full max-w-full break-words dark:prose-invert">
        <ReactMarkdown
          remarkPlugins={[remarkMath, remarkGfm]}
          rehypePlugins={[rehypeKatex, rehypeHighlight]}
          components={{
            code,
            p,
          }}
        >
          {fixLatexComments(escapeCurrencyDollars(content))}
        </ReactMarkdown>
      </div>

      {showActions && (
        <>
          {/* Original buttons - shown when not generating */}
          {!isGenerating && (
            <div className="bot-message-actions">
              <button className="bot-action-btn" title="Copy" onClick={handleCopy}>
                <ContentCopyOutlinedIcon style={{ fontSize: 22 }} />
              </button>
              {/* <button className="bot-action-btn" title="Like" disabled>
                <ThumbUpOutlinedIcon style={{ fontSize: 22 }} />
              </button>
              <button className="bot-action-btn" title="Dislike" disabled>
                <ThumbDownOutlinedIcon style={{ fontSize: 22 }} />
              </button> */}
            </div>
          )}
          
          {/* Advanced actions - shown on hover when not generating */}
          {!isGenerating && (
            <div className="flex justify-end gap-1 w-full mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              {isDelete ? (
                <>
                  <button
                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                    aria-label="cancel"
                    onClick={() => setIsDelete(false)}
                  >
                    <Close fontSize="small" />
                  </button>
                  <button
                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                    aria-label="confirm"
                    onClick={handleDelete}
                  >
                    <Check fontSize="small" />
                  </button>
                </>
              ) : (
                <>
                  {isLastMessage && onRefresh && (
                    <button
                      className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                      onClick={handleRefresh}
                      title="Regenerate response"
                    >
                      <Refresh fontSize="small" />
                    </button>
                  )}
                  

                  
                  {onEdit && (
                    <button
                      className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                      onClick={handleEdit}
                      title="Edit message"
                    >
                      <Edit fontSize="small" />
                    </button>
                  )}
                  
                  {onDelete && (
                    <button
                      className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                      onClick={() => setIsDelete(true)}
                      title="Delete message"
                    >
                      <Delete fontSize="small" />
                    </button>
                  )}
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default BotMessage; 