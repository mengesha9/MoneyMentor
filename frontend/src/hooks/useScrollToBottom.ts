import { useRef, useEffect } from 'react';

export const useScrollToBottom = (dependencies: any[] = []) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when dependencies change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, dependencies);

  return messagesEndRef;
}; 