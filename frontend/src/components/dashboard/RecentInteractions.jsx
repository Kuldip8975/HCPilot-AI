import React from 'react';
import PropTypes from 'prop-types';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { Calendar, ChevronRight, Clock, MessageSquare, Phone, Mail } from 'lucide-react';

import styles from './RecentInteractions.module.css';

export const RecentInteractions = ({ interactions, onViewAll }) => {
  // Safe date formatting function
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    try {
      const parsedDate = parseISO(dateString);
      if (isNaN(parsedDate.getTime())) return 'Invalid date';
      return formatDistanceToNow(parsedDate, { addSuffix: true });
    } catch (error) {
      return 'Invalid date';
    }
  };

  const getInteractionIcon = (type) => {
    if (!type) return <MessageSquare size={16} />;
    switch (type?.toLowerCase()) {
      case 'meeting':
        return <Calendar size={16} />;
      case 'call':
        return <Phone size={16} />;
      case 'email':
        return <Mail size={16} />;
      default:
        return <MessageSquare size={16} />;
    }
  };

  const getTypeColor = (type) => {
    if (!type) return '#64748b';
    switch (type?.toLowerCase()) {
      case 'meeting':
        return '#2563eb';
      case 'call':
        return '#7c3aed';
      case 'email':
        return '#f59e0b';
      default:
        return '#64748b';
    }
  };

  return (
    <div className={styles.recentInteractions}>
      <div className={styles.header}>
        <h3 className={styles.title}>Recent Interactions</h3>
        <button className={styles.viewAll} onClick={onViewAll}>
          View All
          <ChevronRight size={16} />
        </button>
      </div>

      <div className={styles.list}>
        {interactions.length === 0 ? (
          <div className={styles.emptyState}>
            <p>No interactions yet.</p>
            <p className={styles.emptyStateSub}>Start logging your HCP interactions.</p>
          </div>
        ) : (
          interactions.map((interaction) => (
            <div key={interaction.id} className={styles.interactionItem}>
              <div className={styles.interactionIcon} style={{ backgroundColor: getTypeColor(interaction.type) }}>
                {getInteractionIcon(interaction.type)}
              </div>
              <div className={styles.interactionContent}>
                <div className={styles.interactionHeader}>
                  <span className={styles.hcpName}>{interaction.hcpName || 'Unknown HCP'}</span>
                  <span className={styles.interactionType}>{interaction.type || 'Other'}</span>
                </div>
                <div className={styles.interactionSpecialty}>{interaction.hcpSpecialty || ''}</div>
                <p className={styles.interactionSummary}>{interaction.summary || ''}</p>
                <div className={styles.interactionFooter}>
                  <span className={styles.interactionDate}>
                    <Clock size={12} />
                    {formatDate(interaction.date)}
                  </span>
                  {interaction.followUp && (
                    <span className={styles.followUpBadge}>Follow-up</span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

RecentInteractions.propTypes = {
  interactions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      hcpName: PropTypes.string,
      hcpSpecialty: PropTypes.string,
      date: PropTypes.string,
      type: PropTypes.string,
      summary: PropTypes.string,
      followUp: PropTypes.bool,
    })
  ).isRequired,
  onViewAll: PropTypes.func.isRequired,
};

export default RecentInteractions;