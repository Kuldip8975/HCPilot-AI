import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { toast } from 'react-toastify';
import { hcpService } from '../../services/hcpService';

export const fetchHCPs = createAsyncThunk(
  'hcps/fetchAll',
  async (filters, { rejectWithValue }) => {
    try {
      const response = await hcpService.getHCPs(filters);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch HCPs');
    }
  }
);

export const fetchHCPById = createAsyncThunk(
  'hcps/fetchById',
  async (id, { rejectWithValue }) => {
    try {
      const response = await hcpService.getHCPById(id);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch HCP');
    }
  }
);

export const createHCP = createAsyncThunk(
  'hcps/create',
  async (data, { rejectWithValue }) => {
    try {
      const response = await hcpService.createHCP(data);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to create HCP');
    }
  }
);

export const updateHCP = createAsyncThunk(
  'hcps/update',
  async ({ id, data }, { rejectWithValue }) => {
    try {
      const response = await hcpService.updateHCP(id, data);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to update HCP');
    }
  }
);

export const deleteHCP = createAsyncThunk(
  'hcps/delete',
  async (id, { rejectWithValue }) => {
    try {
      const response = await hcpService.deleteHCP(id);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to delete HCP');
    }
  }
);

const initialState = {
  hcps: [],
  currentHCP: null,
  isLoading: false,
  error: null,
  searchQuery: '',
  filters: { specialty: [], status: [], location: '' },
  pagination: { page: 1, limit: 20, total: 0 },
};

const hcpSlice = createSlice({
  name: 'hcps',
  initialState,
  reducers: {
    setCurrentHCP: (state, action) => { state.currentHCP = action.payload; },
    clearCurrentHCP: (state) => { state.currentHCP = null; },
    setSearchQuery: (state, action) => { state.searchQuery = action.payload; },
    setHCPFilters: (state, action) => { state.filters = { ...state.filters, ...action.payload }; },
    clearHCPFilters: (state) => { state.filters = { specialty: [], status: [], location: '' }; },
    setHCPPagination: (state, action) => { state.pagination = { ...state.pagination, ...action.payload }; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHCPs.pending, (state) => { state.isLoading = true; state.error = null; })
      .addCase(fetchHCPs.fulfilled, (state, action) => {
        state.isLoading = false;
        state.hcps = action.payload.items || [];
        state.pagination.total = action.payload.total || 0;
      })
      .addCase(fetchHCPs.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Failed to fetch HCPs');
      })
      .addCase(fetchHCPById.pending, (state) => { state.isLoading = true; state.error = null; })
      .addCase(fetchHCPById.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentHCP = action.payload;
      })
      .addCase(fetchHCPById.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Failed to fetch HCP');
      })
      .addCase(createHCP.pending, (state) => { state.isLoading = true; })
      .addCase(createHCP.fulfilled, (state, action) => {
        state.isLoading = false;
        state.hcps.unshift(action.payload);
        toast.success('HCP created successfully!');
      })
      .addCase(createHCP.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Failed to create HCP');
      })
      .addCase(updateHCP.pending, (state) => { state.isLoading = true; })
      .addCase(updateHCP.fulfilled, (state, action) => {
        state.isLoading = false;
        const index = state.hcps.findIndex((h) => h.id === action.payload.id);
        if (index !== -1) state.hcps[index] = action.payload;
        toast.success('HCP updated successfully!');
      })
      .addCase(updateHCP.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        toast.error(action.payload || 'Failed to update HCP');
      })
      .addCase(deleteHCP.fulfilled, (state, action) => {
        state.hcps = state.hcps.filter((h) => h.id !== action.payload);
        toast.success('HCP deleted successfully!');
      })
      .addCase(deleteHCP.rejected, (state, action) => {
        state.error = action.payload;
        toast.error(action.payload || 'Failed to delete HCP');
      });
  },
});

export const selectHCPs = (state) => state.hcps.hcps;
export const selectCurrentHCP = (state) => state.hcps.currentHCP;
export const selectHCPsLoading = (state) => state.hcps.isLoading;

export const { setCurrentHCP, clearCurrentHCP, setSearchQuery, setHCPFilters, clearHCPFilters, setHCPPagination } = hcpSlice.actions;
export default hcpSlice.reducer;