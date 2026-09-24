import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { toast } from 'react-toastify';
import { interactionService } from '../../services/interactionService';

export const fetchInteractions = createAsyncThunk(
  'interactions/fetchAll',
  async (filters, { rejectWithValue }) => {
    try {
      const response = await interactionService.getInteractions(filters);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch interactions');
    }
  }
);

export const fetchInteractionById = createAsyncThunk(
  'interactions/fetchById',
  async (id, { rejectWithValue }) => {
    try {
      const response = await interactionService.getInteractionById(id);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch interaction');
    }
  }
);

export const createInteraction = createAsyncThunk(
  'interactions/create',
  async (data, { rejectWithValue }) => {
    try {
      const response = await interactionService.createInteraction(data);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to create interaction');
    }
  }
);

export const createInteractionWithAI = createAsyncThunk(
  'interactions/createWithAI',
  async ({ description, hcpId, context }, { rejectWithValue }) => {
    try {
      const response = await interactionService.createInteractionWithAI(description, hcpId, context);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'AI processing failed');
    }
  }
);

export const updateInteraction = createAsyncThunk(
  'interactions/update',
  async ({ id, data }, { rejectWithValue }) => {
    try {
      const response = await interactionService.updateInteraction(id, data);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to update interaction');
    }
  }
);

export const updateInteractionWithAI = createAsyncThunk(
  'interactions/updateWithAI',
  async ({ id, description }, { rejectWithValue }) => {
    try {
      const response = await interactionService.updateInteractionWithAI(id, description);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'AI processing failed');
    }
  }
);

export const deleteInteraction = createAsyncThunk(
  'interactions/delete',
  async (id, { rejectWithValue }) => {
    try {
      const response = await interactionService.deleteInteraction(id);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to delete interaction');
    }
  }
);

const initialState = {
  interactions: [],
  currentInteraction: null,
  isLoading: false,
  error: null,
  filters: {
    hcpId: null,
    type: null,
    dateFrom: null,
    dateTo: null,
    searchQuery: '',
  },
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
  },
};

const interactionSlice = createSlice({
  name: 'interactions',
  initialState,
  reducers: {
    setCurrentInteraction: (state, action) => {
      state.currentInteraction = action.payload;
    },
    clearCurrentInteraction: (state) => {
      state.currentInteraction = null;
    },
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {
        hcpId: null,
        type: null,
        dateFrom: null,
        dateTo: null,
        searchQuery: '',
      };
    },
    setPagination: (state, action) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    resetState: () => initialState,
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.isLoading = false;
        state.interactions = action.payload.items || [];
        state.pagination.total = action.payload.total || 0;
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Failed to fetch interactions');
      })
      .addCase(fetchInteractionById.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchInteractionById.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentInteraction = action.payload;
      })
      .addCase(fetchInteractionById.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Failed to fetch interaction');
      })
      .addCase(createInteraction.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.isLoading = false;
        state.interactions.unshift(action.payload);
        toast.success('Interaction logged successfully!');
      })
      .addCase(createInteraction.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Failed to log interaction');
      })
      .addCase(createInteractionWithAI.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createInteractionWithAI.fulfilled, (state, action) => {
        state.isLoading = false;
        if (action.payload.interaction) {
          state.interactions.unshift(action.payload.interaction);
        }
        toast.success(action.payload.response || 'Interaction logged successfully!');
      })
      .addCase(createInteractionWithAI.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'AI processing failed');
      })
      .addCase(updateInteraction.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        state.isLoading = false;
        const index = state.interactions.findIndex((i) => i.id === action.payload.id);
        if (index !== -1) {
          state.interactions[index] = action.payload;
        }
        toast.success('Interaction updated successfully!');
      })
      .addCase(updateInteraction.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Failed to update interaction');
      })
      .addCase(deleteInteraction.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(deleteInteraction.fulfilled, (state, action) => {
        state.isLoading = false;
        state.interactions = state.interactions.filter((i) => i.id !== action.payload);
        toast.success('Interaction deleted successfully!');
      })
      .addCase(deleteInteraction.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Failed to delete interaction');
      });
  },
});

export const selectInteractions = (state) => state.interactions.interactions;
export const selectCurrentInteraction = (state) => state.interactions.currentInteraction;
export const selectInteractionsLoading = (state) => state.interactions.isLoading;
export const selectInteractionFilters = (state) => state.interactions.filters;
export const selectInteractionPagination = (state) => state.interactions.pagination;

export const {
  setCurrentInteraction,
  clearCurrentInteraction,
  setFilters,
  clearFilters,
  setPagination,
  resetState,
} = interactionSlice.actions;

export default interactionSlice.reducer;