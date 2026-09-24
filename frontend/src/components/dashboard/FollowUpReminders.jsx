import React from 'react';
import PropTypes from 'prop-types';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { ChevronRight, AlertCircle, Clock, CheckCircle2 } from 'lucide-react';

import styles from './FollowUpReminders.module.css';

/**
 * FollowUpReminders Component
 * Shows pending follow-up tasks with priority and due dates
 */
export const FollowUpReminders = ({ reminders, onViewAll }) => {
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return '#ef4444';
      case 'medium':
        return '#f59e0b';
      case 'overdue':
        return '#dc2626';
      default:
        return '#64748b';
    }
  };

  const getPriorityLabel = (priority) => {
    switch (priority) {
      case 'high':
        return 'High Priority';
      case 'medium':
        return 'Medium Priority';
      case 'overdue':
        return 'Overdue';
      default:
        return 'Normal';
    }
  };

  const getPriorityIcon = (priority) => {
    if (priority === 'overdue') {
      return <AlertCircle size={14} />;
    }
    return <Clock size={14} />;
  };

  return (
    <div className={styles.followUps}>
      <div className={styles.header}>
        <h3 className={styles.title}>Follow-up Reminders</h3>
        <button className={styles.viewAll} onClick={onViewAll}>
          View All
          <ChevronRight size={16} />
        </button>
      </div>

      <div className={styles.list}>
        {reminders.length === 0 ? (
          <div className={styles.emptyState}>
            <CheckCircle2 size={40} strokeWidth={1.5} />
            <p>All caught up!</p>
            <p className={styles.emptyStateSub}>No pending follow-ups.</p>
          </div>
        ) : (
          reminders.map((reminder) => (
            <div key={reminder.id} className={styles.reminderItem}>
              <div className={styles.reminderIndicator}>
                <div 
                  className={styles.priorityDot} 
                  style={{ backgroundColor: getPriorityColor(reminder.priority) }}
                />
              </div>
              <div className={styles.reminderContent}>
                <div className={styles.reminderHeader}>
                  <span className={styles.hcpName}>{reminder.hcpName}</span>
                  <span 
                    className={`${styles.priorityBadge} ${
                      reminder.priority === 'overdue' 
                        ? styles.priorityOverdue 
                        : reminder.priority === 'high' 
                        ? styles.priorityHigh 
                        : styles.priorityMedium
                    }`}
                  >
                    {getPriorityIcon(reminder.priority)}
                    {getPriorityLabel(reminder.priority)}
                  </span>
                </div>
                <div className={styles.hcpSpecialty}>{reminder.hcpSpecialty}</div>
                <p className={styles.notes}>{reminder.notes}</p>
                <div className={styles.reminderFooter}>
                  <span className={styles.dueDate}>
                    <Clock size={12} />
                    Due {formatDistanceToNow(parseISO(reminder.dueDate), { addSuffix: true })}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

FollowUpReminders.propTypes = {
  reminders: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      hcpName: PropTypes.string.isRequired,
      hcpSpecialty: PropTypes.string.isRequired,
      dueDate: PropTypes.string.isRequired,
      priority: PropTypes.oneOf(['high', 'medium', 'low', 'overdue']).isRequired,
      notes: PropTypes.string.isRequired,
    })
  ).isRequired,
  onViewAll: PropTypes.func.isRequired,
};

export default FollowUpReminders;