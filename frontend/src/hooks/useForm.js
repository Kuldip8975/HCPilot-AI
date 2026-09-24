import { useState, useCallback } from 'react';

/**
 * useForm Hook
 * Manages form state, validation, and submission
 */
export const useForm = (initialValues, validate, onSubmit) => {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [touched, setTouched] = useState({});

  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    const val = type === 'checkbox' ? checked : value;
    
    setValues(prev => ({ ...prev, [name]: val }));
    setTouched(prev => ({ ...prev, [name]: true }));
    
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  }, [errors]);

  const handleBlur = useCallback((e) => {
    const { name } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));
    
    if (validate) {
      const fieldError = validate(name, values[name]);
      if (fieldError) {
        setErrors(prev => ({ ...prev, [name]: fieldError }));
      }
    }
  }, [validate, values]);

  const handleSubmit = useCallback(async (e) => {
    e?.preventDefault();
    
    if (validate) {
      const validationErrors = validate(values);
      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors);
        // Mark all fields as touched
        const allTouched = {};
        Object.keys(values).forEach(key => {
          allTouched[key] = true;
        });
        setTouched(allTouched);
        return;
      }
    }
    
    setIsSubmitting(true);
    try {
      await onSubmit(values);
    } catch (error) {
      setErrors({ submit: error.message || 'Submission failed' });
    } finally {
      setIsSubmitting(false);
    }
  }, [values, validate, onSubmit]);

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
  }, [initialValues]);

  const setFieldValue = useCallback((name, value) => {
    setValues(prev => ({ ...prev, [name]: value }));
  }, []);

  const setFieldError = useCallback((name, error) => {
    setErrors(prev => ({ ...prev, [name]: error }));
  }, []);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    reset,
    setFieldValue,
    setFieldError,
    setValues,
  };
};

export default useForm;