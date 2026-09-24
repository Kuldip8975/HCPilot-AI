import React from 'react';
import { LoginForm } from '../components/auth/LoginForm';
import HcPilotLogo from '../components/HcPilotLogo';
import styles from './LoginPage.module.css';

export const LoginPage = () => {
  return (
    <div className={styles.loginPage}>
      {/* Decorative background blobs */}
      <div className={styles.bgBlobTop} aria-hidden="true" />
      <div className={styles.bgBlobBottom} aria-hidden="true" />

      <div className={styles.loginContainer}>
        <div className={styles.loginCard}>
          {/* Brand header */}
          <div className={styles.logo}>
            <HcPilotLogo size={28} variant="light" />
            <div className={styles.logoText}>
              <span className={styles.logoTitle}>HcPilot AI</span>
              <span className={styles.logoSubtitle}>Healthcare CRM</span>
            </div>
          </div>

          {/* Welcome text */}
          <div className={styles.welcomeBlock}>
            
          </div>

          {/* Form (uses its own LoginForm.module.css) */}
          <LoginForm />

        </div>

        {/* Page footer */}
        <p className={styles.pageFooter}>
          © {new Date().getFullYear()} HcPilot AI
        </p>
      </div>
    </div>
  );
};

export default LoginPage;