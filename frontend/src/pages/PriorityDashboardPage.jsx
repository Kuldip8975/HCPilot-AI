import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Target,
  RefreshCw,
  Clock,
  TrendingUp,
  CalendarCheck,
  MessageSquare,
  CheckCircle,
  Loader,
  Route as RouteIcon,
  Navigation,
  BarChart3,
} from 'lucide-react';
import { toast } from 'react-toastify';

import { priorityService } from '../services/priorityService';
import { followupService } from '../services/followupService';
import { ROUTES } from '../routes/RouteConstants';
import { DayPlanMap } from '../components/DayPlanMap';
import styles from './PriorityDashboardPage.module.css';

// Must match backend/app/services/route_planner_service.py's
// DEFAULT_VISIT_DURATION_MINUTES - used here only to estimate remaining
// time budget after marking a stop visited (for re-routing), not to
// compute the actual plan (the backend is the source of truth for that).
const DEFAULT_VISIT_DURATION_MINUTES = 20;

/**
 * PriorityDashboardPage - "Next Best Action" for the rep.
 *
 * Ranks the rep's own HCPs by a transparent, rule-based score (days
 * since last contact + engagement_score + pending follow-up status),
 * then shows a short LLM-written (or rule-based fallback) reason for
 * each of the top picks. See backend/app/services/priority_service.py
 * for the honest scope note on why this is rule-based, not a trained ML
 * model - this mirrors what real pharma CRM tools (Veeva, Aktana) call
 * "Next Best Action".
 *
 * "Mark Complete" resolves the actual pending FollowUp record via
 * PUT /followups/{id}/complete (previously wired up on the backend but
 * never called from anywhere in the frontend) - this is the one place
 * in the app where a rep sees "this HCP has something pending" per-HCP,
 * so it's the natural place to let them close it out.
 *
 * "Plan My Day" (Smart Day Planner) reuses these same priority scores
 * as the "value" side of a time-budgeted route: given how much time the
 * rep has today, it picks which of these HCPs to visit and in what
 * order, using real road travel time (via OSRM on the backend) as the
 * "cost" side. See backend/app/services/route_planner_service.py for
 * the algorithm (a simplified Orienteering Problem solver).
 *
 * "Visited" on a planned stop marks it done (POST /day-plan/mark-visited,
 * logged for the planned-vs-actual analytics strip) and re-requests a
 * plan for the REMAINING stops only, with a reduced time budget (this
 * plan's total minus the time spent reaching + visiting that stop) and a
 * fresh live-location read - so the rest of the day's route adjusts to
 * where the rep actually is now, not where they started.
 *
 * Error handling note: request failures are NOT toasted here - the app's
 * axios response interceptor (src/api/interceptors.js) already shows a
 * toast for every non-2xx response, parsing both error envelope shapes
 * the backend can send (plain FastAPI { detail } and the app's custom
 * { success, error: { message, details } } shape, e.g. for validation
 * errors). Toasting again here would just duplicate that message.
 */
export const PriorityDashboardPage = () => {
  const navigate = useNavigate();
  const [priorities, setPriorities] = useState([]);
  const [generatedAt, setGeneratedAt] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [completingId, setCompletingId] = useState(null);

  // --- Smart Day Planner state ---
  const [timeBudgetHours, setTimeBudgetHours] = useState(4);
  const [isPlanningDay, setIsPlanningDay] = useState(false);
  const [dayPlan, setDayPlan] = useState(null);
  const [usedLiveLocation, setUsedLiveLocation] = useState(false);
  const [excludedHcpIds, setExcludedHcpIds] = useState([]);
  const [activeBudgetMinutes, setActiveBudgetMinutes] = useState(null);
  const [visitingHcpId, setVisitingHcpId] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  const loadPriorities = useCallback(async (isRefresh = false) => {
    if (isRefresh) setIsRefreshing(true);
    else setIsLoading(true);
    try {
      const result = await priorityService.getWeeklyPriorities();
      setPriorities(result?.priorities || []);
      setGeneratedAt(result?.generated_at || null);
    } catch (error) {
      // Interceptor already shows a toast for this - no need to duplicate it.
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  const loadAnalytics = useCallback(async () => {
    try {
      const result = await priorityService.getDayPlanAnalytics();
      setAnalytics(result);
    } catch {
      // Analytics is a nice-to-have strip, not critical - fail silently.
    }
  }, []);

  useEffect(() => {
    loadPriorities(false);
    loadAnalytics();
  }, [loadPriorities, loadAnalytics]);

  const handleLogInteraction = (item) => {
    navigate(ROUTES.INTERACTION_NEW, {
      state: { hcpId: item.hcp_id, hcpName: item.hcp_name },
    });
  };

  const handleCompleteFollowup = async (item) => {
    if (!item.followup_id || completingId) return;
    setCompletingId(item.followup_id);
    try {
      await followupService.completeFollowup(item.followup_id);
      toast.success(`Follow-up with ${item.hcp_name} marked complete.`);
      await loadPriorities(true);
    } catch (error) {
      // Interceptor already shows a toast for this - no need to duplicate it.
    } finally {
      setCompletingId(null);
    }
  };

  const getLiveLocation = () =>
    new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve({ latitude: null, longitude: null });
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
        },
        () => resolve({ latitude: null, longitude: null }),
        { enableHighAccuracy: false, timeout: 5000, maximumAge: 60000 }
      );
    });

  const handlePlanDay = async () => {
    setIsPlanningDay(true);
    setDayPlan(null);
    setExcludedHcpIds([]);
    try {
      const location = await getLiveLocation();
      setUsedLiveLocation(location.latitude != null && location.longitude != null);

      const budgetMinutes = Math.round(Number(timeBudgetHours) * 60);
      const result = await priorityService.getDayPlan({
        timeBudgetMinutes: budgetMinutes,
        latitude: location.latitude,
        longitude: location.longitude,
      });
      setDayPlan(result);
      setActiveBudgetMinutes(budgetMinutes);
      loadAnalytics();
    } catch (error) {
      // Interceptor already shows a toast for this - no need to duplicate it.
    } finally {
      setIsPlanningDay(false);
    }
  };

  const handleMarkVisited = async (stop) => {
    if (visitingHcpId) return;
    setVisitingHcpId(stop.hcp_id);
    try {
      await priorityService.markDayPlanVisited(stop.hcp_id);

      const newExcluded = [...excludedHcpIds, stop.hcp_id];
      const elapsed = stop.estimated_arrival_offset_minutes + DEFAULT_VISIT_DURATION_MINUTES;
      const remainingBudget = Math.max(Math.round((activeBudgetMinutes || 0) - elapsed), 1);

      const location = await getLiveLocation();
      setUsedLiveLocation(location.latitude != null && location.longitude != null);

      const result = await priorityService.getDayPlan({
        timeBudgetMinutes: remainingBudget,
        latitude: location.latitude,
        longitude: location.longitude,
        excludeHcpIds: newExcluded,
      });

      setDayPlan(result);
      setExcludedHcpIds(newExcluded);
      setActiveBudgetMinutes(remainingBudget);
      toast.success(`${stop.name} marked visited - route updated for the rest of the day.`);
      loadAnalytics();
    } catch (error) {
      // Interceptor already shows a toast for this - no need to duplicate it.
    } finally {
      setVisitingHcpId(null);
    }
  };

  const navigateUrl = (lat, lng) =>
    `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;

  const scoreTier = (score) => {
    if (score >= 65) return styles.tierHigh;
    if (score >= 35) return styles.tierMedium;
    return styles.tierLow;
  };

  const formatGeneratedAt = (iso) => {
    if (!iso) return '';
    try {
      return new Date(iso).toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '';
    }
  };

  const formatMinutes = (minutes) => {
    const total = Math.round(minutes);
    const h = Math.floor(total / 60);
    const m = total % 60;
    if (h <= 0) return `${m}m`;
    return `${h}h ${m}m`;
  };

  return (
    <div className={styles.priorityPage}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>
            <Target size={24} className={styles.titleIcon} />
            This Week's Priorities
          </h1>
          <p className={styles.subtitle}>
            Your HCPs ranked by who needs attention this week - and why.
          </p>
        </div>
        <div className={styles.headerActions}>
          {generatedAt && !isLoading && (
            <span className={styles.generatedAt}>
              Updated {formatGeneratedAt(generatedAt)}
            </span>
          )}
          <button
            className={styles.refreshButton}
            onClick={() => loadPriorities(true)}
            disabled={isLoading || isRefreshing}
          >
            {isRefreshing ? (
              <Loader size={16} className={styles.spinning} />
            ) : (
              <RefreshCw size={16} />
            )}
            Refresh
          </button>
        </div>
      </div>

      {!isLoading && priorities.length > 0 && (
        <div className={styles.planSection}>
          <div className={styles.planHeader}>
            <div>
              <h2 className={styles.planTitle}>
                <RouteIcon size={19} className={styles.planTitleIcon} />
                Plan My Day
              </h2>
              <p className={styles.planSubtitle}>
                Pick who to visit today and in what order, based on your priorities and real travel time.
              </p>
            </div>
          </div>

          {analytics && analytics.planned_count > 0 && (
            <div className={styles.planAnalyticsStrip}>
              <BarChart3 size={15} />
              <span>
                Last {analytics.days} days: <strong>{analytics.planned_count}</strong> stops planned,{' '}
                <strong>{analytics.visited_count}</strong> visited (
                <strong>{analytics.completion_rate}%</strong> completion)
              </span>
            </div>
          )}

          <div className={styles.planControls}>
            <div className={styles.planInputGroup}>
              <label className={styles.planInputLabel} htmlFor="timeBudgetHours">
                Hours available
              </label>
              <input
                id="timeBudgetHours"
                type="number"
                min="1"
                max="12"
                step="0.5"
                className={styles.planInput}
                value={timeBudgetHours}
                onChange={(e) => setTimeBudgetHours(e.target.value)}
              />
            </div>
            <button
              className={styles.planButton}
              onClick={handlePlanDay}
              disabled={isPlanningDay}
            >
              {isPlanningDay ? (
                <Loader size={16} className={styles.spinning} />
              ) : (
                <Navigation size={16} />
              )}
              {isPlanningDay ? 'Building plan...' : 'Generate Plan'}
            </button>
            <span className={styles.planLocationNote}>
              {usedLiveLocation
                ? 'Using your live location.'
                : 'Uses your profile address if location access is off.'}
            </span>
          </div>

          {dayPlan && (
            <>
              <div className={styles.planSummary}>
                <div className={styles.planSummaryItem}>
                  <span className={styles.planSummaryValue}>{dayPlan.plan.length}</span>
                  <span className={styles.planSummaryLabel}>Stops planned</span>
                </div>
                <div className={styles.planSummaryItem}>
                  <span className={styles.planSummaryValue}>
                    {formatMinutes(dayPlan.total_time_minutes)}
                  </span>
                  <span className={styles.planSummaryLabel}>Total time (incl. visits)</span>
                </div>
                <div className={styles.planSummaryItem}>
                  <span className={styles.planSummaryValue}>{Math.round(dayPlan.total_value)}</span>
                  <span className={styles.planSummaryLabel}>Priority value covered</span>
                </div>
              </div>

              {dayPlan.plan.length === 0 && (
                <p className={styles.planEmptyNote}>
                  {excludedHcpIds.length > 0
                    ? "That's everyone for today - no more stops fit in the remaining time."
                    : "No visits fit in this time budget yet - try increasing the hours, or make sure your HCPs' addresses have been saved so they can be routed to."}
                </p>
              )}

              {dayPlan.plan.length > 0 && (
                <>
                  <div style={{ marginTop: '1rem' }}>
                    <DayPlanMap
                      repLocation={{
                        latitude: dayPlan.rep_start_latitude,
                        longitude: dayPlan.rep_start_longitude,
                      }}
                      stops={dayPlan.plan}
                    />
                  </div>

                  <div className={styles.planStopList}>
                    {dayPlan.plan.map((stop, index) => (
                      <div key={stop.hcp_id} className={styles.planStop}>
                        <div className={styles.planStopRank}>{index + 1}</div>
                        <div className={styles.planStopInfo}>
                          <p className={styles.planStopName}>{stop.name}</p>
                          <div className={styles.planStopMeta}>
                            {stop.specialty && <span>{stop.specialty}</span>}
                            <span>Priority {Math.round(stop.priority_score ?? 0)}</span>
                            <span>+{formatMinutes(stop.travel_minutes_from_previous)} travel</span>
                            <span>Arrives ~{formatMinutes(stop.estimated_arrival_offset_minutes)} in</span>
                          </div>
                        </div>
                        <div className={styles.planStopActions}>
                          <button
                            className={styles.visitedButton}
                            onClick={() => handleMarkVisited(stop)}
                            disabled={visitingHcpId === stop.hcp_id}
                          >
                            {visitingHcpId === stop.hcp_id ? (
                              <Loader size={14} className={styles.spinning} />
                            ) : (
                              <CheckCircle size={14} />
                            )}
                            Visited
                          </button>
                          <a className={styles.navigateButton} href={navigateUrl(stop.latitude, stop.longitude)} target="_blank" rel="noopener noreferrer">
                            <Navigation size={14} />
                            Navigate
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {dayPlan.skipped.length > 0 && (
                <p className={styles.planSkippedNote}>
                  Not included: {dayPlan.skipped.map((s) => s.name).join(', ')} - either
                  their address isn't set yet, or they didn't fit in today's time budget.
                </p>
              )}
            </>
          )}
        </div>
      )}

      {isLoading && (
        <div className={styles.loadingState}>
          <Loader size={22} className={styles.spinning} />
          <p>Scoring your HCPs and generating recommendations...</p>
        </div>
      )}

      {!isLoading && priorities.length === 0 && (
        <div className={styles.emptyState}>
          <Target size={32} className={styles.emptyIcon} />
          <p>No priorities yet - log a few interactions first, and this will rank who to contact next.</p>
        </div>
      )}

      {!isLoading && priorities.length > 0 && (
        <div className={styles.priorityList}>
          {priorities.map((item, index) => (
            <div key={item.hcp_id} className={styles.priorityCard}>
              <div className={styles.rank}>{index + 1}</div>

              <div className={styles.cardMain}>
                <div className={styles.cardTop}>
                  <div>
                    <h3 className={styles.hcpName}>{item.hcp_name}</h3>
                    {item.specialty && (
                      <span className={styles.specialty}>{item.specialty}</span>
                    )}
                  </div>
                  <div className={`${styles.scoreBadge} ${scoreTier(item.score)}`}>
                    {Math.round(item.score)}
                  </div>
                </div>

                <p className={styles.reason}>{item.reason}</p>

                <div className={styles.badges}>
                  <span className={styles.badge}>
                    <Clock size={13} />
                    {item.days_since_contact >= 999
                      ? 'Never contacted'
                      : `${item.days_since_contact}d since contact`}
                  </span>
                  <span className={styles.badge}>
                    <TrendingUp size={13} />
                    Engagement {item.engagement_score}/100
                  </span>
                  {item.has_pending_followup && (
                    <span className={`${styles.badge} ${styles.badgePending}`}>
                      <CalendarCheck size={13} />
                      Follow-up pending
                    </span>
                  )}
                </div>

                <div className={styles.scoreBar}>
                  <div
                    className={`${styles.scoreBarFill} ${scoreTier(item.score)}`}
                    style={{ width: `${Math.min(item.score, 100)}%` }}
                  />
                </div>
              </div>

              <div className={styles.cardActions}>
                {item.has_pending_followup && item.followup_id && (
                  <button
                    className={styles.completeButton}
                    onClick={() => handleCompleteFollowup(item)}
                    disabled={completingId === item.followup_id}
                  >
                    {completingId === item.followup_id ? (
                      <Loader size={15} className={styles.spinning} />
                    ) : (
                      <CheckCircle size={15} />
                    )}
                    Mark Complete
                  </button>
                )}
                <button
                  className={styles.logButton}
                  onClick={() => handleLogInteraction(item)}
                >
                  <MessageSquare size={15} />
                  Log Interaction
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PriorityDashboardPage;