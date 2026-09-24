import React from 'react';
import styles from './Footer.module.css';

/**
 * Footer Component
 * Displays copyright and version information at the bottom of the page
 */
export const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className={styles.footer}>
      <div className={styles.footerContent}>
        <span className={styles.copyright}>
          &copy; {currentYear} Naukri CRM. All rights reserved.
        </span>
        <span className={styles.version}>
          v1.0.0
        </span>
      </div>
    </footer>
  );
};

export default Footer;