import React from 'react';
import { Navigate } from 'react-router-dom';
import PropTypes from 'prop-types';

import { useAuth } from '../hooks/useAuth';
import { ROUTES } from './RouteConstants';
import { Loading } from '../components/common/Loading';

/**
 * PublicRoute Component
 * Wraps public routes (login, register, etc.)
 * Redirects to dashboard if already authenticated
 */
export const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading while checking authentication
  if (isLoading) {
    return <Loading fullScreen message="Checking authentication..." />;
  }

  // Redirect to dashboard if already authenticated
  if (isAuthenticated) {
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  // Render children if not authenticated
  return children;
};

PublicRoute.propTypes = {
  children: PropTypes.node.isRequired,
};