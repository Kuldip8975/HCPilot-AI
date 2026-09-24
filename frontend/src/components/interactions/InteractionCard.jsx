import React from 'react';
import PropTypes from 'prop-types';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { Calendar, MessageSquare, Phone, Mail, Clock, Edit, Eye, ChevronRight } from 'lucide-react';

import styles from './InteractionCard.module.css';

/**
 * InteractionCard Component
 * Displays a summary of an interaction in the history list
 */
export const InteractionCard = ({ interaction, onView, onEdit }) => {
  // Safe date formatting
  const formatDate = (dateString) => {
    if (!dateString) return null;
    try {
      const parsedDate = parseISO(dateString);
      if (isNaN(parsedDate.getTime())) return null;
      return formatDistanceToNow(parsedDate, { addSuffix: true });
    } catch (error) {
      return null;
    }
  };

  const getTypeIcon = (type) => {
    if (!type) return <MessageSquare size={18} />;
    switch (type.toLowerCase()) {
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
    if (!type) return '#64748b';
    switch (type.toLowerCase()) {
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

  // Safe access to properties with fallbacks
  const {
    id,
    hcpName = 'Unknown HCP',
    hcpSpecialty = '',
    date = null,
    type = 'other',
    summary = '',
    notes = '',
    followUp = false,
    followUpDate = null,
    followUpStatus = null,
  } = interaction || {};

  const formattedDate = formatDate(date);
  const formattedFollowUpDate = formatDate(followUpDate);
  // Only show the badge when we actually have a real, resolvable
  // follow-up date - a "Follow-up: Unknown date" badge is worse than no
  // badge at all.
  const showFollowUpBadge = followUp && !!formattedFollowUpDate;

  return (
    <div className={styles.interactionCard}>
      <div className={styles.cardHeader}>
        <div className={styles.typeBadge} style={{ backgroundColor: getTypeColor(type) }}>
          {getTypeIcon(type)}
          <span>{type || 'Other'}</span>
        </div>
        <div className={styles.cardDate}>
          <Clock size={14} />
          <span>{formattedDate || 'Unknown date'}</span>
        </div>
      </div>

      <div className={styles.cardBody}>
        <div className={styles.hcpInfo}>
          <h3 className={styles.hcpName}>{hcpName}</h3>
          {hcpSpecialty && (
            <span className={styles.hcpSpecialty}>{hcpSpecialty}</span>
          )}
        </div>
        {summary && <p className={styles.interactionSummary}>{summary}</p>}
        {notes && <p className={styles.interactionNotes}>{notes}</p>}
        {showFollowUpBadge && (
          <div className={styles.followUpBadge}>
            <Calendar size={14} />
            Follow-up: {formattedFollowUpDate}
            {followUpStatus ? ` (${followUpStatus})` : ''}
          </div>
        )}
      </div>

      <div className={styles.cardActions}>
        <button className={styles.actionButton} onClick={() => onView(id)}>
          <Eye size={16} />
          View Details
        </button>
        <button className={`${styles.actionButton} ${styles.editButton}`} onClick={() => onEdit(id)}>
          <Edit size={16} />
          Edit
        </button>
        <button className={styles.expandButton} onClick={() => onView(id)}>
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  );
};

InteractionCard.propTypes = {
  interaction: PropTypes.shape({
    id: PropTypes.string.isRequired,
    hcpName: PropTypes.string,
    hcpSpecialty: PropTypes.string,
    date: PropTypes.string,
    type: PropTypes.string,
    summary: PropTypes.string,
    notes: PropTypes.string,
    followUp: PropTypes.bool,
    followUpDate: PropTypes.string,
    followUpStatus: PropTypes.string,
  }).isRequired,
  onView: PropTypes.func.isRequired,
  onEdit: PropTypes.func.isRequired,
};

export default InteractionCard;