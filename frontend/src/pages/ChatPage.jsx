import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Send, 
  Mic, 
  User, 
  Bot, 
  Loader, 
  Plus, 
  MessageSquare,
  X,
  ChevronLeft
} from 'lucide-react';
import { toast } from 'react-toastify';

import { ROUTES } from '../routes/RouteConstants';
import { sendMessage, createSession, addMessage } from '../redux/slices/chatSlice';
import styles from './ChatPage.module.css';

/**
 * ChatPage Component
 * Full-page chat interface for AI interactions
 */
export const ChatPage = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const messages = useSelector((state) => state.chat.messages);
  const isProcessing = useSelector((state) => state.chat.isLoading);
  const activeSessionId = useSelector((state) => state.chat.activeSessionId);

  const [inputValue, setInputValue] = useState('');
  // NOTE: the backend doesn't yet persist/list past chat sessions
  // (no GET /ai/chat/sessions implemented), so this sidebar list is
  // cosmetic only - selecting one just relabels the header, it doesn't
  // load real historical messages from the server.
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [showSessions, setShowSessions] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Start a real chat session and show the initial greeting on first load
  useEffect(() => {
    if (!activeSessionId) {
      dispatch(createSession());
    }
    if (messages.length === 0) {
      dispatch(addMessage({
        id: 'welcome',
        role: 'assistant',
        content: 'Hello! I\'m your AI assistant for HCP interactions. I can help you log interactions, schedule follow-ups, search for HCPs, and answer any questions you have. How can I help you today?',
        timestamp: new Date().toISOString(),
      }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || isProcessing) return;

    const text = inputValue.trim();
    setInputValue('');

    try {
      await dispatch(sendMessage({ message: text, sessionId: activeSessionId, context: {} })).unwrap();
    } catch (error) {
      toast.error(error || 'Failed to process your message. Please try again.');
    } finally {
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    setActiveSession(null);
    dispatch(createSession());
    dispatch(addMessage({
      id: 'welcome',
      role: 'assistant',
      content: 'Starting a new conversation! How can I help you today?',
      timestamp: new Date().toISOString(),
    }));
    setShowSessions(false);
  };

  const handleSelectSession = (session) => {
    // NOTE: this only relabels the header - the backend doesn't persist
    // past sessions yet, so there's no real history to load here.
    setActiveSession(session);
    dispatch(createSession());
    dispatch(addMessage({
      id: 'session',
      role: 'assistant',
      content: `Continuing conversation: ${session.title}`,
      timestamp: new Date().toISOString(),
    }));
    setShowSessions(false);
  };

  const handleBackToDashboard = () => {
    navigate(ROUTES.DASHBOARD);
  };

  return (
    <div className={styles.chatPage}>
      {/* Sidebar - Sessions */}
      <div className={`${styles.sidebar} ${showSessions ? styles.sidebarOpen : ''}`}>
        <div className={styles.sidebarHeader}>
          <h3 className={styles.sidebarTitle}>Conversations</h3>
          <button className={styles.newChatButton} onClick={handleNewChat}>
            <Plus size={18} />
            New Chat
          </button>
        </div>
        <div className={styles.sessionList}>
          {sessions.map((session) => (
            <button
              key={session.id}
              className={`${styles.sessionItem} ${activeSession?.id === session.id ? styles.active : ''}`}
              onClick={() => handleSelectSession(session)}
            >
              <MessageSquare size={16} />
              <div className={styles.sessionInfo}>
                <div className={styles.sessionTitle}>{session.title}</div>
                <div className={styles.sessionTime}>
                  {new Date(session.timestamp).toLocaleDateString()}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className={styles.mainArea}>
        {/* Header */}
        <div className={styles.chatHeader}>
          <div className={styles.chatHeaderLeft}>
            <button 
              className={styles.menuButton}
              onClick={() => setShowSessions(!showSessions)}
            >
              <MessageSquare size={20} />
            </button>
            <button 
              className={styles.backButton}
              onClick={handleBackToDashboard}
            >
              <ChevronLeft size={20} />
              Dashboard
            </button>
            <div className={styles.chatInfo}>
              <span className={styles.chatTitle}>
                {activeSession ? activeSession.title : 'New Conversation'}
              </span>
              <span className={styles.chatStatus}>
                {isProcessing ? 'AI is typing...' : 'Online'}
              </span>
            </div>
          </div>
          <button className={styles.closeButton} onClick={handleBackToDashboard}>
            <X size={20} />
          </button>
        </div>

        {/* Messages */}
        <div className={styles.messagesContainer}>
          {messages.map((message) => (
            <div
              key={message.id}
              className={`${styles.message} ${
                message.role === 'user' ? styles.userMessage : styles.assistantMessage
              }`}
            >
              <div className={styles.messageAvatar}>
                {message.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={styles.messageContent}>
                <div className={styles.messageText}>{message.content}</div>
                <div className={styles.messageTime}>
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          {isProcessing && (
            <div className={`${styles.message} ${styles.assistantMessage}`}>
              <div className={styles.messageAvatar}>
                <Bot size={16} />
              </div>
              <div className={styles.messageContent}>
                <div className={styles.typingIndicator}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className={styles.chatInput}>
          <textarea
            ref={inputRef}
            className={styles.inputArea}
            placeholder="Type your message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            rows={1}
            disabled={isProcessing}
          />
          <div className={styles.inputActions}>
            <button
              className={styles.voiceButton}
              onClick={() => toast.info('Voice input coming soon!')}
            >
              <Mic size={20} />
            </button>
            <button
              className={styles.sendButton}
              onClick={handleSend}
              disabled={!inputValue.trim() || isProcessing}
            >
              {isProcessing ? <Loader size={20} className={styles.spinning} /> : <Send size={20} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;