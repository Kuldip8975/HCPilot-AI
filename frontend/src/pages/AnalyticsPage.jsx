import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { TrendingUp, Users, MessageSquare, Calendar, Activity, PieChart } from 'lucide-react';

import { fetchInteractions, selectInteractions } from '../redux/slices/interactionSlice';
import { fetchHCPs, selectHCPs } from '../redux/slices/hcpSlice';
import { Loading } from '../components/common/Loading';
import styles from './AnalyticsPage.module.css';

export const AnalyticsPage = () => {
  const dispatch = useDispatch();
  const interactions = useSelector(selectInteractions);
  const hcps = useSelector(selectHCPs);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30days');

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await Promise.all([
        dispatch(fetchInteractions({ limit: 1000 })),
        dispatch(fetchHCPs({ limit: 100 })),
      ]);
      setIsLoading(false);
    };
    loadData();
  }, [dispatch]);

  // Calculate metrics
  // Calculate metrics
  const getHcpId = (i) => i.hcp_id ?? i.hcpId;
  const getInteractionType = (i) => i.interaction_type ?? i.interactionType ?? i.type;
  const getFollowUpRequired = (i) => i.follow_up_required ?? i.followUpRequired;
  const getHcpName = (i) => i.hcp_name ?? i.hcpName;
  const getHcpSpecialty = (i) => i.hcp_specialty ?? i.hcpSpecialty;

  const totalInteractions = interactions.length;
  const uniqueHCPs = new Set(interactions.map(getHcpId)).size;
  const followUps = interactions.filter(getFollowUpRequired).length;
  const engagementRate = hcps.length > 0 ? Math.round((uniqueHCPs / hcps.length) * 100) : 0;

  const metrics = [
    { id: 1, title: 'Total Interactions', value: totalInteractions, icon: MessageSquare, color: '#2563eb', change: '+12.5%', trend: 'up' },
    { id: 2, title: 'Active HCPs', value: uniqueHCPs, icon: Users, color: '#7c3aed', change: '+8.3%', trend: 'up' },
    { id: 3, title: 'Follow-up Rate', value: `${followUps}`, icon: Calendar, color: '#f59e0b', change: '+5.2%', trend: 'up' },
    { id: 4, title: 'Engagement Score', value: `${engagementRate}%`, icon: TrendingUp, color: '#22c55e', change: '+3.1%', trend: 'up' },
  ];

  // Interaction types breakdown
  const typeCounts = {};
  interactions.forEach(i => {
    const type = getInteractionType(i) || 'other';
    typeCounts[type] = (typeCounts[type] || 0) + 1;
  });

  const interactionTypes = Object.entries(typeCounts).map(([type, count]) => ({
    type: type.charAt(0).toUpperCase() + type.slice(1),
    count,
    color: ['#2563eb', '#7c3aed', '#f59e0b', '#64748b'][Object.keys(typeCounts).indexOf(type) % 4],
  }));

  const hcpInteractions = {};
  interactions.forEach(i => {
    const name = getHcpName(i) || 'Unknown';
    hcpInteractions[name] = (hcpInteractions[name] || 0) + 1;
  });

  const topHCPs = Object.entries(hcpInteractions)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name, count], index) => ({
      name,
      interactions: count,
      rank: index + 1,
      specialty: getHcpSpecialty(interactions.find(i => getHcpName(i) === name) || {}) || '',
    }));

  // Weekly data
  const weeklyData = [
    { day: 'Mon', interactions: Math.floor(Math.random() * 10) + 5 },
    { day: 'Tue', interactions: Math.floor(Math.random() * 10) + 8 },
    { day: 'Wed', interactions: Math.floor(Math.random() * 10) + 6 },
    { day: 'Thu', interactions: Math.floor(Math.random() * 10) + 10 },
    { day: 'Fri', interactions: Math.floor(Math.random() * 10) + 7 },
    { day: 'Sat', interactions: Math.floor(Math.random() * 5) + 2 },
    { day: 'Sun', interactions: Math.floor(Math.random() * 5) + 1 },
  ];

  const maxInteractions = Math.max(...weeklyData.map(d => d.interactions));

  if (isLoading) {
    return <Loading fullScreen message="Loading analytics..." />;
  }

  return (
    <div className={styles.analyticsPage}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Analytics</h1>
          <p className={styles.subtitle}>Track your HCP interaction performance and insights</p>
        </div>
        <div className={styles.headerControls}>
          <div className={styles.timeRangeSelector}>
            <Calendar size={18} />
            <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)} className={styles.timeSelect}>
              <option value="7days">Last 7 Days</option>
              <option value="30days">Last 30 Days</option>
              <option value="90days">Last 90 Days</option>
            </select>
          </div>
        </div>
      </div>

      <div className={styles.metricsGrid}>
        {metrics.map((metric) => (
          <div key={metric.id} className={styles.metricCard}>
            <div className={styles.metricHeader}>
              <div className={styles.metricIcon} style={{ backgroundColor: metric.color }}>
                <metric.icon size={20} color="#ffffff" />
              </div>
              <span className={`${styles.metricChange} ${styles[metric.trend]}`}>
                {metric.change}
              </span>
            </div>
            <div className={styles.metricValue}>{metric.value}</div>
            <div className={styles.metricTitle}>{metric.title}</div>
          </div>
        ))}
      </div>

      <div className={styles.chartsSection}>
        <div className={styles.chartCard}>
          <div className={styles.chartHeader}>
            <h3 className={styles.chartTitle}>
              <Activity size={18} />
              Weekly Interaction Activity
            </h3>
          </div>
          <div className={styles.barChart}>
            {weeklyData.map((data) => (
              <div key={data.day} className={styles.barGroup}>
                <div
                  className={styles.bar}
                  style={{
                    height: `${(data.interactions / maxInteractions) * 100}%`,
                    backgroundColor: data.interactions === maxInteractions ? '#2563eb' : '#93c5fd'
                  }}
                />
                <span className={styles.barLabel}>{data.day}</span>
                <span className={styles.barValue}>{data.interactions}</span>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.chartsRow}>
          <div className={styles.chartCard}>
            <div className={styles.chartHeader}>
              <h3 className={styles.chartTitle}>
                <PieChart size={18} />
                Interaction Types
              </h3>
            </div>
            <div className={styles.typeList}>
              {interactionTypes.map((type) => (
                <div key={type.type} className={styles.typeItem}>
                  <div className={styles.typeInfo}>
                    <span className={styles.typeDot} style={{ backgroundColor: type.color }} />
                    <span className={styles.typeName}>{type.type}</span>
                  </div>
                  <div className={styles.typeCount}>{type.count}</div>
                  <div className={styles.typeBar}>
                    <div
                      className={styles.typeBarFill}
                      style={{
                        width: `${(type.count / totalInteractions) * 100}%`,
                        backgroundColor: type.color
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.chartCard}>
            <div className={styles.chartHeader}>
              <h3 className={styles.chartTitle}>
                <Users size={18} />
                Top HCPs by Interactions
              </h3>
            </div>
            <div className={styles.topHCPList}>
              {topHCPs.map((hcp) => (
                <div key={hcp.name} className={styles.topHCPItem}>
                  <div className={styles.topHCPRank}>#{hcp.rank}</div>
                  <div className={styles.topHCPInfo}>
                    <div className={styles.topHCPName}>{hcp.name}</div>
                    <div className={styles.topHCPSpecialty}>{hcp.specialty}</div>
                  </div>
                  <div className={styles.topHCPCount}>{hcp.interactions} interactions</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;