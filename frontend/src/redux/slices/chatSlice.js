import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { toast } from 'react-toastify';
import { chatService } from '../../services/chatService';

export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ message, sessionId, context }, { rejectWithValue }) => {
    try {
      const data = await chatService.sendMessage(message, sessionId, context);
      // The backend returns { success, response, session_id, intent, tool_executed, interaction, should_end }
      // Shape it into the {userMessage, assistantMessage, sessionId} format this slice expects.
      const userMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      };
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response || "I've processed your request.",
        timestamp: new Date().toISOString(),
        intent: data.intent,
      };
      return {
        userMessage,
        assistantMessage,
        sessionId: data.session_id || sessionId,
      };
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to send message');
    }
  }
);

export const fetchSessions = createAsyncThunk(
  'chat/fetchSessions',
  async (_, { rejectWithValue }) => {
    try {
      const response = await chatService.getSessions();
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch sessions');
    }
  }
);

export const fetchSession = createAsyncThunk(
  'chat/fetchSession',
  async (sessionId, { rejectWithValue }) => {
    try {
      const response = await chatService.getSession(sessionId);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch session');
    }
  }
);

export const deleteSession = createAsyncThunk(
  'chat/deleteSession',
  async (sessionId, { rejectWithValue }) => {
    try {
      const response = await chatService.deleteSession(sessionId);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to delete session');
    }
  }
);

const initialState = {
  messages: [],
  sessions: [],
  activeSessionId: null,
  isLoading: false,
  error: null,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setActiveSession: (state, action) => {
      state.activeSessionId = action.payload;
      const session = state.sessions.find((s) => s.id === action.payload);
      state.messages = session?.messages || [];
    },
    addMessage: (state, action) => {
      state.messages.push(action.payload);
      const session = state.sessions.find((s) => s.id === state.activeSessionId);
      if (session) {
        if (!session.messages) session.messages = [];
        session.messages.push(action.payload);
      }
    },
    createSession: (state, action) => {
      const newSession = {
        id: `session-${Date.now()}`,
        title: action.payload || 'New Conversation',
        messages: [],
        timestamp: new Date().toISOString(),
      };
      state.sessions.unshift(newSession);
      state.activeSessionId = newSession.id;
      state.messages = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => { state.isLoading = true; state.error = null; })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isLoading = false;
        const { userMessage, assistantMessage, sessionId } = action.payload;
        state.messages.push(userMessage);
        state.messages.push(assistantMessage);
        const session = state.sessions.find((s) => s.id === sessionId);
        if (session) {
          if (!session.messages) session.messages = [];
          session.messages.push(userMessage);
          session.messages.push(assistantMessage);
        }
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Failed to send message');
      })
      .addCase(fetchSessions.fulfilled, (state, action) => {
        state.sessions = action.payload;
      })
      .addCase(fetchSession.fulfilled, (state, action) => {
        state.messages = action.payload.messages || [];
      })
      .addCase(deleteSession.fulfilled, (state, action) => {
        state.sessions = state.sessions.filter((s) => s.id !== action.payload);
        if (state.activeSessionId === action.payload) {
          state.activeSessionId = state.sessions[0]?.id || null;
          state.messages = state.sessions[0]?.messages || [];
        }
      });
  },
});

export const { setActiveSession, addMessage, createSession } = chatSlice.actions;
export default chatSlice.reducer;