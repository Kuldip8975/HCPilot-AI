import React from 'react';
import PropTypes from 'prop-types';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { Calendar, MessageSquare, Phone, Mail, Clock, ChevronRight } from 'lucide-react';

import styles from './HCPInteractionTimeline.module.css';

/**
 * HCPInteractionTimeline Component
 * Displays chronological timeline of interactions for an HCP
 */
export const HCPInteractionTimeline = ({ interactions, onLogInteraction }) => {
  const getInteractionIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'meeting':
        return <Calendar size={18} />;
      case 'call':
        return <Phone size={18} />;
      case 'email':
        return <Mail size={18} />;
      default:
        return <MessageSquare size={18} />;
    }
  };

  const getTypeColor = (type) => {
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

  const getTypeBadgeClass = (type) => {
    switch (type?.toLowerCase()) {
      case 'meeting':
        return styles.badgeMeeting;
      case 'call':
        return styles.badgeCall;
      case 'email':
        return styles.badgeEmail;
      default:
        return styles.badgeOther;
    }
  };

  return (
    <div className={styles.timeline}>
      <div className={styles.header}>
        <h3 className={styles.title}>Interaction History</h3>
        <button className={styles.logButton} onClick={onLogInteraction}>
          <MessageSquare size={16} />
          Log New
        </button>
      </div>

      <div className={styles.timelineList}>
        {interactions.length === 0 ? (
          <div className={styles.emptyState}>
            <p>No interactions yet.</p>
            <button className={styles.emptyStateButton} onClick={onLogInteraction}>
              Log your first interaction with this HCP
            </button>
          </div>
        ) : (
          interactions.map((interaction, index) => (
            <div key={interaction.id} className={styles.timelineItem}>
              {/* Timeline line */}
              {index < interactions.length - 1 && (
                <div className={styles.timelineLine} />
              )}
              
              {/* Timeline dot */}
              <div 
                className={styles.timelineDot}
                style={{ backgroundColor: getTypeColor(interaction.type) }}
              >
                {getInteractionIcon(interaction.type)}
              </div>

              {/* Content */}
              <div className={styles.timelineContent}>
                <div className={styles.timelineHeader}>
                  <div className={styles.timelineLeft}>
                    <span className={styles.interactionType}>
                      {interaction.type}
                    </span>
                    <span className={styles.interactionDate}>
                      <Clock size={12} />
                      {formatDistanceToNow(parseISO(interaction.date), { addSuffix: true })}
                    </span>
                  </div>
                  {interaction.followUp && (
                    <span className={styles.followUpBadge}>
                      Follow-up: {new Date(interaction.followUpDate).toLocaleDateString()}
                    </span>
                  )}
                </div>

                <h4 className={styles.interactionSummary}>{interaction.summary}</h4>
                <p className={styles.interactionNotes}>{interaction.notes}</p>

                <div className={styles.timelineActions}>
                  <button className={styles.viewDetailButton}>
                    View Details
                    <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

HCPInteractionTimeline.propTypes = {
  interactions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      date: PropTypes.string.isRequired,
      type: PropTypes.string.isRequired,
      summary: PropTypes.string.isRequired,
      notes: PropTypes.string.isRequired,
      followUp: PropTypes.bool.isRequired,
      followUpDate: PropTypes.string,
    })
  ).isRequired,
  onLogInteraction: PropTypes.func.isRequired,
};

export default HCPInteractionTimeline;