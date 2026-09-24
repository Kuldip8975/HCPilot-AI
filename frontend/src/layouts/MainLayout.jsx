import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';

import { Sidebar } from '../components/layout/Sidebar';
import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';

import styles from './MainLayout.module.css';

const isDesktop = () =>
  typeof window !== 'undefined' && window.innerWidth > 960;

export const MainLayout = () => {
  // On mobile, sidebar starts closed. On desktop, it starts open.
  const [sidebarOpen, setSidebarOpen] = useState(isDesktop());

  const toggleSidebar = () => setSidebarOpen((prev) => !prev);

  // Auto-close sidebar when resizing down to mobile
  // Auto-open sidebar when resizing back to desktop
  useEffect(() => {
    const handleResize = () => {
      setSidebarOpen(isDesktop());
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className={styles.mainLayout}>
      <Sidebar isOpen={sidebarOpen} onToggle={toggleSidebar} />

      <div
        className={`${styles.mainContent} ${
          sidebarOpen ? styles.sidebarOpen : styles.sidebarClosed
        }`}
      >
        <Header onMenuClick={toggleSidebar} />

        <main className={styles.contentArea}>
          <div className={styles.contentWrapper}>
            <Outlet />
          </div>
        </main>

        <Footer />
      </div>
    </div>
  );
};

export default MainLayout;