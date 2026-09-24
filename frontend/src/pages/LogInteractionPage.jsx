import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

import InteractionForm from '../components/interactions/InteractionForm';
import ChatInterface from '../components/interactions/ChatInterface';
import { ROUTES } from '../routes/RouteConstants';

import styles from './LogInteractionPage.module.css';

export const LogInteractionPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [selectedHCP, setSelectedHCP] = useState(null);
  const formRef = useRef(null);

  useEffect(() => {
    if (location.state?.hcpId) {
      setSelectedHCP({
        id: location.state.hcpId,
        name: location.state.hcpName || 'Selected HCP',
      });
    }
  }, [location.state]);

  const handleSuccess = () => {
    navigate(ROUTES.INTERACTION_HISTORY);
  };

  const handleCancel = () => {
    navigate(-1);
  };

  // Called by the chat panel whenever the AI extracts fields from what
  // the user typed - fills in the visible form for review, doesn't save
  // anything on its own.
  const handleExtracted = (fields) => {
    formRef.current?.fillFromAI(fields);
  };

  return (
    <div className={styles.logInteractionPage}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <button className={styles.backButton} onClick={handleCancel}>
            <ArrowLeft size={20} />
            Back
          </button>
          <div>
            <h1 className={styles.title}>Log Interaction</h1>
            {selectedHCP && (
              <p className={styles.subtitle}>
                Logging interaction with: <strong>{selectedHCP.name}</strong>
              </p>
            )}
          </div>
        </div>
      </div>

      <div className={styles.splitContent}>
        <div className={styles.formPanel}>
          <InteractionForm
            ref={formRef}
            initialHCP={selectedHCP}
            onSuccess={handleSuccess}
            onCancel={handleCancel}
          />
        </div>
        <div className={styles.chatPanel}>
          <ChatInterface
            initialHCP={selectedHCP}
            onExtracted={handleExtracted}
            onCancel={handleCancel}
          />
        </div>
      </div>
    </div>
  );
};

export default LogInteractionPage;