import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { X, Check, ChevronDown } from 'lucide-react';

import styles from './HCPFilters.module.css';

/**
 * HCPFilters Component
 * Filter panel for HCP search with multiple filter options
 */
export const HCPFilters = ({ onClose, onApply }) => {
  const [filters, setFilters] = useState({
    specialty: [],
    status: [],
    location: '',
  });

  const specialties = [
    'Oncology',
    'Cardiology',
    'Pediatrics',
    'Neurology',
    'Dermatology',
    'Orthopedics',
    'Radiology',
    'Surgery',
  ];

  const statuses = [
    { value: 'active', label: 'Active' },
    { value: 'inactive', label: 'Inactive' },
    { value: 'pending', label: 'Pending' },
  ];

  const toggleSpecialty = (specialty) => {
    setFilters((prev) => ({
      ...prev,
      specialty: prev.specialty.includes(specialty)
        ? prev.specialty.filter((s) => s !== specialty)
        : [...prev.specialty, specialty],
    }));
  };

  const toggleStatus = (status) => {
    setFilters((prev) => ({
      ...prev,
      status: prev.status.includes(status)
        ? prev.status.filter((s) => s !== status)
        : [...prev.status, status],
    }));
  };

  const handleLocationChange = (e) => {
    setFilters((prev) => ({
      ...prev,
      location: e.target.value,
    }));
  };

  const handleApply = () => {
    onApply(filters);
  };

  const handleReset = () => {
    setFilters({
      specialty: [],
      status: [],
      location: '',
    });
  };

  const hasActiveFilters = () => {
    return filters.specialty.length > 0 || 
           filters.status.length > 0 || 
           filters.location !== '';
  };

  return (
    <div className={styles.filtersPanel}>
      <div className={styles.filtersHeader}>
        <h3 className={styles.filtersTitle}>Filters</h3>
        <button className={styles.closeButton} onClick={onClose}>
          <X size={20} />
        </button>
      </div>

      <div className={styles.filtersBody}>
        {/* Specialty Filter */}
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel}>Specialty</label>
          <div className={styles.specialtyGrid}>
            {specialties.map((specialty) => (
              <button
                key={specialty}
                className={`${styles.specialtyButton} ${
                  filters.specialty.includes(specialty) ? styles.active : ''
                }`}
                onClick={() => toggleSpecialty(specialty)}
              >
                {filters.specialty.includes(specialty) && <Check size={14} />}
                {specialty}
              </button>
            ))}
          </div>
        </div>

        {/* Status Filter */}
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel}>Status</label>
          <div className={styles.statusGroup}>
            {statuses.map((status) => (
              <button
                key={status.value}
                className={`${styles.statusButton} ${
                  filters.status.includes(status.value) ? styles.active : ''
                }`}
                onClick={() => toggleStatus(status.value)}
              >
                {filters.status.includes(status.value) && <Check size={14} />}
                {status.label}
              </button>
            ))}
          </div>
        </div>

        {/* Location Filter */}
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel}>Location</label>
          <input
            type="text"
            placeholder="Enter location..."
            value={filters.location}
            onChange={handleLocationChange}
            className={styles.locationInput}
          />
        </div>
      </div>

      <div className={styles.filtersFooter}>
        {hasActiveFilters() && (
          <button className={styles.resetButton} onClick={handleReset}>
            Reset Filters
          </button>
        )}
        <div className={styles.actions}>
          <button className={styles.cancelButton} onClick={onClose}>
            Cancel
          </button>
          <button className={styles.applyButton} onClick={handleApply}>
            Apply Filters
          </button>
        </div>
      </div>
    </div>
  );
};

HCPFilters.propTypes = {
  onClose: PropTypes.func.isRequired,
  onApply: PropTypes.func.isRequired,
};

export default HCPFilters;