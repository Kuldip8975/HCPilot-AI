import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import {
  Calendar,
  Clock,
  LogOut,
  User,
  LayoutGrid,
  History as HistoryIcon,
  BarChart3,
  Users,
  Activity,
  ChevronDown,
  ChevronUp,
  Tag,
} from 'lucide-react';

import { doctorService } from '../services/doctorService';
import { logout } from '../redux/slices/authSlice';
import { ROUTES } from '../routes/RouteConstants';
import { Loading } from '../components/common/Loading';
import HcPilotLogo from '../components/HcPilotLogo';
import styles from './DoctorDashboardPage.module.css';

const TABS = [
  { id: 'overview', label: 'Overview', icon: LayoutGrid },
  { id: 'followups', label: 'Follow-ups', icon: Calendar },
  { id: 'history', label: 'History', icon: HistoryIcon },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
];

const formatDate = (isoString, opts) => {
  if (!isoString) return 'Date not set';
  try {
    return new Date(isoString).toLocaleString(undefined, opts || {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
};

export const DoctorDashboardPage = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [activeTab, setActiveTab] = useState('overview');
  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState(null);
  const [followUps, setFollowUps] = useState([]);
  const [history, setHistory] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedFollowUpId, setExpandedFollowUpId] = useState(null);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [profileRes, statsRes, followUpsRes, historyRes, analyticsRes] = await Promise.all([
          doctorService.getMyProfile(),
          doctorService.getMyStats(),
          doctorService.getMyFollowUps(true),
          doctorService.getMyHistory(50),
          doctorService.getMyAnalytics(30),
        ]);
        setProfile(profileRes);
        setStats(statsRes);
        setFollowUps(followUpsRes || []);
        setHistory(historyRes || []);
        setAnalytics(analyticsRes);
      } catch (err) {
        setError(
          err?.response?.data?.detail ||
          "Couldn't load your dashboard right now. Please try again."
        );
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  const handleLogout = async () => {
    await dispatch(logout());
    navigate(ROUTES.LOGIN);
  };

  const toggleFollowUp = (id) => {
    setExpandedFollowUpId((current) => (current === id ? null : id));
  };

  if (isLoading) {
    return <Loading fullScreen message="Loading your dashboard..." />;
  }

  const trendEntries = analytics
    ? Object.entries(analytics.daily_trend).sort(([a], [b]) => a.localeCompare(b)).slice(-14)
    : [];
  const maxTrendValue = Math.max(1, ...trendEntries.map(([, count]) => count));

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          {/* Brand tile — HcPilot AI */}
          <HcPilotLogo size={38} />
          <div>
            <div className={styles.headerTitle}>HcPilot AI · Doctor Portal</div>
            <div className={styles.headerSubtitle}>
              {profile?.name ? `Welcome, ${profile.name}` : 'Your follow-ups'}
            </div>
          </div>
        </div>
        <button type="button" className={styles.logoutButton} onClick={handleLogout}>
          <LogOut size={16} />
          Log out
        </button>
      </header>

      <nav className={styles.tabBar}>
        {TABS.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              type="button"
              className={`${styles.tabButton} ${activeTab === tab.id ? styles.tabButtonActive : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={15} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      <main className={styles.content}>
        {error && <div className={styles.errorBanner}>{error}</div>}

        {activeTab === 'overview' && (
          <>
            {profile && (
              <div className={styles.profileCard}>
                <div className={styles.profileAvatar}>
                  <User size={22} />
                </div>
                <div>
                  <div className={styles.profileName}>{profile.name}</div>
                  <div className={styles.profileMeta}>
                    {[profile.specialty, profile.organization, profile.location]
                      .filter(Boolean)
                      .join(' · ')}
                  </div>
                </div>
              </div>
            )}

            <div className={styles.statsGrid}>
              <div className={styles.statCard}>
                <div className={styles.statIcon}><Activity size={18} /></div>
                <div className={styles.statValue}>{stats?.total_visits ?? 0}</div>
                <div className={styles.statLabel}>Total visits logged</div>
              </div>
              <div className={styles.statCard}>
                <div className={styles.statIcon}><Users size={18} /></div>
                <div className={styles.statValue}>{stats?.distinct_reps ?? 0}</div>
                <div className={styles.statLabel}>Reps who've visited</div>
              </div>
              <div className={styles.statCard}>
                <div className={styles.statIcon}><Calendar size={18} /></div>
                <div className={styles.statValue}>{stats?.upcoming_followups ?? 0}</div>
                <div className={styles.statLabel}>Upcoming follow-ups</div>
              </div>
            </div>

            {stats?.last_visit_date && (
              <div className={styles.lastVisit}>
                Last visit logged: <strong>{formatDate(stats.last_visit_date, { year: 'numeric', month: 'short', day: 'numeric' })}</strong>
              </div>
            )}
          </>
        )}

        {activeTab === 'followups' && (
          <>
            <h2 className={styles.sectionTitle}>Upcoming follow-ups scheduled with you</h2>
            {followUps.length === 0 ? (
              <div className={styles.emptyState}>
                No sales reps have scheduled a follow-up with you yet. When
                they do, it'll show up here automatically.
              </div>
            ) : (
              <div className={styles.followUpList}>
                {followUps.map((f) => {
                  const isExpanded = expandedFollowUpId === f.followup_id;
                  return (
                    <div
                      key={f.followup_id}
                      className={styles.followUpCard}
                      style={{ cursor: 'pointer' }}
                      onClick={() => toggleFollowUp(f.followup_id)}
                    >
                      <div className={styles.followUpDate}>
                        <Calendar size={16} />
                        {formatDate(f.scheduled_date)}
                        <span className={styles.followUpChevron}>
                          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </span>
                      </div>
                      <div className={styles.followUpRep}>
                        <User size={14} />
                        Requested by <strong>{f.rep_name}</strong>
                      </div>

                      {!isExpanded && f.interaction_summary && (
                        <div className={styles.followUpSummary}>{f.interaction_summary}</div>
                      )}

                      {isExpanded && (
                        <>
                          {f.interaction_summary && (
                            <div className={styles.followUpSummary}>
                              <strong>Visit summary:</strong> {f.interaction_summary}
                            </div>
                          )}
                          {f.interaction_topics && (
                            <div className={styles.followUpNotes}>
                              <Tag size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                              Topics: {f.interaction_topics}
                            </div>
                          )}
                          {f.notes && (
                            <div className={styles.followUpNotes}>Rep's note: "{f.notes}"</div>
                          )}
                        </>
                      )}

                      <div className={styles.followUpFooter}>
                        <span className={`${styles.priorityBadge} ${styles[`priority_${f.priority}`] || ''}`}>
                          <Clock size={12} />
                          {f.priority} priority
                        </span>
                        <span className={styles.statusBadge}>{f.status}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {activeTab === 'history' && (
          <>
            <h2 className={styles.sectionTitle}>Your visit history</h2>
            {history.length === 0 ? (
              <div className={styles.emptyState}>
                No visits have been logged with you yet.
              </div>
            ) : (
              <div className={styles.historyList}>
                {history.map((h) => (
                  <div key={h.interaction_id} className={styles.historyRow}>
                    <div className={styles.historyDate}>
                      {formatDate(h.interaction_date, { year: 'numeric', month: 'short', day: 'numeric' })}
                    </div>
                    <div className={styles.historyBody}>
                      <div className={styles.historyRep}>
                        <strong>{h.rep_name}</strong>
                        <span className={styles.historyType}>{h.interaction_type}</span>
                      </div>
                      {h.summary && <div className={styles.historySummary}>{h.summary}</div>}
                      {h.topics && <div className={styles.historyTopics}>Topics: {h.topics}</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'analytics' && (
          <>
            <h2 className={styles.sectionTitle}>Visits over the last {analytics?.window_days ?? 30} days</h2>
            <div className={styles.analyticsSummary}>
              <strong>{analytics?.total_in_window ?? 0}</strong> visits in this window
            </div>
            {trendEntries.length === 0 ? (
              <div className={styles.emptyState}>
                Not enough visit data yet to show a trend.
              </div>
            ) : (
              <div className={styles.chart}>
                {trendEntries.map(([date, count]) => (
                  <div key={date} className={styles.chartBarWrapper}>
                    <div
                      className={styles.chartBar}
                      style={{ height: `${(count / maxTrendValue) * 100}%` }}
                      title={`${date}: ${count} visit(s)`}
                    />
                    <div className={styles.chartLabel}>{date.slice(5)}</div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default DoctorDashboardPage;