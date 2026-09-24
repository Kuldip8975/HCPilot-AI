import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';

import { useAuth } from '../hooks/useAuth';
import { ROUTES } from './RouteConstants';
import { Loading } from '../components/common/Loading';

export const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading, fetchCurrentUser, token } = useAuth();
  const location = useLocation();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const validateAuth = async () => {
      // Check if token exists in localStorage
      const localToken = localStorage.getItem('authToken');
      
      if (!localToken) {
        setChecking(false);
        return;
      }
      
      try {
        await fetchCurrentUser();
      } catch (error) {
        console.error('Auth validation failed:', error);
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
      } finally {
        setChecking(false);
      }
    };
    
    validateAuth();
  }, [fetchCurrentUser]);

  if (isLoading || checking) {
    return <Loading fullScreen message="Checking authentication..." />;
  }

  // Check both Redux state and localStorage
  const authenticated = isAuthenticated || !!localStorage.getItem('authToken');

  if (!authenticated) {
    return <Navigate to={ROUTES.LOGIN} state={{ from: location }} replace />;
  }

  return children;
};

ProtectedRoute.propTypes = {
  children: PropTypes.node.isRequired,
};

export default ProtectedRoute;