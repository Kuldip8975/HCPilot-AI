import React from 'react';
import PropTypes from 'prop-types';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { MapPin, Mail, Phone, Calendar, MessageSquare, User } from 'lucide-react';

import styles from './HCPCard.module.css';

/**
 * HCPCard Component
 * Displays HCP information in a card format
 */
export const HCPCard = ({ hcp, onView, onLogInteraction }) => {
  const { id, name, title, specialty, email, phone, location, lastInteraction, interactionCount, status } = hcp;

  const statusColors = {
    active: '#22c55e',
    inactive: '#ef4444',
    pending: '#f59e0b',
  };

  const getInitials = (fullName) => {
    if (!fullName) return '?';
    return fullName
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // Some HCPs (e.g. a doctor who just signed up) have no interactions
  // logged yet, so lastInteraction can be null/undefined - guard against
  // that instead of crashing on parseISO(null).
  const lastInteractionLabel = lastInteraction
    ? formatDistanceToNow(parseISO(lastInteraction), { addSuffix: true })
    : 'No interactions yet';

  return (
    <div className={styles.hcpCard}>
      <div className={styles.cardHeader}>
        <div className={styles.avatarContainer}>
          <div className={styles.avatar}>
            {getInitials(name)}
          </div>
          <div 
            className={styles.statusDot} 
            style={{ backgroundColor: statusColors[status] || '#94a3b8' }}
            title={`Status: ${status}`}
          />
        </div>
        <div className={styles.headerInfo}>
          <h3 className={styles.hcpName}>{name}</h3>
          <span className={styles.hcpTitle}>{title}</span>
          <span className={styles.hcpSpecialty}>{specialty}</span>
        </div>
      </div>

      <div className={styles.cardBody}>
        <div className={styles.detailRow}>
          <MapPin size={16} />
          <span>{location}</span>
        </div>
        <div className={styles.detailRow}>
          <Mail size={16} />
          {email ? (
            <a href={`mailto:${email}`} className={styles.detailLink}>{email}</a>
          ) : (
            <span>—</span>
          )}
        </div>
        <div className={styles.detailRow}>
          <Phone size={16} />
          {phone ? (
            <a href={`tel:${phone}`} className={styles.detailLink}>{phone}</a>
          ) : (
            <span>—</span>
          )}
        </div>
        <div className={styles.detailRow}>
          <Calendar size={16} />
          <span>Last interaction: {lastInteractionLabel}</span>
        </div>
        <div className={styles.detailRow}>
          <MessageSquare size={16} />
          <span>{interactionCount} interactions</span>
        </div>
      </div>

      <div className={styles.cardActions}>
        <button
          className={styles.viewButton}
          onClick={() => onView(id)}
        >
          <User size={16} />
          View Profile
        </button>
        <button
          className={styles.interactButton}
          onClick={() => onLogInteraction(id)}
        >
          <MessageSquare size={16} />
          Log Interaction
        </button>
      </div>
    </div>
  );
};

HCPCard.propTypes = {
  hcp: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    title: PropTypes.string,
    specialty: PropTypes.string,
    email: PropTypes.string,
    phone: PropTypes.string,
    location: PropTypes.string,
    lastInteraction: PropTypes.string,
    interactionCount: PropTypes.number,
    status: PropTypes.oneOf(['active', 'inactive', 'pending']),
  }).isRequired,
  onView: PropTypes.func.isRequired,
  onLogInteraction: PropTypes.func.isRequired,
};

export default HCPCard;