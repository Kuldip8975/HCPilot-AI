import React from 'react';
import PropTypes from 'prop-types';
import { Loader } from 'lucide-react';
import clsx from 'clsx';

import styles from './Button.module.css';

/**
 * Button Component
 * Reusable button with multiple variants, sizes, and loading state
 */
export const Button = ({
  children,
  variant = 'primary',
  size = 'medium',
  type = 'button',
  isLoading = false,
  disabled = false,
  fullWidth = false,
  onClick,
  className,
  ...props
}) => {
  const buttonClasses = clsx(
    styles.button,
    styles[variant],
    styles[size],
    {
      [styles.fullWidth]: fullWidth,
      [styles.loading]: isLoading,
      [styles.disabled]: disabled || isLoading,
    },
    className
  );

  return (
    <button
      type={type}
      className={buttonClasses}
      onClick={onClick}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader size={18} className={styles.spinner} />}
      <span className={styles.content}>{children}</span>
    </button>
  );
};

Button.propTypes = {
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf([
    'primary',
    'secondary',
    'success',
    'danger',
    'warning',
    'outline',
    'ghost',
  ]),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  type: PropTypes.oneOf(['button', 'submit', 'reset']),
  isLoading: PropTypes.bool,
  disabled: PropTypes.bool,
  fullWidth: PropTypes.bool,
  onClick: PropTypes.func,
  className: PropTypes.string,
};

export default Button;