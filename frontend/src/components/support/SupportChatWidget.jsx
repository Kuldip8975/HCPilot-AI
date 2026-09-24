import React, { useEffect, useRef, useState } from 'react';
import { MessageCircle, X, Send, Sparkles, RotateCcw } from 'lucide-react';

import { supportService } from '../../services/supportService';
import styles from './SupportChatWidget.module.css';

const QUICK_SUGGESTIONS = [
  'How do I log a visit?',
  'How do I add a doctor?',
  'Is it free to try?',
];

const TEASER_TEXT = "👋 Need help getting started? I'm here!";
const TEASER_DELAY_MS = 4000;
const TEASER_AUTO_HIDE_MS = 9000;

const makeWelcomeMessage = () => ({
  role: 'assistant',
  text: "Hi! I'm here to help you get started with HcPilot AI. What would you like to know?",
  time: new Date(),
});

const formatTime = (date) =>
  date
    ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

/**
 * Floating support/FAQ chat widget for the marketing homepage.
 *
 * This is a RAG-based assistant for anonymous visitors - it answers
 * questions about the product (grounded in app/rag/knowledge_base.py on
 * the backend), it does not log in, does not touch any CRM data, and
 * needs no auth token. It is a deliberately separate feature from the
 * in-app AI chat that logged-in reps use to log interactions.
 */
export const SupportChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([makeWelcomeMessage()]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showTeaser, setShowTeaser] = useState(false);
  const [hasUnread, setHasUnread] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const wrapperRef = useRef(null);

  // Proactive "hey, need help?" teaser - shows once, a few seconds after the
  // page loads, if the visitor hasn't opened the chat yet. Small touch that
  // makes the widget feel like it's actually paying attention, not just
  // sitting there waiting to be found.
  useEffect(() => {
    if (isOpen) return undefined;
    const showTimer = setTimeout(() => {
      setShowTeaser(true);
      setHasUnread(true);
    }, TEASER_DELAY_MS);
    return () => clearTimeout(showTimer);
  }, [isOpen]);

  useEffect(() => {
    if (!showTeaser) return undefined;
    const hideTimer = setTimeout(() => setShowTeaser(false), TEASER_AUTO_HIDE_MS);
    return () => clearTimeout(hideTimer);
  }, [showTeaser]);

  // Auto-scroll to the latest message and focus the input whenever the
  // panel is open.
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      inputRef.current?.focus();
    }
  }, [messages, isOpen]);

  // Click-outside-to-close: clicking anywhere outside the widget closes the
  // panel, same as most chat widgets people are already used to.
  useEffect(() => {
    if (!isOpen) return undefined;
    const handleClickOutside = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const openChat = () => {
    setIsOpen(true);
    setShowTeaser(false);
    setHasUnread(false);
  };

  const toggleChat = () => {
    if (isOpen) {
      setIsOpen(false);
    } else {
      openChat();
    }
  };

  const resetChat = () => {
    setMessages([makeWelcomeMessage()]);
    setInputValue('');
  };

  const sendMessage = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    setMessages((prev) => [...prev, { role: 'user', text: trimmed, time: new Date() }]);
    setInputValue('');
    setIsLoading(true);

    try {
      const result = await supportService.sendMessage(trimmed);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: result?.answer || "Sorry, I couldn't find an answer to that.",
          time: new Date(),
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: 'Sorry, something went wrong. Please try again in a moment.',
          time: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const hasUserMessaged = messages.some((msg) => msg.role === 'user');

  return (
    <div className={styles.wrapper} ref={wrapperRef}>
      {!isOpen && showTeaser && (
        <div className={styles.teaser} onClick={openChat} role="button" tabIndex={0}>
          <span>{TEASER_TEXT}</span>
          <button
            type="button"
            className={styles.teaserClose}
            aria-label="Dismiss"
            onClick={(e) => {
              e.stopPropagation();
              setShowTeaser(false);
            }}
          >
            <X size={12} />
          </button>
        </div>
      )}

      {isOpen && (
        <div className={styles.panel}>
          <div className={styles.header}>
            <div>
              <div className={styles.headerTitle}>
                <Sparkles size={16} />
                HcPilot Support
              </div>
              <div className={styles.headerSubtitle}>
                <span className={styles.statusDot} />
                Here to help you get started
              </div>
            </div>
            <div className={styles.headerActions}>
              <button
                type="button"
                className={styles.iconButton}
                onClick={resetChat}
                aria-label="Start a new chat"
                title="Start a new chat"
              >
                <RotateCcw size={15} />
              </button>
              <button
                type="button"
                className={styles.iconButton}
                onClick={() => setIsOpen(false)}
                aria-label="Close chat"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          <div className={styles.messages}>
            {messages.map((msg, idx) => (
              <div key={idx} className={styles.messageRow}>
                <div
                  className={msg.role === 'user' ? styles.bubbleUser : styles.bubbleAssistant}
                  style={{ animationDelay: `${Math.min(idx, 5) * 30}ms` }}
                >
                  {msg.text}
                </div>
                <span
                  className={
                    msg.role === 'user' ? styles.timeStampUser : styles.timeStampAssistant
                  }
                >
                  {formatTime(msg.time)}
                </span>
              </div>
            ))}
            {isLoading && (
              <div className={styles.bubbleAssistant}>
                <span className={styles.typingDot} />
                <span className={styles.typingDot} />
                <span className={styles.typingDot} />
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {!isLoading && (
            <div className={styles.suggestions}>
              {!hasUserMessaged && (
                <span className={styles.suggestionsLabel}>Quick questions</span>
              )}
              {QUICK_SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className={styles.suggestionChip}
                  onClick={() => sendMessage(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          <form className={styles.inputRow} onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              type="text"
              className={styles.input}
              placeholder="Type your message..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={isLoading}
            />
            <button
              type="submit"
              className={styles.sendButton}
              disabled={isLoading || !inputValue.trim()}
              aria-label="Send"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      )}

      <button
        type="button"
        className={`${styles.bubble} ${hasUnread && !isOpen ? styles.bubblePulse : ''}`}
        onClick={toggleChat}
        aria-label={isOpen ? 'Close support chat' : 'Open support chat'}
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
        {hasUnread && !isOpen && <span className={styles.unreadDot} />}
      </button>
    </div>
  );
};

export default SupportChatWidget;