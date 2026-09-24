import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Eye, EyeOff } from 'lucide-react';

import { login, clearError, selectIsLoading, selectAuthError } from '../../redux/slices/authSlice';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { ROUTES } from '../../routes/RouteConstants';
import styles from './LoginForm.module.css';

export const LoginForm = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const isLoading = useSelector(selectIsLoading);
  const authError = useSelector(selectAuthError);

  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.email) newErrors.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Please enter a valid email';
    if (!formData.password) newErrors.password = 'Password is required';
    else if (formData.password.length < 6) newErrors.password = 'Password must be at least 6 characters';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    const result = await dispatch(login(formData));
    if (result.meta.requestStatus === 'fulfilled') {
      // Doctors go to their own dashboard (their scheduled follow-ups);
      // sales reps go to the normal CRM dashboard.
      const role = result.payload?.user?.role;
      navigate(role === 'doctor' ? ROUTES.DOCTOR_DASHBOARD : ROUTES.DASHBOARD);
    }
  };

  return (
    <div className={styles.loginFormWrapper}>
      <h1 className={styles.welcomeTitle}>Welcome Back</h1>
      <p className={styles.welcomeSubtitle}>Sign in to your account to continue</p>

      <form onSubmit={handleSubmit} className={styles.form}>
        <Input
          label="Email Address"
          name="email"
          type="email"
          placeholder="Enter your email"
          value={formData.email}
          onChange={handleChange}
          error={errors.email}
          required
        />

        <div className={styles.passwordWrapper}>
          <Input
            label="Password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Enter your password"
            value={formData.password}
            onChange={handleChange}
            error={errors.password}
            required
          />
          <button
            type="button"
            className={styles.passwordToggle}
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>

        <div className={styles.formOptions}>
          <label className={styles.rememberMe}>
            <input type="checkbox" />
            Remember me
          </label>
          <Link to="/forgot-password" className={styles.forgotPassword}>
            Forgot password?
          </Link>
        </div>

        {authError && (
          <div className={styles.submitError}>{authError}</div>
        )}

        <Button
          type="submit"
          fullWidth
          size="large"
          isLoading={isLoading}
        >
          Sign In
        </Button>
      </form>

      <p className={styles.registerLink}>
        Don't have an account? <Link to="/register">Sign up</Link>
      </p>
    </div>
  );
};

export default LoginForm;