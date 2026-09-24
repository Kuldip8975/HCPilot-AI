import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  PlusCircle, 
  History, 
  Users, 
  BarChart3, 
  MessageSquare,
  ClipboardList
} from 'lucide-react';

import { ROUTES } from '../../routes/RouteConstants';
import styles from './QuickActions.module.css';

/**
 * QuickActions Component
 * Displays quick action buttons for common tasks
 */
export const QuickActions = () => {
  const navigate = useNavigate();

  const actions = [
    {
      id: 'log-interaction',
      label: 'Log Interaction',
      icon: PlusCircle,
      color: '#2563eb',
      bgColor: 'rgba(37, 99, 235, 0.1)',
      onClick: () => navigate(ROUTES.INTERACTION_NEW),
    },
    {
      id: 'view-history',
      label: 'View History',
      icon: History,
      color: '#7c3aed',
      bgColor: 'rgba(124, 58, 237, 0.1)',
      onClick: () => navigate(ROUTES.INTERACTION_HISTORY),
    },
    {
      id: 'manage-hcps',
      label: 'Manage HCPs',
      icon: Users,
      color: '#f59e0b',
      bgColor: 'rgba(245, 158, 11, 0.1)',
      onClick: () => navigate(ROUTES.HCPS),
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: BarChart3,
      color: '#22c55e',
      bgColor: 'rgba(34, 197, 94, 0.1)',
      onClick: () => navigate(ROUTES.ANALYTICS),
    },
    {
      id: 'ai-chat',
      label: 'AI Chat',
      icon: MessageSquare,
      color: '#06b6d4',
      bgColor: 'rgba(6, 182, 212, 0.1)',
      onClick: () => navigate(ROUTES.CHAT),
    },
    {
      id: 'interactions',
      label: 'All Interactions',
      icon: ClipboardList,
      color: '#64748b',
      bgColor: 'rgba(100, 116, 139, 0.1)',
      onClick: () => navigate(ROUTES.INTERACTIONS),
    },
  ];

  return (
    <div className={styles.quickActions}>
      <h3 className={styles.title}>Quick Actions</h3>
      <div className={styles.actionsGrid}>
        {actions.map((action) => (
          <button
            key={action.id}
            className={styles.actionButton}
            onClick={action.onClick}
          >
            <div 
              className={styles.actionIcon} 
              style={{ 
                color: action.color, 
                backgroundColor: action.bgColor 
              }}
            >
              <action.icon size={20} />
            </div>
            <span className={styles.actionLabel}>{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuickActions;