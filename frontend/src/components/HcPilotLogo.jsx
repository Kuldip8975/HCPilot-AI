import React from 'react';

/**
 * HcPilot AI brand logo.
 * A gradient tile with an interlocked H + C monogram and a subtle medical cross.
 *
 * @param {number} size   - overall pixel size (default 36)
 * @param {string} variant - 'default' | 'light' (light = white tile, colored mark)
 */
export const HcPilotLogo = ({ size = 36, variant = 'default' }) => {
  const isLight = variant === 'light';
  const gradientId = `hcp-grad-${variant}`;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="HcPilot AI logo"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#3b82f6" />
          <stop offset="55%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>

      {/* Rounded tile background */}
      <rect
        x="0"
        y="0"
        width="48"
        height="48"
        rx="12"
        fill={isLight ? '#ffffff' : `url(#${gradientId})`}
        stroke={isLight ? '#e2e8f0' : 'none'}
        strokeWidth={isLight ? 1 : 0}
      />

      {/* H + C monogram */}
      <g
        stroke={isLight ? `url(#${gradientId})` : '#ffffff'}
        strokeWidth="2.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      >
        {/* Left vertical of H */}
        <path d="M14 14 V34" />
        {/* Right vertical of H */}
        <path d="M24 14 V34" />
        {/* H crossbar */}
        <path d="M14 24 H24" />
        {/* C curve (attached, reads as C for Clinera/Care) */}
        <path d="M34 17.5 A8.5 8.5 0 1 0 34 30.5" />
      </g>

      {/* Small pulse dot — "AI signal" accent */}
      <circle
        cx="34"
        cy="24"
        r="2.2"
        fill={isLight ? `url(#${gradientId})` : '#ffffff'}
        opacity="0.9"
      />
    </svg>
  );
};

export default HcPilotLogo;