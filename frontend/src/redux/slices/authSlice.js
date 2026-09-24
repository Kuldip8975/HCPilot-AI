import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { toast } from 'react-toastify';
import { authService } from '../../services/authService';

// Async thunk for login
export const login = createAsyncThunk(
  'auth/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await authService.login(credentials);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Login failed');
    }
  }
);

// Async thunk for register
export const register = createAsyncThunk(
  'auth/register',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await authService.register(userData);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Registration failed');
    }
  }
);

// Async thunk for logout
export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout();
      return true;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Logout failed');
    }
  }
);

// Async thunk for getting current user
// In authSlice.js, update the fetchCurrentUser thunk:

export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem('authToken');
      if (!token) {
        throw new Error('No token found');
      }
      const response = await authService.getCurrentUser();
      return response;
    } catch (error) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch user');
    }
  }
);

const initialState = {
  user: null,
  token: localStorage.getItem('authToken') || null,
  refreshToken: localStorage.getItem('refreshToken') || null,
  isAuthenticated: !!localStorage.getItem('authToken'),
  isLoading: false,
  error: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setCredentials: (state, action) => {
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
      state.isAuthenticated = true;
      localStorage.setItem('authToken', action.payload.token);
      localStorage.setItem('refreshToken', action.payload.refreshToken);
    },
    clearCredentials: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.access_token;
        state.refreshToken = action.payload.refresh_token;
        state.isAuthenticated = true;
        toast.success('Login successful!');
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Login failed');
      })
      // Register
      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.access_token;
        state.refreshToken = action.payload.refresh_token;
        state.isAuthenticated = true;
        toast.success('Registration successful!');
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Registration failed');
      })
      // Logout
      .addCase(logout.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(logout.fulfilled, (state) => {
        state.isLoading = false;
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        toast.info('Logged out successfully');
      })
      .addCase(logout.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        // Still clear credentials even if logout fails
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
      })
      // Fetch Current User
      .addCase(fetchCurrentUser.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(fetchCurrentUser.rejected, (state) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
      });
  },
});

// Selectors
export const selectUser = (state) => state.auth.user;
export const selectToken = (state) => state.auth.token;
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated;
export const selectIsLoading = (state) => state.auth.isLoading;
export const selectAuthError = (state) => state.auth.error;

export const { clearError, setCredentials, clearCredentials } = authSlice.actions;
export default authSlice.reducer;