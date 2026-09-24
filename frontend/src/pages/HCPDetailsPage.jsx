import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Calendar,
  MessageSquare,
  Edit,
  User,
  Activity,
  Star,
  Clock
} from 'lucide-react';

import { hcpService } from '../services/hcpService';
import { interactionService } from '../services/interactionService';
import { HCPInteractionTimeline } from '../components/hcp/HCPInteractionTimeline';
import { Loading } from '../components/common/Loading';
import { ROUTES } from '../routes/RouteConstants';

import styles from './HCPDetailsPage.module.css';

/**
 * HCPDetailsPage Component
 * Displays detailed HCP information and interaction history
 * (fetches real data from the backend instead of mock data)
 */
export const HCPDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [hcp, setHcp] = useState(null);
  const [interactions, setInteractions] = useState([]);

  useEffect(() => {
    let cancelled = false;

    const loadData = async () => {
      setIsLoading(true);
      try {
        const [hcpRes, interactionsRes] = await Promise.all([
          hcpService.getHCPById(id),
          interactionService.getInteractions({ hcp_id: id }),
        ]);

        if (cancelled) return;

        const apiHcp = hcpRes?.data ?? hcpRes;
        const apiInteractions = (interactionsRes?.data ?? interactionsRes)?.items || [];

        setHcp({
          id: apiHcp.id,
          name: apiHcp.name,
          title: apiHcp.title || apiHcp.specialty || 'HCP',
          specialty: apiHcp.specialty || 'â€”',
          email: apiHcp.email || '',
          phone: apiHcp.phone || '',
          // Backend field is "address" (renamed from the older
          // "location") - reading apiHcp.location here always came back
          // undefined, so this card permanently showed "-" for location.
          location: apiHcp.address || 'â€”',
          organization: apiHcp.organization || 'â€”',
          status: apiHcp.status || 'active',
          engagementScore: apiHcp.engagement_score ?? 0,
          totalInteractions: apiInteractions.length,
          lastInteraction: apiHcp.last_interaction || null,
          notes: apiHcp.notes || 'No notes yet.',
          preferences: apiHcp.preferences || 'No preferences on file.',
        });

        setInteractions(
          apiInteractions.map((it) => ({
            id: it.id,
            date: it.interaction_date,
            type: it.interaction_type,
            summary: it.summary || '(no summary)',
            notes: it.notes || '',
            followUp: !!it.follow_up_required,
            followUpDate: it.follow_up_date || null,
          }))
        );
      } catch (error) {
        if (!cancelled) {
          setHcp(null);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    loadData();
    return () => { cancelled = true; };
  }, [id]);

  const handleBack = () => {
    navigate(ROUTES.HCPS);
  };

  const handleLogInteraction = () => {
    navigate(ROUTES.INTERACTION_NEW, { state: { hcpId: id, hcpName: hcp?.name } });
  };

  const handleEditHCP = () => {
    navigate(`/hcps/${id}/edit`);
  };

  if (isLoading) {
    return <Loading fullScreen message="Loading HCP details..." />;
  }

  if (!hcp) {
    return (
      <div className={styles.notFound}>
        <h2>HCP Not Found</h2>
        <button onClick={handleBack} className={styles.backButton}>
          <ArrowLeft size={18} />
          Back to HCP List
        </button>
      </div>
    );
  }

  return (
    <div className={styles.hcpDetailsPage}>
      {/* Header */}
      <div className={styles.header}>
        <button className={styles.backButton} onClick={handleBack}>
          <ArrowLeft size={18} />
          Back to HCPs
        </button>
        <div className={styles.headerActions}>
          <button className={styles.editButton} onClick={handleEditHCP}>
            <Edit size={16} />
            Edit Profile
          </button>
          <button className={styles.interactButton} onClick={handleLogInteraction}>
            <MessageSquare size={16} />
            Log Interaction
          </button>
        </div>
      </div>

      {/* Profile Section */}
      <div className={styles.profileSection}>
        <div className={styles.profileCard}>
          <div className={styles.profileHeader}>
            <div className={styles.avatarLarge}>
              {hcp.name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2)}
            </div>
            <div className={styles.profileInfo}>
              <h1 className={styles.profileName}>{hcp.name}</h1>
              <div className={styles.profileMeta}>
                <span className={styles.profileTitle}>{hcp.title}</span>
                <span className={styles.profileSpecialty}>{hcp.specialty}</span>
                <span className={`${styles.statusBadge} ${styles[hcp.status]}`}>
                  {hcp.status.charAt(0).toUpperCase() + hcp.status.slice(1)}
                </span>
              </div>
              <div className={styles.profileDetails}>
                <div className={styles.detailItem}>
                  <Mail size={16} />
                  {hcp.email ? <a href={`mailto:${hcp.email}`}>{hcp.email}</a> : <span>â€”</span>}
                </div>
                <div className={styles.detailItem}>
                  <Phone size={16} />
                  {hcp.phone ? <a href={`tel:${hcp.phone}`}>{hcp.phone}</a> : <span>â€”</span>}
                </div>
                <div className={styles.detailItem}>
                  <MapPin size={16} />
                  <span>{hcp.location}</span>
                </div>
                <div className={styles.detailItem}>
                  <Activity size={16} />
                  <span>{hcp.organization}</span>
                </div>
              </div>
            </div>
          </div>

          <div className={styles.statsRow}>
            <div className={styles.statItem}>
              <span className={styles.statValue}>{hcp.totalInteractions}</span>
              <span className={styles.statLabel}>Total Interactions</span>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.statItem}>
              <span className={styles.statValue}>{hcp.engagementScore}%</span>
              <span className={styles.statLabel}>Engagement Score</span>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.statItem}>
              <span className={styles.statValue}>
                <Clock size={16} />
              </span>
              <span className={styles.statLabel}>
                Last: {hcp.lastInteraction ? new Date(hcp.lastInteraction).toLocaleDateString() : 'Never'}
              </span>
            </div>
          </div>

          <div className={styles.notesSection}>
            <h4 className={styles.sectionTitle}>Notes</h4>
            <p className={styles.notesText}>{hcp.notes}</p>
          </div>

          <div className={styles.preferencesSection}>
            <h4 className={styles.sectionTitle}>Preferences</h4>
            <p className={styles.preferencesText}>{hcp.preferences}</p>
          </div>
        </div>
      </div>

      {/* Interaction Timeline */}
      <div className={styles.timelineSection}>
        <HCPInteractionTimeline
          interactions={interactions}
          onLogInteraction={handleLogInteraction}
        />
      </div>
    </div>
  );
};

export default HCPDetailsPage;