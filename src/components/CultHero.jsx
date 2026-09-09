import React from 'react';

export default function CultHero({ onExploreClick }) {
  return (
    <section
      style={{
        paddingTop: '64px',
        paddingBottom: '32px',
        textAlign: 'center',
        maxWidth: '920px',
        margin: '0 auto',
        paddingLeft: '16px',
        paddingRight: '16px'
      }}
    >
      {/* Dual-Textured Headline: Striped scanlines + Halftone dot matrix */}
      <h1 className="cult-hero-headline">
        <span className="cult-text-striped">Shadcn,</span>
        <span className="cult-text-dotted">expanded</span>
      </h1>

      {/* Hero Subtitle */}
      <p
        style={{
          fontFamily: 'var(--font-sans)',
          fontSize: '18px',
          color: '#52525B',
          lineHeight: 1.6,
          maxWidth: '680px',
          margin: '0 auto 28px',
          fontWeight: 400
        }}
      >
        78+ animated components and effects. Free, open source, built to drop into any
        shadcn/ui project.
      </p>

      {/* Button Group */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
          flexWrap: 'wrap',
          marginBottom: '28px'
        }}
      >
        <button
          onClick={onExploreClick}
          className="cult-btn-black"
          style={{ height: '44px', padding: '0 24px', fontSize: '13px' }}
        >
          BROWSE 78 COMPONENTS
        </button>

        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="cult-btn-outline"
          style={{ height: '44px', padding: '0 24px', fontSize: '13px' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path
              fillRule="evenodd"
              clipRule="evenodd"
              d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
            />
          </svg>
          <span>GITHUB 6.0K</span>
        </a>
      </div>

      {/* Tech Stack Pills */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          flexWrap: 'wrap'
        }}
      >
        <span className="cult-tech-pill">
          <span>⚛</span>
          <span>REACT</span>
        </span>

        <span className="cult-tech-pill">
          <span>/</span>
          <span>SHADCN/UI</span>
        </span>

        <span className="cult-tech-pill">
          <span>≈</span>
          <span>TAILWIND CSS</span>
        </span>
      </div>
    </section>
  );
}
