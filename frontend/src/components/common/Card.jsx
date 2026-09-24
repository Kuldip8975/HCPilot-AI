import React from 'react';
import PropTypes from 'prop-types';
import clsx from 'clsx';

import styles from './Card.module.css';

/**
 * Card Component
 * Reusable card with header, body, and footer sections
 */
export const Card = ({
  children,
  title,
  subtitle,
  headerActions,
  footer,
  className,
  bodyClassName,
  headerClassName,
  footerClassName,
  noPadding = false,
  ...props
}) => {
  return (
    <div className={clsx(styles.card, className)} {...props}>
      {(title || subtitle || headerActions) && (
        <div className={clsx(styles.header, headerClassName)}>
          <div className={styles.headerContent}>
            {title && <h3 className={styles.title}>{title}</h3>}
            {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
          </div>
          {headerActions && (
            <div className={styles.headerActions}>{headerActions}</div>
          )}
        </div>
      )}
      <div className={clsx(styles.body, { [styles.noPadding]: noPadding }, bodyClassName)}>
        {children}
      </div>
      {footer && (
        <div className={clsx(styles.footer, footerClassName)}>
          {footer}
        </div>
      )}
    </div>
  );
};

Card.propTypes = {
  children: PropTypes.node.isRequired,
  title: PropTypes.node,
  subtitle: PropTypes.node,
  headerActions: PropTypes.node,
  footer: PropTypes.node,
  className: PropTypes.string,
  bodyClassName: PropTypes.string,
  headerClassName: PropTypes.string,
  footerClassName: PropTypes.string,
  noPadding: PropTypes.bool,
};

export default Card;