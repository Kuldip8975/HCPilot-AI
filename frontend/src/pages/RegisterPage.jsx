import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Eye, EyeOff, Stethoscope, Briefcase } from 'lucide-react';

import { register } from '../redux/slices/authSlice';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import HcPilotLogo from '../components/HcPilotLogo';
import { ROUTES } from '../routes/RouteConstants';
import styles from './RegisterPage.module.css';

export const RegisterPage = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    fullName: '',
    role: 'sales_rep',
    specialty: '',
    organization: '',
    address: '',
    phone: '',
  });
  const [errors, setErrors] = useState({});

  const isDoctor = formData.role === 'doctor';

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const selectRole = (role) => {
    setFormData(prev => ({ ...prev, role }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.fullName) newErrors.fullName = 'Full name is required';
    if (!formData.email) newErrors.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Please enter a valid email';
    if (!formData.password) newErrors.password = 'Password is required';
    else if (formData.password.length < 6) newErrors.password = 'Password must be at least 6 characters';
    if (isDoctor && !formData.specialty) newErrors.specialty = 'Specialty is required for doctor accounts';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsLoading(true);
    try {
      const result = await dispatch(register(formData)).unwrap();
      if (result) {
        navigate(result.user?.role === 'doctor' ? ROUTES.DOCTOR_DASHBOARD : ROUTES.DASHBOARD);
      }
    } catch (error) {
      setErrors({ submit: error || 'Registration failed. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.registerPage}>
      <div className={styles.registerContainer}>
        <div className={styles.registerCard}>
          {/* Brand header — HcPilot AI */}
          <div className={styles.logo}>
            <HcPilotLogo size={36} variant="light" />
            <div className={styles.logoText}>
              <span className={styles.logoTitle}>HcPilot AI</span>
              <span className={styles.logoSubtitle}>Healthcare CRM</span>
            </div>
          </div>

          <h1 className={styles.welcomeTitle}>Create account</h1>
          <p className={styles.welcomeSubtitle}>Sign up to get started</p>

          {/* Role toggle - who is signing up */}
          <div className={styles.roleToggle}>
            <button
              type="button"
              className={`${styles.roleOption} ${!isDoctor ? styles.roleOptionActive : ''}`}
              onClick={() => selectRole('sales_rep')}
            >
              <Briefcase size={16} />
              Medical Rep
            </button>
            <button
              type="button"
              className={`${styles.roleOption} ${isDoctor ? styles.roleOptionActive : ''}`}
              onClick={() => selectRole('doctor')}
            >
              <Stethoscope size={16} />
              Doctor
            </button>
          </div>

          <form onSubmit={handleSubmit} className={styles.form}>
            <Input
              label="Full Name"
              name="fullName"
              type="text"
              placeholder={isDoctor ? 'Dr. Sarah Chen' : 'Enter your full name'}
              value={formData.fullName}
              onChange={handleChange}
              error={errors.fullName}
              required
            />

            <Input
              label="Email Address"
              name="email"
              type="email"
              placeholder="you@company.com"
              value={formData.email}
              onChange={handleChange}
              error={errors.email}
              required
            />

            {isDoctor && (
              <>
                <p className={styles.doctorFieldsHint}>
                  If a rep has already added you to the CRM with this same
                  email, your account will link to that existing profile
                  automatically.
                </p>
                <Input
                  label="Specialty"
                  name="specialty"
                  type="text"
                  placeholder="e.g. Oncology"
                  value={formData.specialty}
                  onChange={handleChange}
                  error={errors.specialty}
                  required
                />
                <Input
                  label="Hospital / Clinic"
                  name="organization"
                  type="text"
                  placeholder="e.g. City General Hospital"
                  value={formData.organization}
                  onChange={handleChange}
                />
              </>
            )}

            <Input
              label="Address"
              name="address"
              type="text"
              placeholder="e.g. FC Road, Pune"
              value={formData.address}
              onChange={handleChange}
            />
            <p className={styles.doctorFieldsHint}>
              {isDoctor
                ? "Becomes your clinic/hospital address on your HCP profile - auto-geocoded so reps can route to you."
                : 'Used as your base location for the Smart Day Planner when live GPS is off - auto-geocoded, never shown as raw coordinates.'}
            </p>

            <Input
              label="Phone (optional)"
              name="phone"
              type="tel"
              placeholder="e.g. +91 98765 43210"
              value={formData.phone}
              onChange={handleChange}
            />

            <div className={styles.passwordWrapper}>
              <Input
                label="Password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Min 6 characters"
                value={formData.password}
                onChange={handleChange}
                error={errors.password}
                required
              />
              <button
                type="button"
                className={styles.passwordToggle}
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>

            {errors.submit && (
              <div className={styles.submitError}>{errors.submit}</div>
            )}

            <Button
              type="submit"
              fullWidth
              size="small"
              isLoading={isLoading}
            >
              Create Account
            </Button>
          </form>

          <p className={styles.loginLink}>
            Already have an account? <Link to={ROUTES.LOGIN}>Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;