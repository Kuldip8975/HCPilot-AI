import React, { useMemo } from 'react';
import PropTypes from 'prop-types';
import styles from './WeeklyActivityChart.module.css';

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const TRACK_HEIGHT = 120;   // px — matches CSS .barTrack height

export const WeeklyActivityChart = ({ interactions = [] }) => {
  const { data, maxCount, totalThisWeek } = useMemo(() => {
    const days = [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let i = 6; i >= 0; i--) {
      const day = new Date(today);
      day.setDate(day.getDate() - i);
      days.push({ date: day, count: 0 });
    }

    interactions.forEach((interaction) => {
      const rawDate =
        interaction.interaction_date ||
        interaction.date ||
        interaction.created_at;
      if (!rawDate) return;

      const interactionDate = new Date(rawDate);
      interactionDate.setHours(0, 0, 0, 0);

      const match = days.find(
        (d) => d.date.getTime() === interactionDate.getTime()
      );
      if (match) match.count += 1;
    });

    const max = Math.max(...days.map((d) => d.count), 1);
    const total = days.reduce((sum, d) => sum + d.count, 0);
    return { data: days, maxCount: max, totalThisWeek: total };
  }, [interactions]);

  return (
    <div className={styles.chartCard}>
      <div className={styles.chartHeader}>
        <h3 className={styles.chartTitle}>Weekly Activity</h3>
        <span className={styles.chartSubtitle}>
          {totalThisWeek > 0
            ? `${totalThisWeek} interaction${totalThisWeek === 1 ? '' : 's'} logged this week`
            : 'No interactions logged in the last 7 days'}
        </span>
      </div>

      <div className={styles.barsRow}>
        {data.map((day, index) => {
          // Compute bar height in px directly — no % surprises
          const barHeight =
            day.count > 0
              ? Math.max((day.count / maxCount) * TRACK_HEIGHT, 8)
              : 4;

          const isToday = index === data.length - 1;
          const label = DAY_LABELS[day.date.getDay()];

          return (
            <div
              key={day.date.toISOString()}
              className={styles.barColumn}
              title={`${label}: ${day.count} interaction${day.count === 1 ? '' : 's'}`}
            >
              <span className={styles.barCount}>
                {day.count > 0 ? day.count : ''}
              </span>

              <div className={styles.barTrack}>
                <div
                  className={`${styles.bar} ${isToday ? styles.barToday : ''}`}
                  style={{ height: `${barHeight}px` }}
                />
              </div>

              <span
                className={`${styles.barLabel} ${
                  isToday ? styles.barLabelToday : ''
                }`}
              >
                {label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

WeeklyActivityChart.propTypes = {
  interactions: PropTypes.array,
};

export default WeeklyActivityChart;