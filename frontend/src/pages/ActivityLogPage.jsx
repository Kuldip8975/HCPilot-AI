import React, { useEffect, useState } from 'react';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { Activity, Plus, Pencil, Trash2, CheckCircle2, FileClock } from 'lucide-react';

import { auditService } from '../services/auditService';
import { Loading } from '../components/common/Loading';
import styles from './ActivityLogPage.module.css';

const ACTION_ICON = {
  create: Plus,
  update: Pencil,
  delete: Trash2,
  complete: CheckCircle2,
};

const ACTION_COLOR = {
  create: '#16a34a',
  update: '#2563eb',
  delete: '#dc2626',
  complete: '#7c3aed',
};

const RESOURCE_LABEL = {
  interaction: 'Interaction',
  followup: 'Follow-up',
  hcp: 'HCP',
};

const describe = (log) => {
  const resource = RESOURCE_LABEL[log.resource] || log.resource;
  const action = log.action;
  const verb = {
    create: 'created',
    update: 'updated',
    delete: 'deleted',
    complete: 'completed',
  }[action] || action;
  return `${resource} ${verb}`;
};

const formatChanges = (changes) => {
  if (!changes || typeof changes !== 'object') return null;
  const entries = Object.entries(changes).filter(([, v]) => v !== null && v !== undefined && v !== '');
  if (entries.length === 0) return null;
  return entries.map(([key, value]) => `${key}: ${String(value)}`).join('  ·  ');
};

/**
 * ActivityLogPage - a simple, honest compliance/audit trail: every
 * interaction/follow-up/HCP create, update, delete or complete the
 * current user has done, most recent first, with what changed.
 */
export const ActivityLogPage = () => {
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await auditService.getMyActivity(200);
        setLogs(data || []);
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to load activity log.');
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  if (isLoading) {
    return <Loading message="Loading activity log..." />;
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Activity Log</h1>
          <p className={styles.subtitle}>
            Every change you've made - HCPs, visits, and follow-ups - kept as an audit trail.
          </p>
        </div>
      </div>

      {error && <div className={styles.errorBanner}>{error}</div>}

      {logs.length === 0 ? (
        <div className={styles.emptyState}>
          <FileClock size={32} />
          <p>No activity recorded yet.</p>
        </div>
      ) : (
        <div className={styles.logList}>
          {logs.map((log) => {
            const Icon = ACTION_ICON[log.action] || Activity;
            const color = ACTION_COLOR[log.action] || '#64748b';
            const changesText = formatChanges(log.changes);
            return (
              <div key={log.id} className={styles.logRow}>
                <div className={styles.logIcon} style={{ backgroundColor: `${color}1a`, color }}>
                  <Icon size={16} />
                </div>
                <div className={styles.logBody}>
                  <div className={styles.logHeadline}>{describe(log)}</div>
                  {changesText && <div className={styles.logChanges}>{changesText}</div>}
                  <div className={styles.logMeta}>
                    {log.resource_id && <span className={styles.logId}>#{log.resource_id.slice(0, 8)}</span>}
                    <span>
                      {(() => {
                        try {
                          return formatDistanceToNow(parseISO(log.created_at), { addSuffix: true });
                        } catch {
                          return log.created_at;
                        }
                      })()}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ActivityLogPage;