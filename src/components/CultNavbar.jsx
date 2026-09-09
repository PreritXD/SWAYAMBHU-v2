import React from 'react';
import { ArrowUpRight } from 'lucide-react';

export default function CultNavbar({ onChatClick }) {
  return (
    <header className="cult-header" role="banner">
      <div className="cult-header-inner">
        {/* Left: Cult UI Dot Monogram & Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
          <a
            href="/"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '9px',
              textDecoration: 'none',
              color: '#09090B'
            }}
          >
            {/* Cult UI 7-dot cluster logo */}
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              style={{ display: 'inline-block' }}
            >
              <circle cx="12" cy="12" r="2.2" fill="#09090B" />
              <circle cx="12" cy="5" r="2" fill="#09090B" />
              <circle cx="12" cy="19" r="2" fill="#09090B" />
              <circle cx="5" cy="8.5" r="2" fill="#09090B" />
              <circle cx="19" cy="8.5" r="2" fill="#09090B" />
              <circle cx="5" cy="15.5" r="2" fill="#09090B" />
              <circle cx="19" cy="15.5" r="2" fill="#09090B" />
            </svg>
            <span
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '17px',
                fontWeight: 800,
                letterSpacing: '-0.03em',
                color: '#09090B'
              }}
            >
              cult ui
            </span>
          </a>

          {/* Navigation Links */}
          <nav
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
            className="hide-mobile"
          >
            <a
              href="#satsang-chat"
              onClick={(e) => {
                e.preventDefault();
                if (onChatClick) onChatClick();
                else document.getElementById('satsang-chat')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="cult-nav-item"
            >
              Components
            </a>

            <a
              href="#satsang-chat"
              onClick={(e) => {
                e.preventDefault();
                if (onChatClick) onChatClick();
                else document.getElementById('satsang-chat')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="cult-nav-item"
            >
              <span>Discourses</span>
              <span className="cult-nav-badge">438+ new</span>
              <ArrowUpRight size={13} style={{ color: '#71717A' }} />
            </a>

            <a
              href="#satsang-chat"
              onClick={(e) => {
                e.preventDefault();
                if (onChatClick) onChatClick();
                else document.getElementById('satsang-chat')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="cult-nav-item"
            >
              <span>Council Mode</span>
              <span className="cult-nav-badge">2 new</span>
              <ArrowUpRight size={13} style={{ color: '#71717A' }} />
            </a>

            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="cult-nav-item"
            >
              <span>Docs</span>
              <ArrowUpRight size={13} style={{ color: '#71717A' }} />
            </a>
          </nav>
        </div>

        {/* Right Actions: Cult Pro black pill, GitHub 6.0k, Social icon */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => {
              if (onChatClick) onChatClick();
              else document.getElementById('satsang-chat')?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="cult-btn-black"
          >
            Ask Satsang AI
          </button>

          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="cult-btn-outline"
            style={{ height: '36px', padding: '0 14px', fontSize: '12.5px' }}
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
            <span>6.0k</span>
          </a>

          {/* X / Twitter icon */}
          <a
            href="https://x.com"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              color: '#52525B',
              textDecoration: 'none',
              transition: 'color 0.15s ease'
            }}
            title="Follow on X"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
            </svg>
          </a>
        </div>
      </div>
    </header>
  );
}
