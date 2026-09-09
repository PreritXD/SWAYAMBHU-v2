import React from 'react';
import { Home, BookOpen, ExternalLink, Sparkles } from 'lucide-react';

export default function LiquidNavbar({ onHomeClick }) {
  return (
    <header className="liquid-navbar" role="banner">
      {/* Brand Monogram & Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #EA580C 0%, #9A3412 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFDF9',
            fontSize: '16px',
            fontWeight: 'bold',
            fontFamily: 'var(--font-devanagari)',
            boxShadow: '0 4px 12px rgba(234, 88, 12, 0.35)',
            border: '1.5px solid rgba(255, 255, 255, 0.7)'
          }}
        >
          राधा
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span
            style={{
              fontFamily: 'var(--font-serif)',
              fontSize: '15px',
              fontWeight: 700,
              color: '#78350F',
              letterSpacing: '0.02em',
              lineHeight: 1.2
            }}
          >
            श्री राधा केली कुंज
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '10.5px',
              fontWeight: 700,
              color: '#C2410C',
              letterSpacing: '0.06em',
              textTransform: 'uppercase'
            }}
          >
            Swayambhu Satsang AI
          </span>
        </div>
      </div>

      {/* Navigation Links: Home, Docs, GitHub */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {/* Home */}
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            if (onHomeClick) onHomeClick();
            else window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
          className="liquid-nav-link"
          title="गृह पृष्ठ (Home)"
        >
          <Home size={15} />
          <span>Home</span>
        </a>

        {/* Docs */}
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="liquid-nav-link"
          title="FastAPI Interactive API Documentation"
        >
          <BookOpen size={15} />
          <span>Docs</span>
        </a>

        {/* GitHub */}
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="liquid-nav-link"
          title="Source Code on GitHub"
        >
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="currentColor"
            style={{ display: 'inline-block' }}
          >
            <path
              fillRule="evenodd"
              clipRule="evenodd"
              d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
            />
          </svg>
          <span>GitHub</span>
        </a>
      </nav>
    </header>
  );
}
