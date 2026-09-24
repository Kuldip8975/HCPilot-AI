import React from 'react';
import PropTypes from 'prop-types';
import clsx from 'clsx';

import styles from './Loading.module.css';

/**
 * Loading Component
 * Reusable loading spinner with optional message and full-screen mode
 */
export const Loading = ({
  message,
  fullScreen = false,
  size = 'medium',
  className,
  ...props
}) => {
  const sizeMap = {
    small: 24,
    medium: 40,
    large: 56,
  };

  const spinnerSize = sizeMap[size] || sizeMap.medium;

  return (
    <div
      className={clsx(
        styles.loadingContainer,
        {
          [styles.fullScreen]: fullScreen,
        },
        className
      )}
      {...props}
    >
      <div className={styles.spinnerWrapper}>
        <div
          className={styles.spinner}
          style={{
            width: spinnerSize,
            height: spinnerSize,
          }}
        />
        {message && <p className={styles.message}>{message}</p>}
      </div>
    </div>
  );
};

Loading.propTypes = {
  message: PropTypes.string,
  fullScreen: PropTypes.bool,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  className: PropTypes.string,
};

export default Loading;