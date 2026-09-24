import React, { forwardRef } from 'react';
import PropTypes from 'prop-types';
import clsx from 'clsx';

import styles from './Input.module.css';

/**
 * Input Component
 * Reusable input with label, error, and various input types
 */
export const Input = forwardRef(({
  label,
  name,
  type = 'text',
  placeholder,
  value,
  onChange,
  onBlur,
  error,
  required = false,
  disabled = false,
  className,
  inputClassName,
  ...props
}, ref) => {
  const inputClasses = clsx(
    styles.input,
    {
      [styles.error]: error,
      [styles.disabled]: disabled,
    },
    inputClassName
  );

  return (
    <div className={clsx(styles.inputGroup, className)}>
      {label && (
        <label htmlFor={name} className={styles.label}>
          {label}
          {required && <span className={styles.required}>*</span>}
        </label>
      )}
      <input
        ref={ref}
        id={name}
        name={name}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        disabled={disabled}
        className={inputClasses}
        {...props}
      />
      {error && <span className={styles.errorMessage}>{error}</span>}
    </div>
  );
});

Input.displayName = 'Input';

Input.propTypes = {
  label: PropTypes.string,
  name: PropTypes.string.isRequired,
  type: PropTypes.string,
  placeholder: PropTypes.string,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onChange: PropTypes.func,
  onBlur: PropTypes.func,
  error: PropTypes.string,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  className: PropTypes.string,
  inputClassName: PropTypes.string,
};

export default Input;