import { useEffect } from 'react';

export const useClickOutside = (
  ref: React.RefObject<HTMLElement>,
  handler: () => void,
  selector?: string
) => {
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      
      if (selector) {
        // If selector is provided, check if click is outside the selector
        if (!target.closest(selector)) {
          handler();
        }
      } else if (ref.current && !ref.current.contains(target)) {
        // Otherwise check if click is outside the ref
        handler();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [ref, handler, selector]);
}; 