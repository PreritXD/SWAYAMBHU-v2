import { useEffect } from 'react';

/**
 * useKeyboardShortcut
 * Listens for Cmd+K / Ctrl+K and '/' to trigger the 21st-style Command Palette,
 * and Escape to dismiss.
 */
export function useKeyboardShortcut({ onOpen, onClose, isOpen }) {
  useEffect(() => {
    function handleKeyDown(e) {
      // Ignore if user is currently typing in an input, textarea, or contentEditable
      const target = e.target;
      const isInput =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable;

      // Cmd + K or Ctrl + K
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          onOpen();
        }
        return;
      }

      // Quick '/' shortcut when not in input
      if (e.key === '/' && !isInput) {
        e.preventDefault();
        onOpen();
        return;
      }

      // Escape to close
      if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        onClose();
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onOpen, onClose, isOpen]);
}
