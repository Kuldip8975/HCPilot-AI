import React from 'react';
import PropTypes from 'prop-types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import styles from './StatCard.module.css';

/**
 * StatCard — displays a single KPI with icon, value, and trend pill.
 */
export const StatCard = ({
  title,
  value,
  icon: Icon,
  color,
  trend,
  trendDirection = 'neutral',
}) => {
  const isPositive = trendDirection === 'up';
  const isNegative = trendDirection === 'down';

  return (
    <div className={styles.statCard}>
      <div className={styles.statHeader}>
        <div
          className={styles.statIcon}
          style={{
            background: `linear-gradient(135deg, ${color}, ${color}cc)`,
          }}
        >
          <Icon size={20} color="#ffffff" />
        </div>

        {trend && (
          <div
            className={`${styles.trend} ${
              isPositive
                ? styles.positive
                : isNegative
                ? styles.negative
                : styles.neutral
            }`}
          >
            {isPositive && <TrendingUp size={14} />}
            {isNegative && <TrendingDown size={14} />}
            {!isPositive && !isNegative && <Minus size={14} />}
            <span>{trend}</span>
          </div>
        )}
      </div>

      <div className={styles.statBody}>
        <div className={styles.statValue}>{value}</div>
        <div className={styles.statTitle}>{title}</div>
      </div>
    </div>
  );
};

StatCard.propTypes = {
  title: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  icon: PropTypes.elementType.isRequired,
  color: PropTypes.string.isRequired,
  trend: PropTypes.string,
  trendDirection: PropTypes.oneOf(['up', 'down', 'neutral']),
};

export default StatCard;