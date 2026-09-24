import React, { useState, useEffect, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Sparkles, Search, User, Calendar, Quote, Loader } from 'lucide-react';
import { toast } from 'react-toastify';

import { fetchHCPs, selectHCPs, selectHCPsLoading } from '../redux/slices/hcpSlice';
import { searchService } from '../services/searchService';
import styles from './SmartSearchPage.module.css';

/**
 * SmartSearchPage
 * Ask natural-language questions about your own past interactions.
 * Backend runs a fresh TF-IDF retrieval over the logged-in rep's own
 * interaction rows (topics/summary/notes), then asks the LLM to answer
 * grounded only in the matched interactions - so answers always come
 * with real, clickable-feeling source citations, not made-up recall.
 */
export const SmartSearchPage = () => {
  const dispatch = useDispatch();
  const hcps = useSelector(selectHCPs);
  const hcpsLoading = useSelector(selectHCPsLoading);

  const [question, setQuestion] = useState('');
  const [hcpFilter, setHcpFilter] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    dispatch(fetchHCPs());
  }, [dispatch]);

  const hcpOptions = useMemo(
    () => [...hcps].sort((a, b) => (a.name || '').localeCompare(b.name || '')),
    [hcps]
  );

  const examplePrompts = [
    'What did I discuss with doctors about clinical trials?',
    'Which HCPs mentioned concerns about side effects?',
    'Summarize my last few conversations about the new drug launch.',
  ];

  const handleAsk = async (e) => {
    e?.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      toast.error('Type a question first');
      return;
    }

    setIsAsking(true);
    setHasSearched(true);
    try {
      const result = await searchService.askAboutInteractions(
        trimmed,
        hcpFilter || null
      );
      setAnswer(result?.answer || 'No answer returned.');
      setSources(result?.sources || []);
    } catch (error) {
      const message =
        error?.response?.data?.detail || error?.message || 'Search failed. Please try again.';
      toast.error(typeof message === 'string' ? message : 'Search failed. Please try again.');
      setAnswer(null);
      setSources([]);
    } finally {
      setIsAsking(false);
    }
  };

  const handleExampleClick = (prompt) => {
    setQuestion(prompt);
  };

  const formatDate = (value) => {
    if (!value) return '';
    try {
      return new Date(value).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return value;
    }
  };

  return (
    <div className={styles.searchPage}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          <Sparkles size={24} className={styles.titleIcon} />
          Smart Search
        </h1>
        <p className={styles.subtitle}>
          Ask questions about your own logged interactions - answers are grounded
          only in what you've actually recorded.
        </p>
      </div>

      <form className={styles.searchCard} onSubmit={handleAsk}>
        <div className={styles.searchRow}>
          <div className={styles.inputWrapper}>
            <Search size={18} className={styles.inputIcon} />
            <input
              type="text"
              className={styles.questionInput}
              placeholder="e.g. What did Dr. Kuldip say about the clinical trial last month?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={isAsking}
            />
          </div>
          <select
            className={styles.hcpSelect}
            value={hcpFilter}
            onChange={(e) => setHcpFilter(e.target.value)}
            disabled={isAsking || hcpsLoading}
          >
            <option value="">All HCPs</option>
            {hcpOptions.map((hcp) => (
              <option key={hcp.id} value={hcp.id}>
                {hcp.name}
              </option>
            ))}
          </select>
          <button
            type="submit"
            className={styles.askButton}
            disabled={isAsking || !question.trim()}
          >
            {isAsking ? <Loader size={18} className={styles.spinning} /> : <Sparkles size={18} />}
            {isAsking ? 'Thinking...' : 'Ask'}
          </button>
        </div>

        {!hasSearched && (
          <div className={styles.examples}>
            <span className={styles.examplesLabel}>Try asking:</span>
            {examplePrompts.map((prompt) => (
              <button
                type="button"
                key={prompt}
                className={styles.exampleChip}
                onClick={() => handleExampleClick(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>
        )}
      </form>

      {isAsking && (
        <div className={styles.loadingState}>
          <Loader size={22} className={styles.spinning} />
          <p>Searching your interactions and generating an answer...</p>
        </div>
      )}

      {!isAsking && hasSearched && answer && (
        <div className={styles.resultsSection}>
          <div className={styles.answerCard}>
            <div className={styles.answerHeader}>
              <Sparkles size={18} className={styles.answerIcon} />
              <span>Answer</span>
            </div>
            <p className={styles.answerText}>{answer}</p>
          </div>

          {sources.length > 0 && (
            <div className={styles.sourcesSection}>
              <h3 className={styles.sourcesTitle}>
                Sources ({sources.length})
              </h3>
              <div className={styles.sourcesList}>
                {sources.map((source, idx) => (
                  <div key={source.interaction_id || idx} className={styles.sourceCard}>
                    <div className={styles.sourceMeta}>
                      <span className={styles.sourceHcp}>
                        <User size={14} />
                        {source.hcp_name || 'Unknown HCP'}
                      </span>
                      <span className={styles.sourceDate}>
                        <Calendar size={14} />
                        {formatDate(source.date)}
                      </span>
                    </div>
                    <div className={styles.sourceSnippet}>
                      <Quote size={14} className={styles.quoteIcon} />
                      <span>{source.snippet}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {sources.length === 0 && (
            <p className={styles.noSources}>
              No specific interactions matched closely enough to cite as sources.
            </p>
          )}
        </div>
      )}

      {!isAsking && hasSearched && !answer && (
        <div className={styles.emptyState}>
          <p>No answer could be generated. Try rephrasing your question.</p>
        </div>
      )}
    </div>
  );
};

export default SmartSearchPage;