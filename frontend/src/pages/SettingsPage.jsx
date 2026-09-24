import React, { useState } from 'react';
import { 
  User, 
  Bell, 
  Shield, 
  Palette, 
  Globe, 
  Key,
  ChevronRight,
  Moon,
  Sun
} from 'lucide-react';

import styles from './SettingsPage.module.css';

/**
 * SettingsPage Component
 * User settings and preferences page
 */
export const SettingsPage = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [notifications, setNotifications] = useState(true);

  const settingsSections = [
    {
      id: 'profile',
      icon: User,
      title: 'Profile',
      description: 'Manage your personal information',
      onClick: () => console.log('Navigate to profile'),
    },
    {
      id: 'notifications',
      icon: Bell,
      title: 'Notifications',
      description: 'Configure notification preferences',
      onClick: () => console.log('Navigate to notifications'),
    },
    {
      id: 'security',
      icon: Shield,
      title: 'Security',
      description: 'Password and security settings',
      onClick: () => console.log('Navigate to security'),
    },
    {
      id: 'appearance',
      icon: Palette,
      title: 'Appearance',
      description: 'Theme and display settings',
      onClick: () => console.log('Navigate to appearance'),
    },
    {
      id: 'language',
      icon: Globe,
      title: 'Language',
      description: 'Language preferences',
      onClick: () => console.log('Navigate to language'),
    },
    {
      id: 'api',
      icon: Key,
      title: 'API Keys',
      description: 'Manage your API keys',
      onClick: () => console.log('Navigate to API keys'),
    },
  ];

  return (
    <div className={styles.settingsPage}>
      <div className={styles.header}>
        <h1 className={styles.title}>Settings</h1>
        <p className={styles.subtitle}>Manage your account preferences</p>
      </div>

      <div className={styles.settingsGrid}>
        {/* Settings Sections */}
        <div className={styles.settingsList}>
          {settingsSections.map((section) => (
            <button
              key={section.id}
              className={styles.settingsItem}
              onClick={section.onClick}
            >
              <div className={styles.settingsItemLeft}>
                <div className={styles.settingsIcon}>
                  <section.icon size={20} />
                </div>
                <div className={styles.settingsItemInfo}>
                  <div className={styles.settingsItemTitle}>{section.title}</div>
                  <div className={styles.settingsItemDescription}>{section.description}</div>
                </div>
              </div>
              <ChevronRight size={18} className={styles.settingsItemArrow} />
            </button>
          ))}
        </div>

        {/* Quick Settings */}
        <div className={styles.quickSettings}>
          <h3 className={styles.quickSettingsTitle}>Quick Settings</h3>
          
          <div className={styles.quickSettingItem}>
            <div className={styles.quickSettingInfo}>
              <span className={styles.quickSettingLabel}>Dark Mode</span>
              <span className={styles.quickSettingDescription}>Toggle dark theme</span>
            </div>
            <button
              className={`${styles.toggleButton} ${darkMode ? styles.active : ''}`}
              onClick={() => setDarkMode(!darkMode)}
            >
              <div className={styles.toggleThumb}>
                {darkMode ? <Moon size={14} /> : <Sun size={14} />}
              </div>
            </button>
          </div>

          <div className={styles.quickSettingItem}>
            <div className={styles.quickSettingInfo}>
              <span className={styles.quickSettingLabel}>Notifications</span>
              <span className={styles.quickSettingDescription}>Email and in-app notifications</span>
            </div>
            <button
              className={`${styles.toggleButton} ${notifications ? styles.active : ''}`}
              onClick={() => setNotifications(!notifications)}
            >
              <div className={styles.toggleThumb}>
                {notifications ? '✓' : '✕'}
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;