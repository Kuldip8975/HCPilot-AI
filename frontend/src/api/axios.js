import axios from 'axios';
import { API_CONFIG } from '../config';
import {
  requestInterceptor,
  requestErrorHandler,
  responseSuccessHandler,
  responseErrorHandler,
} from './interceptors';

// Create Axios instance
const axiosInstance = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Store reference for interceptors
axiosInstance.__REDUX_STORE__ = null;

// Setup interceptors
axiosInstance.interceptors.request.use(requestInterceptor, requestErrorHandler);
axiosInstance.interceptors.response.use(responseSuccessHandler, responseErrorHandler);

export default axiosInstance;