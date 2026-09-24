import React, { useState, useEffect, useMemo, forwardRef, useImperativeHandle } from 'react';
import PropTypes from 'prop-types';
import { useDispatch, useSelector } from 'react-redux';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import Select from 'react-select';
import { Calendar, User, MessageSquare } from 'lucide-react';
import { toast } from 'react-toastify';

import { createInteraction } from '../../redux/slices/interactionSlice';
import { fetchHCPs, selectHCPs, selectHCPsLoading } from '../../redux/slices/hcpSlice';
import { followupService } from '../../services/followupService';
import { Button } from '../common/Button';
import styles from './InteractionForm.module.css';

const interactionSchema = yup.object({
  hcpId: yup.string().required('HCP is required'),
  interactionDate: yup.string().required('Date is required'),
  interactionType: yup.string().required('Type is required'),
  topics: yup.string().required('Topics are required'),
  summary: yup.string().required('Summary is required'),
  notes: yup.string(),
  followUpRequired: yup.boolean(),
  // datetime-local input value, e.g. "2026-09-22T15:00" - needs both a
  // date AND a time, since the backend's double-booking check works on a
  // +/-30 minute window and the doctor's dashboard needs a real time too.
  followUpDate: yup.string().when('followUpRequired', {
    is: true,
    then: (schema) => schema.required('Follow-up date & time is required'),
    otherwise: (schema) => schema.notRequired(),
  }),
});

export const InteractionForm = forwardRef(({ initialHCP, onSuccess, onCancel }, ref) => {
  const dispatch = useDispatch();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hcps = useSelector(selectHCPs);
  const hcpsLoading = useSelector(selectHCPsLoading);

  // Load real HCPs from the backend so the user picks a valid UUID
  // instead of typing one in by hand (that was the bug: manually typed
  // values like "001" aren't valid UUIDs and the create-interaction
  // API call would fail).
  useEffect(() => {
    dispatch(fetchHCPs());
  }, [dispatch]);

  const hcpOptions = useMemo(
    () => hcps.map((hcp) => ({ value: hcp.id, label: hcp.name })),
    [hcps]
  );

  // Make sure the HCP passed in (e.g. from the HCP detail page) shows up
  // as a selected option even before the full list has loaded.
  const initialHCPOption = initialHCP?.id
    ? { value: initialHCP.id, label: initialHCP.name || 'Selected HCP' }
    : null;

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(interactionSchema),
    defaultValues: {
      hcpId: initialHCP?.id || '',
      interactionDate: new Date().toISOString().split('T')[0],
      interactionType: 'meeting',
      followUpRequired: false,
    },
  });

  const watchFollowUp = watch('followUpRequired');

  // Lets the AI chat panel fill in these exact fields for the user to
  // review before submitting - nothing here saves anything on its own.
  useImperativeHandle(ref, () => ({
    fillFromAI: (fields) => {
      if (!fields) return;
      if (fields.hcp_id) {
        setValue('hcpId', fields.hcp_id, { shouldValidate: true });
      }
      if (fields.interaction_type) {
        setValue('interactionType', fields.interaction_type);
      }
      if (fields.topics) {
        setValue('topics', fields.topics, { shouldValidate: true });
      }
      if (fields.summary) {
        setValue('summary', fields.summary, { shouldValidate: true });
      }
      if (fields.notes) {
        setValue('notes', fields.notes);
      }
      if (fields.follow_up_required) {
        setValue('followUpRequired', true);
        if (fields.follow_up_date) {
          setValue('followUpDate', fields.follow_up_date, { shouldValidate: true });
        }
      }
    },
  }));

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      // Step 1: if a follow-up was requested, check for a double-booking
      // BEFORE saving anything at all. If this time clashes, stop here -
      // nothing gets created, not even the interaction/visit.
      let scheduledIso = null;
      if (data.followUpRequired && data.followUpDate) {
        // datetime-local gives "2026-09-22T15:00" with no timezone -
        // treat it as the user's local time and convert to a proper
        // ISO string with timezone offset for the backend.
        scheduledIso = new Date(data.followUpDate).toISOString();

        const availability = await followupService.checkAvailability(data.hcpId, scheduledIso);
        if (availability && availability.available === false) {
          toast.error(availability.message || 'This HCP already has a follow-up booked around that time. Please pick a different time.');
          setIsSubmitting(false);
          return; // Stop - nothing saved.
        }
      }

      // Step 2: the time is free (or no follow-up was requested) - now
      // it's safe to actually log the interaction.
      const interactionData = {
        hcp_id: data.hcpId,
        interaction_date: data.interactionDate + 'T00:00:00Z',
        interaction_type: data.interactionType,
        topics: data.topics,
        summary: data.summary,
        notes: data.notes || '',
        follow_up_required: data.followUpRequired || false,
        follow_up_date: null,
        follow_up_priority: 'medium',
      };

      const interaction = await dispatch(createInteraction(interactionData)).unwrap();
      if (!interaction) {
        throw new Error('Failed to log interaction');
      }

      // Step 3: create the real, conflict-checked follow-up record. The
      // time was already confirmed free in Step 1, so this should
      // succeed - it's still wrapped in try/catch to handle the rare
      // case where someone else grabbed the same slot in between.
      if (data.followUpRequired && scheduledIso) {
        try {
          await followupService.createFollowup({
            interaction_id: interaction.id,
            scheduled_date: scheduledIso,
            priority: 'medium',
            notes: data.notes || '',
          });
          toast.success('Interaction logged and follow-up scheduled!');
        } catch (followupError) {
          console.error('Follow-up scheduling failed:', followupError);
          toast.error('Interaction was saved, but the follow-up could not be scheduled (someone else may have just booked that time). Please try again.');
          onSuccess();
          return;
        }
      } else {
        toast.success('Interaction logged successfully!');
      }

      onSuccess();
    } catch (error) {
      toast.error(error || 'Failed to log interaction');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className={styles.interactionForm} onSubmit={handleSubmit(onSubmit)}>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>
          <User size={18} />
          HCP Information
        </h3>
        <div className={styles.formGroup}>
          <label className={styles.label}>
            HCP <span className={styles.required}>*</span>
          </label>
          <Controller
            name="hcpId"
            control={control}
            defaultValue={initialHCP?.id || ''}
            render={({ field: { onChange, value, ref } }) => (
              <Select
                inputRef={ref}
                classNamePrefix="hcpSelect"
                className={errors.hcpId ? styles.error : ''}
                placeholder="Search for an HCP by name..."
                isLoading={hcpsLoading}
                isClearable
                options={hcpOptions}
                value={
                  hcpOptions.find((opt) => opt.value === value) ||
                  (value ? initialHCPOption : null)
                }
                onChange={(selected) => onChange(selected ? selected.value : '')}
                noOptionsMessage={() =>
                  hcpsLoading ? 'Loading HCPs...' : 'No HCPs found'
                }
              />
            )}
          />
          {errors.hcpId && (
            <span className={styles.errorMessage}>{errors.hcpId.message}</span>
          )}
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>
          <MessageSquare size={18} />
          Interaction Details
        </h3>
        <div className={styles.formRow}>
          <div className={styles.formGroup}>
            <label className={styles.label}>
              Date <span className={styles.required}>*</span>
            </label>
            <input
              type="date"
              className={`${styles.input} ${errors.interactionDate ? styles.error : ''}`}
              {...register('interactionDate')}
            />
            {errors.interactionDate && (
              <span className={styles.errorMessage}>{errors.interactionDate.message}</span>
            )}
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>
              Type <span className={styles.required}>*</span>
            </label>
            <select
              className={`${styles.input} ${styles.select} ${errors.interactionType ? styles.error : ''}`}
              {...register('interactionType')}
            >
              <option value="meeting">Meeting</option>
              <option value="call">Call</option>
              <option value="email">Email</option>
              <option value="other">Other</option>
            </select>
            {errors.interactionType && (
              <span className={styles.errorMessage}>{errors.interactionType.message}</span>
            )}
          </div>
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>
            Topics <span className={styles.required}>*</span>
          </label>
          <input
            type="text"
            className={`${styles.input} ${errors.topics ? styles.error : ''}`}
            placeholder="e.g., Clinical trial, New drug..."
            {...register('topics')}
          />
          {errors.topics && (
            <span className={styles.errorMessage}>{errors.topics.message}</span>
          )}
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>
            Summary <span className={styles.required}>*</span>
          </label>
          <textarea
            className={`${styles.input} ${styles.textarea} ${errors.summary ? styles.error : ''}`}
            placeholder="Brief summary..."
            rows={3}
            {...register('summary')}
          />
          {errors.summary && (
            <span className={styles.errorMessage}>{errors.summary.message}</span>
          )}
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>Additional Notes</label>
          <textarea
            className={`${styles.input} ${styles.textarea}`}
            placeholder="Any additional notes..."
            rows={2}
            {...register('notes')}
          />
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>
          <Calendar size={18} />
          Follow-up
        </h3>
        <div className={styles.formGroup}>
          <label className={styles.checkboxLabel}>
            <input type="checkbox" {...register('followUpRequired')} />
            Schedule follow-up
          </label>
        </div>

        {watchFollowUp && (
          <div className={styles.formGroup}>
            <label className={styles.label}>
              Follow-up Date &amp; Time <span className={styles.required}>*</span>
            </label>
            <input
              type="datetime-local"
              className={`${styles.input} ${errors.followUpDate ? styles.error : ''}`}
              {...register('followUpDate')}
            />
            {errors.followUpDate && (
              <span className={styles.errorMessage}>{errors.followUpDate.message}</span>
            )}
          </div>
        )}
      </div>

      <div className={styles.formActions}>
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" isLoading={isSubmitting}>
          {isSubmitting ? 'Logging...' : 'Log Interaction'}
        </Button>
      </div>
    </form>
  );
});

InteractionForm.displayName = 'InteractionForm';

InteractionForm.propTypes = {
  initialHCP: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
  }),
  onSuccess: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};

export default InteractionForm;