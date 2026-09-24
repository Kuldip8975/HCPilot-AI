import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { KeyRound, ArrowLeft, RefreshCw } from 'lucide-react';
import { toast } from 'react-toastify';

import { authService } from '../services/authService';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { ROUTES } from '../routes/RouteConstants';
import styles from './ForgotPasswordPage.module.css';

const OTP_VALIDITY_SECONDS = 50;

/**
 * Forgot Password - OTP flow.
 *
 * Scope note: this project has no email-sending service configured, so
 * the backend returns the OTP directly in the /forgot-password response
 * instead of emailing it - this page shows it on-screen with a countdown
 * instead of a real inbox. That's a deliberate, disclosed demo-scope
 * decision (see backend/app/services/auth_service.py), not a bug.
 *
 * Everything - email, new password, confirm password, and the OTP field -
 * lives on this one page/form, matching how the request was described.
 */
export const ForgotPasswordPage = () => {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [otpInput, setOtpInput] = useState('');

  const [displayedOtp, setDisplayedOtp] = useState(null);
  const [secondsLeft, setSecondsLeft] = useState(0);

  const [isRequestingOtp, setIsRequestingOtp] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [errors, setErrors] = useState({});

  const timerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const startCountdown = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    setSecondsLeft(OTP_VALIDITY_SECONDS);
    timerRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          setDisplayedOtp(null); // OTP has expired - hide it
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const validateEmail = () => {
    if (!email) {
      setErrors({ email: 'Email is required' });
      return false;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
      setErrors({ email: 'Please enter a valid email' });
      return false;
    }
    setErrors({});
    return true;
  };

  const handleGetVerificationCode = async () => {
    if (!validateEmail()) return;

    setIsRequestingOtp(true);
    try {
      const result = await authService.forgotPassword(email);
      setDisplayedOtp(result?.otp || null);
      setOtpInput('');
      startCountdown();
      toast.success('Verification code generated - it stays valid for 50 seconds.');
    } catch (error) {
      const message = error?.response?.data?.detail || 'Failed to generate a verification code.';
      toast.error(typeof message === 'string' ? message : 'Failed to generate a verification code.');
    } finally {
      setIsRequestingOtp(false);
    }
  };

  const validateResetForm = () => {
    const newErrors = {};
    if (!email) newErrors.email = 'Email is required';
    if (!otpInput || otpInput.length !== 6) newErrors.otp = 'Enter the 6-digit code';
    if (!newPassword || newPassword.length < 6) newErrors.newPassword = 'Password must be at least 6 characters';
    if (confirmPassword !== newPassword) newErrors.confirmPassword = 'Passwords do not match';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!validateResetForm()) return;

    setIsResetting(true);
    try {
      await authService.resetPassword({
        email,
        otp: otpInput,
        newPassword,
        confirmPassword,
      });
      toast.success('Password reset successfully. Please log in with your new password.');
      navigate(ROUTES.LOGIN);
    } catch (error) {
      const message = error?.response?.data?.detail || 'Failed to reset password.';
      toast.error(typeof message === 'string' ? message : 'Failed to reset password.');
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className={styles.pageWrapper}>
      <div className={styles.card}>
        <Link to={ROUTES.LOGIN} className={styles.backLink}>
          <ArrowLeft size={16} />
          Back to login
        </Link>

        <h1 className={styles.title}>
          <KeyRound size={22} className={styles.titleIcon} />
          Reset Your Password
        </h1>
        <p className={styles.subtitle}>
          Enter your email, choose a new password, then generate a verification code to confirm it's you.
        </p>

        <form onSubmit={handleResetPassword} className={styles.form}>
          <Input
            label="Email Address"
            name="email"
            type="email"
            placeholder="Enter your account email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
            required
          />

          <Input
            label="New Password"
            name="newPassword"
            type="password"
            placeholder="At least 6 characters"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            error={errors.newPassword}
            required
          />

          <Input
            label="Confirm New Password"
            name="confirmPassword"
            type="password"
            placeholder="Re-enter new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={errors.confirmPassword}
            required
          />

          <div className={styles.otpSection}>
            <Button
              type="button"
              variant="secondary"
              onClick={handleGetVerificationCode}
              isLoading={isRequestingOtp}
              disabled={isRequestingOtp}
            >
              <RefreshCw size={15} />
              {displayedOtp ? 'Get New Code' : 'Get Verification Code'}
            </Button>

            {displayedOtp && (
              <div className={styles.otpDisplay}>
                <span className={styles.otpValue}>{displayedOtp}</span>
                <span className={styles.otpCountdown}>
                  Valid for {secondsLeft}s
                </span>
              </div>
            )}

            {!displayedOtp && secondsLeft === 0 && otpInput === '' && (
              <p className={styles.otpHint}>
                  </p>
            )}
          </div>

          <Input
            label="Enter Verification Code"
            name="otp"
            type="text"
            placeholder="6-digit code"
            maxLength={6}
            value={otpInput}
            onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, ''))}
            error={errors.otp}
            required
          />

          <Button
            type="submit"
            fullWidth
            size="large"
            isLoading={isResetting}
          >
            Reset Password
          </Button>
        </form>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;