import React, { useEffect, useRef, useState } from 'react';
import HcPilotLogo from '../components/HcPilotLogo';
import { Link } from 'react-router-dom';
import {
  MessageSquare, Users, TrendingUp, Sparkles,
  ShieldCheck, CheckCircle2, ArrowRight, Play,
  Star, Lock, Zap, BarChart3, ChevronDown,
  Stethoscope, HeartPulse, Pill,
} from 'lucide-react';

import { ROUTES } from '../routes/RouteConstants';
import { SupportChatWidget } from '../components/support/SupportChatWidget';
import styles from './HomePage.module.css';

/* ---------------- Data ---------------- */

const FEATURES = [
  {
    icon: Sparkles,
    title: 'Conversational Logging',
    description: 'Describe a visit in plain language — our LangGraph agent extracts every detail automatically.',
  },
  {
    icon: Users,
    title: 'HCP Relationship Hub',
    description: 'Every Healthcare Professional, their specialty, and full interaction history in one place.',
  },
  {
    icon: ShieldCheck,
    title: 'Reviewed, Not Blind',
    description: 'AI fills the form for you, but you always review and approve before anything is saved.',
  },
  {
    icon: TrendingUp,
    title: 'Actionable Analytics',
    description: 'Track engagement trends and follow-up performance across your entire territory.',
  },
];

const STEPS = [
  {
    title: 'Describe the visit',
    description: 'Type or speak naturally — "Met Dr. Chen, discussed Product X, positive sentiment."',
    icon: MessageSquare,
  },
  {
    title: 'AI extracts the details',
    description: 'Our agent identifies the HCP, topics, and sentiment, then fills in the structured form.',
    icon: Sparkles,
  },
  {
    title: 'Review and log it',
    description: 'Check the auto-filled fields, adjust anything, and save with one click.',
    icon: CheckCircle2,
  },
];

const TRUST_BADGES = [
  { icon: ShieldCheck, label: 'HIPAA-aligned' },
  { icon: Lock, label: 'SOC 2 ready' },
  { icon: Zap, label: 'Real-time sync' },
  { icon: BarChart3, label: 'Analytics built-in' },
];

const TESTIMONIALS = [
  {
    quote: 'HcPilot AI cut my admin time in half. I log a visit in 12 seconds on the way to my car.',
    name: 'Priya R.',
    role: 'Oncology Sales Rep',
    initials: 'PR',
  },
  {
    quote: 'The AI actually understands my notes. It catches the HCP, topics, and sentiment every time.',
    name: 'Marcus T.',
    role: 'Regional Manager',
    initials: 'MT',
  },
  {
    quote: 'Our team finally has real engagement data. Follow-ups stopped falling through the cracks.',
    name: 'Aisha K.',
    role: 'Field Director',
    initials: 'AK',
  },
];

const FAQS = [
  {
    q: 'Is my data secure?',
    a: 'Yes. HcPilot AI is built with HIPAA-aligned practices and SOC 2-ready infrastructure. All data is encrypted in transit and at rest.',
  },
  {
    q: 'Can I edit what the AI logs?',
    a: 'Absolutely. The AI only fills the form — you review every field and approve before anything is saved.',
  },
  {
    q: 'Does it work on mobile?',
    a: 'Yes. HcPilot AI is fully responsive and works on phone, tablet, and desktop, so you can log visits anywhere.',
  },
  {
    q: 'How fast can my team start?',
    a: 'Most teams are up and running in under 10 minutes. No complex setup, no IT tickets.',
  },
];

/* ---------- Terminal typing scenarios (loops) ---------- */

const COMMAND_SCENARIOS = [
  {
    command: 'Met Dr. Sarah Chen, discussed Product X, positive sentiment',
    response: {
      prefix: 'Logged with ',
      highlight: 'Dr. Sarah Chen',
      suffix: ' · Oncology',
    },
  },
  {
    command: 'Visited Dr. James Patel, demoed CardioMed Plus, very interested',
    response: {
      prefix: 'Logged with ',
      highlight: 'Dr. James Patel',
      suffix: ' · Cardiology',
    },
  },
  {
    command: 'Spoke with Dr. Emily Rivera about NeuroBoost, requested samples',
    response: {
      prefix: 'Logged with ',
      highlight: 'Dr. Emily Rivera',
      suffix: ' · Neurology',
    },
  },
];

const TYPING_SPEED = 45;        // ms per character
const RESPONSE_HOLD = 3500;     // how long the response stays visible
const SCENARIO_GAP = 1500;      // pause between scenarios
const LOOP_GAP = 8000;          // ~8s after last scenario, then restart
                                // (each scenario ≈ 3-5s + 3.5s hold → loop ≈ 60s)

/* ---------------- Component ---------------- */

export const HomePage = () => {
  const [typedText, setTypedText] = useState('');
  const [showResponse, setShowResponse] = useState(false);
  const [typingDone, setTypingDone] = useState(false);
  const [scenarioIndex, setScenarioIndex] = useState(0);
  const [openFaq, setOpenFaq] = useState(0);

  const charIndexRef = useRef(0);
  const timeoutRef = useRef(null);

  // Looping terminal animation
  useEffect(() => {
    const current = COMMAND_SCENARIOS[scenarioIndex];
    const fullCommand = current.command;

    // Reset state for this scenario
    setTypedText('');
    setShowResponse(false);
    setTypingDone(false);
    charIndexRef.current = 0;

    const runScenario = () => {
      // Type next char
      if (charIndexRef.current < fullCommand.length) {
        setTypedText(fullCommand.slice(0, charIndexRef.current + 1));
        charIndexRef.current += 1;
        timeoutRef.current = setTimeout(runScenario, TYPING_SPEED);
      } else {
        // Finished typing — show response
        setTypingDone(true);
        timeoutRef.current = setTimeout(() => {
          setShowResponse(true);

          // Hold response, then move to next scenario
          timeoutRef.current = setTimeout(() => {
            const nextIndex = (scenarioIndex + 1) % COMMAND_SCENARIOS.length;

            // If we just finished the LAST scenario, add a longer pause
            const gap = nextIndex === 0 ? LOOP_GAP : SCENARIO_GAP;
            timeoutRef.current = setTimeout(() => {
              setScenarioIndex(nextIndex);
            }, gap);
          }, RESPONSE_HOLD);
        }, 350);
      }
    };

    // Small initial delay before typing starts
    timeoutRef.current = setTimeout(runScenario, 600);

    return () => clearTimeout(timeoutRef.current);
  }, [scenarioIndex]);

  const currentScenario = COMMAND_SCENARIOS[scenarioIndex];

  return (
    <div className={styles.page}>
      {/* ---------- Navbar ---------- */}
      <nav className={styles.navbar}>
        <div className={styles.navBrand}>
                  <div className={styles.navBrand}>
                      <HcPilotLogo size={36} />
                      <span className={styles.logoTitle}>HcPilot AI</span>
                  </div>

        </div>
        <div className={styles.navActions}>
          <Link to={ROUTES.LOGIN} className={styles.navLogin}>Log In</Link>
          <Link to={ROUTES.REGISTER} className={styles.navSignup}>
            Sign Up <ArrowRight size={14} />
          </Link>
        </div>
      </nav>

      {/* ---------- Hero ---------- */}
      <section className={styles.hero}>
        <div className={styles.heroText}>
          <div className={styles.heroBadge}>
            <Sparkles size={13} />
            <span>AI-powered field CRM</span>
          </div>

          <h1 className={styles.heroHeadline}>
            The AI-first CRM built for{' '}
            <span className={styles.heroHighlight}>healthcare field teams</span>
          </h1>

          <p className={styles.heroSubtext}>
            Log HCP interactions by typing or talking. Let HcPilot AI handle the busywork
            while you focus on the relationship.
          </p>

          <div className={styles.heroActions}>
            <Link to={ROUTES.REGISTER} className={styles.heroCta}>
              Get Started Free <ArrowRight size={16} />
            </Link>
            <a href="#how-it-works" className={styles.heroSecondary}>
              <span className={styles.playIcon}><Play size={12} fill="currentColor" /></span>
              See how it works
            </a>
          </div>

          <div className={styles.heroTrust}>
            {TRUST_BADGES.map(({ icon: Icon, label }) => (
              <span key={label} className={styles.trustBadge}>
                <Icon size={13} />
                {label}
              </span>
            ))}
          </div>
        </div>

        <div className={styles.heroVisual}>
          {/* Mac-style terminal */}
          <div className={styles.terminalMockup}>
            <div className={styles.terminalHeader}>
              <div className={styles.terminalDots}>
                <span className={`${styles.terminalDot} ${styles.dotRed}`} />
                <span className={`${styles.terminalDot} ${styles.dotYellow}`} />
                <span className={`${styles.terminalDot} ${styles.dotGreen}`} />
              </div>
              <span className={styles.terminalTitle}>hcpilot · log interaction</span>
            </div>

            <div className={styles.terminalBody}>
              <div className={styles.terminalLine}>
                <span className={styles.prompt}>
                  <span className={styles.promptSymbol}>❯</span>
                </span>
                <span className={styles.commandText}>{typedText}</span>
                {!typingDone && <span className={styles.typingCursor} />}
              </div>

              <div
                className={`${styles.terminalResponse} ${
                  showResponse ? styles.visible : ''
                }`}
              >
                <CheckCircle2 size={15} className={styles.responseIcon} />
                <span className={styles.responseText}>
                  {currentScenario.response.prefix}
                  <span className={styles.responseHighlight}>
                    {currentScenario.response.highlight}
                  </span>
                  {currentScenario.response.suffix}
                </span>
              </div>
            </div>
          </div>

          {/* Floating stat card */}
          <div className={styles.floatingCard}>
            <div className={styles.floatingCardIcon}>
              <Zap size={16} />
            </div>
            <div>
              <div className={styles.floatingCardValue}>12s</div>
              <div className={styles.floatingCardLabel}>avg. log time</div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- Trust strip ---------- */}
      <section className={styles.trustStrip}>
        <p className={styles.trustStripText}>Trusted by field teams across</p>
        <div className={styles.trustStripIcons}>
          <span><Stethoscope size={20} /> Oncology</span>
          <span><HeartPulse size={20} /> Cardiology</span>
          <span><Pill size={20} /> Pharma</span>
          <span><Users size={20} /> Med Devices</span>
        </div>
      </section>

      {/* ---------- Key Features ---------- */}
      <section className={styles.features}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>Features</span>
          <h2 className={styles.sectionTitle}>Everything you need, nothing you don't</h2>
          <p className={styles.sectionSubtitle}>
            Built for reps in the field — fast, simple, and intelligent.
          </p>
        </div>

        <div className={styles.featureGrid}>
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <div key={feature.title} className={styles.featureCard}>
                <div className={styles.featureIcon}>
                  <Icon size={22} />
                </div>
                <h3 className={styles.featureTitle}>{feature.title}</h3>
                <p className={styles.featureDescription}>{feature.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ---------- How it Works ---------- */}
      <section className={styles.howItWorks} id="how-it-works">
        <div className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>How it works</span>
          <h2 className={styles.sectionTitle}>Three steps. Zero friction.</h2>
          <p className={styles.sectionSubtitle}>
            From a quick note to a fully logged interaction in seconds.
          </p>
        </div>

        <div className={styles.stepsLayout}>
          <div className={styles.stepsList}>
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              return (
                <div key={step.title} className={styles.step}>
                  <div className={styles.stepMarker}>
                    <Icon size={16} />
                  </div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepNumber}>Step {index + 1}</div>
                    <h3 className={styles.stepTitle}>{step.title}</h3>
                    <p className={styles.stepDescription}>{step.description}</p>
                  </div>
                </div>
              );
            })}
            <Link to={ROUTES.REGISTER} className={styles.stepsCta}>
              Start for Free <ArrowRight size={16} />
            </Link>
          </div>

          <div className={styles.stepsVisual}>
            <div className={styles.stepsVisualInner}>
              <div className={styles.mockField}>
                <div className={styles.mockFieldLabel}>HCP</div>
                <div className={styles.mockFieldValue}>Dr. Sarah Chen</div>
              </div>
              <div className={styles.mockField}>
                <div className={styles.mockFieldLabel}>Topic</div>
                <div className={styles.mockFieldValue}>Product X</div>
              </div>
              <div className={styles.mockField}>
                <div className={styles.mockFieldLabel}>Sentiment</div>
                <div className={styles.mockFieldValue}>
                  <span className={styles.sentimentPill}>Positive</span>
                </div>
              </div>
              <div className={styles.mockField}>
                <div className={styles.mockFieldLabel}>Specialty</div>
                <div className={styles.mockFieldValue}>Oncology</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- Testimonials ---------- */}
      <section className={styles.testimonials}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>Loved by teams</span>
          <h2 className={styles.sectionTitle}>Field reps actually enjoy using it</h2>
        </div>

        <div className={styles.testimonialGrid}>
          {TESTIMONIALS.map((t) => (
            <div key={t.name} className={styles.testimonialCard}>
              <div className={styles.stars}>
                {[...Array(5)].map((_, i) => (
                  <Star key={i} size={14} fill="#fbbf24" color="#fbbf24" />
                ))}
              </div>
              <p className={styles.testimonialQuote}>"{t.quote}"</p>
              <div className={styles.testimonialAuthor}>
                <div className={styles.avatar}>{t.initials}</div>
                <div>
                  <div className={styles.authorName}>{t.name}</div>
                  <div className={styles.authorRole}>{t.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ---------- FAQ ---------- */}
      <section className={styles.faq}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>FAQ</span>
          <h2 className={styles.sectionTitle}>Questions, answered</h2>
        </div>

        <div className={styles.faqList}>
          {FAQS.map((item, index) => {
            const isOpen = openFaq === index;
            return (
              <div
                key={item.q}
                className={`${styles.faqItem} ${isOpen ? styles.faqItemOpen : ''}`}
              >
                <button
                  className={styles.faqQuestion}
                  onClick={() => setOpenFaq(isOpen ? -1 : index)}
                  aria-expanded={isOpen}
                >
                  <span>{item.q}</span>
                  <ChevronDown
                    size={18}
                    className={`${styles.faqChevron} ${
                      isOpen ? styles.faqChevronOpen : ''
                    }`}
                  />
                </button>
                <div
                  className={`${styles.faqAnswerWrapper} ${
                    isOpen ? styles.faqAnswerWrapperOpen : ''
                  }`}
                >
                  <p className={styles.faqAnswer}>{item.a}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ---------- Final CTA ---------- */}
      <section className={styles.finalCta}>
        <div className={styles.finalCtaInner}>
          <h2 className={styles.finalCtaTitle}>
            Ready to reclaim your day?
          </h2>
          <p className={styles.finalCtaText}>
            Join field teams using HcPilot AI to log faster, follow up smarter, and sell better.
          </p>
          <div className={styles.finalCtaActions}>
            <Link to={ROUTES.REGISTER} className={styles.finalCtaPrimary}>
              Get Started Free <ArrowRight size={16} />
            </Link>
            <Link to={ROUTES.LOGIN} className={styles.finalCtaSecondary}>
              Log In
            </Link>
          </div>
          <p className={styles.finalCtaNote}>No credit card required · Free to try</p>
        </div>
      </section>

      {/* ---------- Footer ---------- */}
      <footer className={styles.footer}>
        <div className={styles.footerTop}>
          <div className={styles.footerBrand}>
            <div className={styles.logoIcon}>
              <Stethoscope size={18} />
            </div>
            <span className={styles.logoTitle}>HcPilot AI</span>
          </div>
          <p className={styles.footerTagline}>AI-first CRM for healthcare field teams</p>
        </div>
        <div className={styles.footerBottom}>
          <span>© {new Date().getFullYear()} HcPilot AI. All rights reserved.</span>
          <div className={styles.footerLinks}>
            <Link to={ROUTES.LOGIN}>Log In</Link>
            <Link to={ROUTES.REGISTER}>Sign Up</Link>
          </div>
        </div>
      </footer>

      {/* RAG-powered support/FAQ chat widget for anonymous visitors */}
      <SupportChatWidget />
    </div>
  );
};

export default HomePage;