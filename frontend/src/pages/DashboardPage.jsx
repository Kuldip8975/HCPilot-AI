import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  Users,
  Calendar,
  MessageSquare,
  TrendingUp,
  PlusCircle,
} from 'lucide-react';

import {
  fetchInteractions,
  selectInteractions,
  selectInteractionsLoading,
} from '../redux/slices/interactionSlice';
import {
  fetchHCPs,
  selectHCPs,
  selectHCPsLoading,
} from '../redux/slices/hcpSlice';
import { selectUser } from '../redux/slices/authSlice';
import { StatCard } from '../components/dashboard/StatCard';
import { WeeklyActivityChart } from '../components/dashboard/WeeklyActivityChart';
import { RecentInteractions } from '../components/dashboard/RecentInteractions';
import { FollowUpReminders } from '../components/dashboard/FollowUpReminders';
import { QuickActions } from '../components/dashboard/QuickActions';
import { Loading } from '../components/common/Loading';
import { ROUTES } from '../routes/RouteConstants';
import styles from './DashboardPage.module.css';

/* ---------- Helpers ---------- */

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
};

// Normalize interaction shape regardless of backend field naming
const normalizeInteraction = (i) => ({
  id: i.id,
  hcpId: i.hcpId || i.hcp_id,
  hcpName: i.hcp_name || i.hcpName || 'Unknown HCP',
  hcpSpecialty: i.hcp_specialty || i.hcpSpecialty || '',
  date:
    i.interaction_date ||
    i.date ||
    i.created_at ||
    new Date().toISOString(),
  type: i.interaction_type || i.type || 'other',
  summary: i.summary || (i.notes ? i.notes.slice(0, 100) : ''),
  followUp: i.follow_up_required ?? i.followUpRequired ?? i.followUp ?? false,
  followUpDate: i.follow_up_date || i.followUpDate || null,
  followUpPriority: i.follow_up_priority || i.followUpPriority || 'medium',
});

/* ---------- Component ---------- */

export const DashboardPage = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const interactions = useSelector(selectInteractions);
  const hcps = useSelector(selectHCPs);
  const user = useSelector(selectUser);
  const interactionsLoading = useSelector(selectInteractionsLoading);
  const hcpsLoading = useSelector(selectHCPsLoading);

  const [isLoading, setIsLoading] = useState(true);

  const firstName = user?.full_name?.split(' ')[0] || 'there';

  /* ---------- Load data ---------- */
  useEffect(() => {
    let mounted = true;

    const loadData = async () => {
      setIsLoading(true);
      await Promise.all([
        dispatch(fetchInteractions({ limit: 10 })),
        dispatch(fetchHCPs({ limit: 100 })),
      ]);
      if (mounted) setIsLoading(false);
    };

    loadData();
    return () => {
      mounted = false;
    };
  }, [dispatch]);

  /* ---------- Derived data ---------- */

  // Single normalized list — used everywhere below
  const normalized = useMemo(
    () => interactions.map(normalizeInteraction),
    [interactions]
  );

  // Stats
  const totalInteractions = normalized.length;
  const uniqueHCPs = new Set(normalized.map((i) => i.hcpId).filter(Boolean)).size;
  const followUpsDue = normalized.filter((i) => i.followUp).length;
  const engagementRate =
    hcps.length > 0 ? Math.round((uniqueHCPs / hcps.length) * 100) : 0;

  const stats = [
    {
      id: 1,
      title: 'Total HCPs',
      value: hcps.length,
      icon: Users,
      color: '#2563eb',
      trend: hcps.length > 0 ? `+${hcps.length}` : '0',
      trendDirection: hcps.length > 0 ? 'up' : 'neutral',
    },
    {
      id: 2,
      title: 'Interactions',
      value: totalInteractions,
      icon: MessageSquare,
      color: '#7c3aed',
      trend: totalInteractions > 0 ? `+${totalInteractions}` : '0',
      trendDirection: totalInteractions > 0 ? 'up' : 'neutral',
    },
    {
      id: 3,
      title: 'Follow-ups Due',
      value: followUpsDue,
      icon: Calendar,
      color: '#f59e0b',
      trend: followUpsDue > 0 ? `⚠ ${followUpsDue}` : '✓ 0',
      trendDirection: followUpsDue > 3 ? 'down' : followUpsDue > 0 ? 'neutral' : 'up',
    },
    {
      id: 4,
      title: 'Engagement Rate',
      value: `${engagementRate}%`,
      icon: TrendingUp,
      color: '#22c55e',
      trend: `${engagementRate}%`,
      trendDirection:
        engagementRate > 50 ? 'up' : engagementRate > 0 ? 'neutral' : 'down',
    },
  ];

  // Recent interactions (top 5)
  const recentInteractions = useMemo(
    () =>
      normalized.slice(0, 5).map((i) => ({
        id: i.id,
        hcpName: i.hcpName,
        hcpSpecialty: i.hcpSpecialty,
        date: i.date,
        type: i.type,
        summary: i.summary,
        followUp: i.followUp,
      })),
    [normalized]
  );

  // Follow-ups (top 3)
  const followUps = useMemo(
    () =>
      normalized
        .filter((i) => i.followUp)
        .slice(0, 3)
        .map((i) => ({
          id: i.id,
          hcpName: i.hcpName,
          hcpSpecialty: i.hcpSpecialty,
          dueDate:
            i.followUpDate ||
            new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          priority: i.followUpPriority,
          notes: i.summary || 'Follow-up required',
        })),
    [normalized]
  );

  /* ---------- Loading ---------- */
  if (isLoading || interactionsLoading || hcpsLoading) {
    return <Loading fullScreen message="Loading dashboard..." />;
  }

  /* ---------- Render ---------- */
  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerText}>
          <h1 className={styles.title}>
            {getGreeting()}, {firstName} 👋
          </h1>
          <p className={styles.subtitle}>
            Here's what's happening with your HCP interactions today.
          </p>
        </div>

        <div className={styles.headerActions}>
          <button
            className={styles.primaryButton}
            onClick={() => navigate(ROUTES.INTERACTION_NEW)}
          >
            <PlusCircle size={18} />
            Log Interaction
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className={styles.statsGrid}>
        {stats.map((stat) => (
          <StatCard key={stat.id} {...stat} />
        ))}
      </div>

      {/* Weekly chart */}
      <WeeklyActivityChart interactions={normalized} />

      {/* Quick actions */}
      <QuickActions />

      {/* Bottom grid */}
      <div className={styles.contentGrid}>
        <div className={styles.recentInteractions}>
          <RecentInteractions
            interactions={recentInteractions}
            onViewAll={() => navigate(ROUTES.INTERACTION_HISTORY)}
          />
        </div>
        <div className={styles.followUps}>
          <FollowUpReminders
            reminders={followUps}
            onViewAll={() => navigate(ROUTES.INTERACTION_HISTORY)}
          />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;