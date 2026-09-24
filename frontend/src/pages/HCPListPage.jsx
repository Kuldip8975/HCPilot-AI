import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Search, Plus, Filter, ArrowUpDown } from 'lucide-react';

import { HCPCard } from '../components/hcp/HCPCard';
import { HCPFilters } from '../components/hcp/HCPFilters';
import { Loading } from '../components/common/Loading';
import { ROUTES } from '../routes/RouteConstants';
import { fetchHCPs, selectHCPs, selectHCPsLoading } from '../redux/slices/hcpSlice';

import styles from './HCPListPage.module.css';

/**
 * HCPListPage Component
 * Displays a list of HCPs with search, filter, and sort capabilities
 * (fetches real data from the backend instead of mock data)
 */
export const HCPListPage = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const apiHCPs = useSelector(selectHCPs);
  const isLoading = useSelector(selectHCPsLoading);

  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('name');

  useEffect(() => {
    dispatch(fetchHCPs({}));
  }, [dispatch]);

  // Map backend field names -> the shape HCPCard expects.
  // Note: the backend's HCP model field is "address" (renamed from the
  // older "location"), so this reads hcp.address - reading hcp.location
  // here would always be undefined and the card would always show "-".
  const hcps = useMemo(() => {
    return (apiHCPs || []).map((hcp) => ({
      id: hcp.id,
      name: hcp.name,
      title: hcp.title || hcp.specialty || 'HCP',
      specialty: hcp.specialty || 'â€”',
      email: hcp.email || '',
      phone: hcp.phone || '',
      location: hcp.address || 'â€”',
      lastInteraction: hcp.last_interaction || null,
      interactionCount: hcp.interaction_count ?? 0,
      status: hcp.status || 'active',
    }));
  }, [apiHCPs]);

  // Filter and search logic
  const filteredHCPs = hcps.filter((hcp) => {
    const q = searchQuery.toLowerCase();
    return (
      hcp.name.toLowerCase().includes(q) ||
      (hcp.specialty || '').toLowerCase().includes(q) ||
      (hcp.location || '').toLowerCase().includes(q)
    );
  });

  // Sort logic
  const sortedHCPs = [...filteredHCPs].sort((a, b) => {
    if (sortBy === 'name') {
      return a.name.localeCompare(b.name);
    } else if (sortBy === 'lastInteraction') {
      if (!a.lastInteraction) return 1;
      if (!b.lastInteraction) return -1;
      return new Date(b.lastInteraction) - new Date(a.lastInteraction);
    } else if (sortBy === 'interactionCount') {
      return b.interactionCount - a.interactionCount;
    }
    return 0;
  });

  const handleViewHCP = (id) => {
    navigate(`/hcps/${id}`);
  };

  const handleLogInteraction = (id) => {
    navigate(ROUTES.INTERACTION_NEW, { state: { hcpId: id } });
  };

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
  };

  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };

  return (
    <div className={styles.hcpListPage}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Healthcare Professionals</h1>
          <p className={styles.subtitle}>
            Manage and view all HCPs in your network
          </p>
        </div>
        <button
          className={styles.addButton}
          onClick={() => navigate('/hcps/create')}
        >
          <Plus size={18} />
          Add HCP
        </button>
      </div>

      {/* Search and Filters */}
      <div className={styles.searchSection}>
        <div className={styles.searchBar}>
          <Search size={20} className={styles.searchIcon} />
          <input
            type="text"
            placeholder="Search by name, specialty, or location..."
            value={searchQuery}
            onChange={handleSearchChange}
            className={styles.searchInput}
          />
          {searchQuery && (
            <button className={styles.clearSearch} onClick={handleClearSearch}>
              âœ•
            </button>
          )}
        </div>
        <div className={styles.filterActions}>
          <button
            className={`${styles.filterButton} ${showFilters ? styles.active : ''}`}
            onClick={toggleFilters}
          >
            <Filter size={18} />
            Filters
          </button>
          <div className={styles.sortWrapper}>
            <ArrowUpDown size={18} />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className={styles.sortSelect}
            >
              <option value="name">Sort by Name</option>
              <option value="lastInteraction">Sort by Recent</option>
              <option value="interactionCount">Sort by Interactions</option>
            </select>
          </div>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <HCPFilters
          onClose={() => setShowFilters(false)}
          onApply={(filters) => {
            dispatch(fetchHCPs(filters));
            setShowFilters(false);
          }}
        />
      )}

      {/* Results */}
      {isLoading ? (
        <Loading message="Loading HCPs..." />
      ) : (
        <div className={styles.resultsSection}>
          <div className={styles.resultsHeader}>
            <span className={styles.resultCount}>
              {sortedHCPs.length} HCP{sortedHCPs.length !== 1 ? 's' : ''} found
            </span>
          </div>

          <div className={styles.hcpGrid}>
            {sortedHCPs.map((hcp) => (
              <HCPCard
                key={hcp.id}
                hcp={hcp}
                onView={handleViewHCP}
                onLogInteraction={handleLogInteraction}
              />
            ))}
          </div>

          {sortedHCPs.length === 0 && (
            <div className={styles.emptyState}>
              <p>No HCPs found matching your search.</p>
              <button className={styles.clearFiltersButton} onClick={handleClearSearch}>
                Clear search
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default HCPListPage;