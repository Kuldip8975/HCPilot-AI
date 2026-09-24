import { useSelector, useDispatch } from 'react-redux';
import { useMemo } from 'react';

import {
  selectIsAuthenticated,
  selectIsLoading,
  selectUser,
  selectToken,
  selectAuthError,
  login,
  logout,
  register,
  fetchCurrentUser,
  clearError,
} from '../redux/slices/authSlice';

export const useAuth = () => {
  const dispatch = useDispatch();
  
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const isLoading = useSelector(selectIsLoading);
  const user = useSelector(selectUser);
  const token = useSelector(selectToken);
  const error = useSelector(selectAuthError);

  const authActions = useMemo(
    () => ({
      login: (credentials) => dispatch(login(credentials)),
      logout: () => dispatch(logout()),
      register: (userData) => dispatch(register(userData)),
      fetchCurrentUser: () => dispatch(fetchCurrentUser()),
      clearError: () => dispatch(clearError()),
    }),
    [dispatch]
  );

  return {
    isAuthenticated,
    isLoading,
    user,
    token,
    error,
    ...authActions,
  };
};

export default useAuth;