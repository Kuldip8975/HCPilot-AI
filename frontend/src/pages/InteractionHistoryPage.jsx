import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Search, Filter, ArrowUpDown, Plus, X } from 'lucide-react';
import { toast } from 'react-toastify';

import {
  fetchInteractions,
  updateInteraction,
  selectInteractions,
  selectInteractionsLoading,
  selectInteractionFilters,
  setFilters,
} from '../redux/slices/interactionSlice';
import { followupService } from '../services/followupService';
import { InteractionCard } from '../components/interactions/InteractionCard';
import { Loading } from '../components/common/Loading';
import { ROUTES } from '../routes/RouteConstants';
import styles from './InteractionHistoryPage.module.css';

export const InteractionHistoryPage = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const interactions = useSelector(selectInteractions);
  const isLoading = useSelector(selectInteractionsLoading);
  const filters = useSelector(selectInteractionFilters);

  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  // Real follow-up records, keyed by interaction_id, so each interaction
  // card can show its ACTUAL scheduled follow-up date.
  const [followUpsByInteraction, setFollowUpsByInteraction] = useState({});

  // "View Details" -> the raw interaction object to show read-only.
  const [viewingInteraction, setViewingInteraction] = useState(null);
  // "Edit" -> a form-state copy of the raw interaction, editable.
  const [editingInteraction, setEditingInteraction] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    dispatch(fetchInteractions(filters));
  }, [dispatch, filters]);

  const loadFollowUps = async () => {
    try {
      const list = await followupService.getFollowups();
      const map = {};
      (list || []).forEach((f) => {
        if (!map[f.interaction_id] || f.status === 'pending') {
          map[f.interaction_id] = f;
        }
      });
      setFollowUpsByInteraction(map);
    } catch (err) {
      console.error('Failed to load follow-ups:', err);
    }
  };

  useEffect(() => {
    loadFollowUps();
  }, []);

  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    dispatch(setFilters({ searchQuery: query }));
  };

  const handleFilterChange = (type) => {
    setFilterType(type);
    dispatch(setFilters({ type: type === 'all' ? null : type }));
  };

  // Instead of navigating to a details page that doesn't exist (it was
  // falling through to the catch-all route and redirecting to the
  // dashboard), open a small modal right here with everything about this
  // interaction.
  const handleViewInteraction = (id) => {
    const raw = (interactions || []).find((i) => i.id === id);
    if (raw) setViewingInteraction(raw);
  };

  const handleEditInteraction = (id) => {
    const raw = (interactions || []).find((i) => i.id === id);
    if (!raw) return;
    setEditingInteraction({
      id: raw.id,
      topics: raw.topics || '',
      summary: raw.summary || '',
      notes: raw.notes || '',
      interaction_type: raw.interaction_type || 'meeting',
    });
  };

  const closeModals = () => {
    setViewingInteraction(null);
    setEditingInteraction(null);
  };

  const handleEditFieldChange = (field, value) => {
    setEditingInteraction((prev) => ({ ...prev, [field]: value }));
  };

  const handleSaveEdit = async () => {
    if (!editingInteraction) return;
    setIsSaving(true);
    try {
      await dispatch(updateInteraction({
        id: editingInteraction.id,
        data: {
          topics: editingInteraction.topics,
          summary: editingInteraction.summary,
          notes: editingInteraction.notes,
          interaction_type: editingInteraction.interaction_type,
        },
      })).unwrap();
      toast.success('Interaction updated successfully!');
      closeModals();
      dispatch(fetchInteractions(filters));
      loadFollowUps();
    } catch (error) {
      toast.error(error || 'Failed to update interaction');
    } finally {
      setIsSaving(false);
    }
  };

  // Map backend field names to frontend expected field names
  const mapInteraction = (interaction) => {
    const realFollowUp = followUpsByInteraction[interaction.id];
    return {
      id: interaction.id,
      hcpName: interaction.hcp_name || interaction.hcpName || 'Unknown HCP',
      hcpSpecialty: interaction.hcp_specialty || interaction.hcpSpecialty || '',
      date: interaction.interaction_date || interaction.date,
      type: interaction.interaction_type || interaction.type || 'other',
      summary: interaction.summary || '',
      notes: interaction.notes || '',
      followUp: !!realFollowUp,
      followUpDate: realFollowUp?.scheduled_date || null,
      followUpStatus: realFollowUp?.status || null,
    };
  };

  const mappedInteractions = (interactions || []).map(mapInteraction);

  if (isLoading) {
    return <Loading message="Loading interactions..." />;
  }

  const viewingFollowUp = viewingInteraction ? followUpsByInteraction[viewingInteraction.id] : null;

  return (
    <div className={styles.historyPage}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Interaction History</h1>
          <p className={styles.subtitle}>View and manage all your HCP interactions</p>
        </div>
        <button className={styles.logButton} onClick={() => navigate(ROUTES.INTERACTION_NEW)}>
          <Plus size={18} /> Log New
        </button>
      </div>

      <div className={styles.controls}>
        <div className={styles.searchBar}>
          <Search size={20} className={styles.searchIcon} />
          <input
            type="text"
            placeholder="Search interactions..."
            value={searchQuery}
            onChange={handleSearch}
            className={styles.searchInput}
          />
        </div>
        <div className={styles.filterControls}>
          <div className={styles.filterGroup}>
            <Filter size={18} />
            <select value={filterType} onChange={(e) => handleFilterChange(e.target.value)} className={styles.filterSelect}>
              <option value="all">All Types</option>
              <option value="meeting">Meetings</option>
              <option value="call">Calls</option>
              <option value="email">Emails</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className={styles.filterGroup}>
            <ArrowUpDown size={18} />
            <select className={styles.filterSelect}>
              <option value="date">Sort by Date</option>
              <option value="hcp">Sort by HCP</option>
            </select>
          </div>
        </div>
      </div>

      <div className={styles.results}>
        <div className={styles.resultCount}>
          {mappedInteractions.length} interaction{mappedInteractions.length !== 1 ? 's' : ''} found
        </div>

        <div className={styles.interactionList}>
          {mappedInteractions.map((interaction) => (
            <InteractionCard
              key={interaction.id}
              interaction={interaction}
              onView={handleViewInteraction}
              onEdit={handleEditInteraction}
            />
          ))}
        </div>

        {mappedInteractions.length === 0 && (
          <div className={styles.emptyState}>
            <p>No interactions found.</p>
            <button className={styles.logButton} onClick={() => navigate(ROUTES.INTERACTION_NEW)}>
              Log your first interaction
            </button>
          </div>
        )}
      </div>

      {/* View Details modal */}
      {viewingInteraction && (
        <div className={styles.modalOverlay} onClick={closeModals}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Interaction Details</h3>
              <button className={styles.modalCloseButton} onClick={closeModals}>
                <X size={20} />
              </button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.modalRow}>
                <span className={styles.modalLabel}>HCP</span>
                <span className={styles.modalValue}>
                  {viewingInteraction.hcp_name || 'Unknown HCP'}
                  {viewingInteraction.hcp_specialty ? ` · ${viewingInteraction.hcp_specialty}` : ''}
                </span>
              </div>
              <div className={styles.modalRow}>
                <span className={styles.modalLabel}>Date</span>
                <span className={styles.modalValue}>
                  {viewingInteraction.interaction_date
                    ? new Date(viewingInteraction.interaction_date).toLocaleString()
                    : '—'}
                </span>
              </div>
              <div className={styles.modalRow}>
                <span className={styles.modalLabel}>Type</span>
                <span className={styles.modalValue}>{viewingInteraction.interaction_type || '—'}</span>
              </div>
              <div className={styles.modalRow}>
                <span className={styles.modalLabel}>Topics</span>
                <span className={styles.modalValue}>{viewingInteraction.topics || '—'}</span>
              </div>
              <div className={styles.modalRow}>
                <span className={styles.modalLabel}>Summary</span>
                <span className={styles.modalValue}>{viewingInteraction.summary || '—'}</span>
              </div>
              <div className={styles.modalRow}>
                <span className={styles.modalLabel}>Notes</span>
                <span className={styles.modalValue}>{viewingInteraction.notes || '—'}</span>
              </div>
              <div className={styles.modalRow}>
                <span className={styles.modalLabel}>Follow-up</span>
                <span className={styles.modalValue}>
                  {viewingFollowUp
                    ? `${new Date(viewingFollowUp.scheduled_date).toLocaleString()} (${viewingFollowUp.status}, ${viewingFollowUp.priority} priority)`
                    : 'None scheduled'}
                </span>
              </div>
            </div>
            <div className={styles.modalFooter}>
              <button className={`${styles.modalButton} ${styles.modalButtonSecondary}`} onClick={closeModals}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit modal */}
      {editingInteraction && (
        <div className={styles.modalOverlay} onClick={closeModals}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Edit Interaction</h3>
              <button className={styles.modalCloseButton} onClick={closeModals}>
                <X size={20} />
              </button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.modalRow}>
                <span className={styles.modalLabel}>Type</span>
                <select
                  className={styles.modalSelect}
                  value={editingInteraction.interaction_type}
                  onChange={(e) => handleEditFieldChange('interaction_type', e.target.value)}
                >
                  <option value="meeting">Meeting</option>
                  <option value="call">Call</option>
                  <option value="email">Email</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className={styles.modalRow}>
                <span className={styles.modalLabel}>Topics</span>
                <input
                  type="text"
                  className={styles.modalInput}
                  value={editingInteraction.topics}
                  onChange={(e) => handleEditFieldChange('topics', e.target.value)}
                />
              </div>
              <div className={styles.modalRow}>
                <span className={styles.modalLabel}>Summary</span>
                <textarea
                  className={styles.modalTextarea}
                  value={editingInteraction.summary}
                  onChange={(e) => handleEditFieldChange('summary', e.target.value)}
                />
              </div>
              <div className={styles.modalRow}>
                <span className={styles.modalLabel}>Notes</span>
                <textarea
                  className={styles.modalTextarea}
                  value={editingInteraction.notes}
                  onChange={(e) => handleEditFieldChange('notes', e.target.value)}
                />
              </div>
            </div>
            <div className={styles.modalFooter}>
              <button className={`${styles.modalButton} ${styles.modalButtonSecondary}`} onClick={closeModals} disabled={isSaving}>
                Cancel
              </button>
              <button className={`${styles.modalButton} ${styles.modalButtonPrimary}`} onClick={handleSaveEdit} disabled={isSaving}>
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractionHistoryPage;