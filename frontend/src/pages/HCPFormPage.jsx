import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';

import { hcpService } from '../services/hcpService';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Loading } from '../components/common/Loading';
import { ROUTES } from '../routes/RouteConstants';

import styles from './HCPFormPage.module.css';

const EMPTY_FORM = {
  name: '',
  title: '',
  specialty: '',
  email: '',
  phone: '',
  address: '',
  organization: '',
  status: 'active',
  notes: '',
  preferences: '',
};

/**
 * HCPFormPage - create or edit an HCP profile.
 *
 * Used for BOTH routes (HCP_CREATE "/hcps/create" and HCP_EDIT
 * "/hcps/:id/edit") - which mode it's in is decided purely by whether
 * useParams() gives an :id. In edit mode it loads the existing HCP first
 * so the form isn't blank.
 *
 * Field names here match the backend's HCPCreate/HCPUpdate schemas
 * exactly (backend/app/schemas/hcp.py) - in particular "address", not the
 * older "location" name some other pages still use.
 *
 * "address" is the only location field the rep fills in - latitude/
 * longitude are computed server-side by geocoding at save time (see
 * HCPService.create_hcp/update_hcp on the backend), so this form never
 * sends or shows raw coordinates.
 */
export const HCPFormPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);

  const [formData, setFormData] = useState(EMPTY_FORM);
  const [isLoading, setIsLoading] = useState(isEditMode);
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (!isEditMode) return;

    let cancelled = false;
    const loadHCP = async () => {
      setIsLoading(true);
      try {
        const res = await hcpService.getHCPById(id);
        const hcp = res?.data ?? res;
        if (cancelled) return;
        setFormData({
          name: hcp.name || '',
          title: hcp.title || '',
          specialty: hcp.specialty || '',
          email: hcp.email || '',
          phone: hcp.phone || '',
          address: hcp.address || '',
          organization: hcp.organization || '',
          status: hcp.status || 'active',
          notes: hcp.notes || '',
          preferences: hcp.preferences || '',
        });
      } catch (error) {
        // Interceptor already toasts the specific error (e.g. 404 if this
        // HCP doesn't exist). Send the rep back to the list rather than
        // leaving them stuck on a form that can't load.
        if (!cancelled) navigate(ROUTES.HCPS, { replace: true });
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    loadHCP();
    return () => { cancelled = true; };
  }, [id, isEditMode, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (formData.email && !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSaving(true);
    try {
      // Send "" as undefined for optional fields rather than empty
      // strings, so the backend's Optional[...] fields stay genuinely
      // empty instead of being set to "" (e.g. email: "" would fail
      // EmailStr validation on create).
      const payload = Object.fromEntries(
        Object.entries(formData).map(([k, v]) => [k, v === '' ? null : v])
      );

      if (isEditMode) {
        await hcpService.updateHCP(id, payload);
        navigate(`/hcps/${id}`);
      } else {
        const res = await hcpService.createHCP(payload);
        const created = res?.data ?? res;
        navigate(created?.id ? `/hcps/${created.id}` : ROUTES.HCPS);
      }
    } catch (error) {
      // Interceptor already toasts the specific backend error (validation,
      // duplicate email, etc.) - nothing more to show here.
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    navigate(isEditMode ? `/hcps/${id}` : ROUTES.HCPS);
  };

  if (isLoading) {
    return <Loading fullScreen message="Loading HCP..." />;
  }

  return (
    <div className={styles.formPage}>
      <div className={styles.formContainer}>
        <button className={styles.backButton} onClick={handleCancel}>
          <ArrowLeft size={18} />
          {isEditMode ? 'Back to Profile' : 'Back to HCPs'}
        </button>

        <div className={styles.formCard}>
          <h1 className={styles.title}>
            {isEditMode ? 'Edit HCP' : 'Add HCP'}
          </h1>
          <p className={styles.subtitle}>
            {isEditMode
              ? 'Update this healthcare professional\'s profile.'
              : 'Add a new healthcare professional to your network.'}
          </p>

          <form onSubmit={handleSubmit} className={styles.form}>
            <Input
              label="Full Name"
              name="name"
              type="text"
              placeholder="e.g. Dr. Sarah Chen"
              value={formData.name}
              onChange={handleChange}
              error={errors.name}
              required
            />

            <div className={styles.formRow}>
              <Input
                label="Title"
                name="title"
                type="text"
                placeholder="e.g. MD"
                value={formData.title}
                onChange={handleChange}
              />
              <Input
                label="Specialty"
                name="specialty"
                type="text"
                placeholder="e.g. Oncology"
                value={formData.specialty}
                onChange={handleChange}
              />
            </div>

            <div className={styles.formRow}>
              <Input
                label="Email"
                name="email"
                type="email"
                placeholder="doctor@example.com"
                value={formData.email}
                onChange={handleChange}
                error={errors.email}
              />
              <Input
                label="Phone"
                name="phone"
                type="tel"
                placeholder="e.g. +91 98765 43210"
                value={formData.phone}
                onChange={handleChange}
              />
            </div>

            <Input
              label="Address"
              name="address"
              type="text"
              placeholder="e.g. FC Road, Pune"
              value={formData.address}
              onChange={handleChange}
            />
            <p className={styles.fieldHint}>
              Used to plan visit routes - geocoded automatically when saved.
            </p>

            <Input
              label="Organization"
              name="organization"
              type="text"
              placeholder="e.g. City General Hospital"
              value={formData.organization}
              onChange={handleChange}
            />

            <div className={styles.fieldGroup}>
              <label className={styles.label} htmlFor="status">Status</label>
              <select
                id="status"
                name="status"
                className={styles.select}
                value={formData.status}
                onChange={handleChange}
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="pending">Pending</option>
              </select>
            </div>

            <div className={styles.fieldGroup}>
              <label className={styles.label} htmlFor="notes">Notes</label>
              <textarea
                id="notes"
                name="notes"
                className={styles.textarea}
                placeholder="Any additional notes about this HCP..."
                value={formData.notes}
                onChange={handleChange}
                rows={3}
              />
            </div>

            <div className={styles.fieldGroup}>
              <label className={styles.label} htmlFor="preferences">Communication Preferences</label>
              <textarea
                id="preferences"
                name="preferences"
                className={styles.textarea}
                placeholder="e.g. Prefers email over calls, best reached mornings..."
                value={formData.preferences}
                onChange={handleChange}
                rows={2}
              />
            </div>

            <div className={styles.formActions}>
              <Button type="button" variant="secondary" onClick={handleCancel}>
                Cancel
              </Button>
              <Button type="submit" isLoading={isSaving}>
                <Save size={16} />
                {isEditMode ? 'Save Changes' : 'Add HCP'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default HCPFormPage;