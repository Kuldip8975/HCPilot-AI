import axiosInstance from '../api/axios';
import { ENDPOINTS } from '../api/endpoints';

export const authService = {
  login: async (credentials) => {
    try {
      const response = await axiosInstance.post(ENDPOINTS.AUTH.LOGIN, {
        email: credentials.email,
        password: credentials.password,
      });

      if (response.access_token) {
        localStorage.setItem('authToken', response.access_token);
        localStorage.setItem('refreshToken', response.refresh_token);
      }

      return response;
    } catch (error) {
      throw error;
    }
  },

  register: async (userData) => {
    try {
      const response = await axiosInstance.post(ENDPOINTS.AUTH.REGISTER, {
        email: userData.email,
        password: userData.password,
        full_name: userData.fullName,
        role: userData.role || 'sales_rep',
        // Only meaningful when role === 'doctor' - the backend ignores
        // these for a sales_rep signup, but there's no harm sending them
        // (they'll just be undefined/omitted for a rep).
        specialty: userData.specialty || undefined,
        organization: userData.organization || undefined,
        // Backend's UserCreate schema (backend/app/schemas/auth.py) calls
        // this field "address", not "location" - sending "location" here
        // meant it was silently dropped as an unrecognized field, so
        // NEITHER role ever got their address geocoded at signup. Used by
        // both roles: a doctor's HCP profile address, or a sales_rep's
        // own base-location fallback for the Smart Day Planner.
        address: userData.address || undefined,
        phone: userData.phone || undefined,
      });

      if (response.access_token) {
        localStorage.setItem('authToken', response.access_token);
        localStorage.setItem('refreshToken', response.refresh_token);
      }

      return response;
    } catch (error) {
      throw error;
    }
  },

  logout: async () => {
    try {
      const response = await axiosInstance.post(ENDPOINTS.AUTH.LOGOUT);
      return response;
    } catch (error) {
      throw error;
    } finally {
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
    }
  },

  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await axiosInstance.post(ENDPOINTS.AUTH.REFRESH, {
        refresh_token: refreshToken,
      });

      if (response.access_token) {
        localStorage.setItem('authToken', response.access_token);
        if (response.refresh_token) {
          localStorage.setItem('refreshToken', response.refresh_token);
        }
      }

      return response;
    } catch (error) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
      throw error;
    }
  },

  getCurrentUser: async () => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.AUTH.ME);
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Request a password-reset OTP. Backend has no email service wired up,
   * so the OTP comes back directly in this response (demo-scope decision,
   * documented on the backend) - the caller is responsible for showing it
   * on-screen with a countdown, not silently trusting an email was sent.
   * Returns { otp, expires_in_seconds }.
   */
  forgotPassword: async (email) => {
    try {
      const response = await axiosInstance.post(ENDPOINTS.AUTH.FORGOT_PASSWORD, { email });
      return response;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Complete the reset using the OTP shown on-screen from forgotPassword().
   */
  resetPassword: async ({ email, otp, newPassword, confirmPassword }) => {
    try {
      const response = await axiosInstance.post(ENDPOINTS.AUTH.RESET_PASSWORD, {
        email,
        otp,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      return response;
    } catch (error) {
      throw error;
    }
  },
};