import React from 'react';
import CultAnnouncementBanner from './components/CultAnnouncementBanner';
import CultNavbar from './components/CultNavbar';
import CultHero from './components/CultHero';
import ChatSanctuary from './components/ChatSanctuary';
import './styles/tokens.css';

export default function App() {
  const handleScrollToChat = () => {
    const el = document.getElementById('satsang-chat');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: '#FFFFFF',
        color: '#09090B',
        display: 'flex',
        flexDirection: 'column',
        fontFamily: 'var(--font-sans)'
      }}
    >
      {/* Top Neon Lime Announcement Bar */}
      <CultAnnouncementBanner onBannerClick={handleScrollToChat} />

      {/* Cult UI Header Navigation */}
      <CultNavbar onChatClick={handleScrollToChat} />

      {/* Main Hero Section with Scanline & Dot Matrix Headline */}
      <main style={{ flex: 1 }}>
        <CultHero onExploreClick={handleScrollToChat} />

        {/* Highlighted Showcase Card hosting the Satsang Chat AI */}
        <section className="cult-showcase-container">
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              marginBottom: '24px'
            }}
          >
            <div className="cult-highlight-tag" style={{ marginBottom: '8px' }}>
              <span className="neon-pill">HIGHLIGHTED</span>
              <span>COMPONENT</span>
            </div>

            <h2
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '22px',
                fontWeight: 700,
                color: '#09090B',
                margin: '0 0 6px 0',
                letterSpacing: '-0.02em'
              }}
            >
              Shift Card
            </h2>

            <p
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '14px',
                color: '#71717A',
                margin: 0
              }}
            >
              A card that shows more detail on hover
            </p>
          </div>

          {/* Interactive Chat Sanctuary Engine */}
          <ChatSanctuary />
        </section>
      </main>

      {/* Minimal Footer */}
      <footer
        style={{
          borderTop: '1px solid #F4F4F5',
          padding: '24px',
          textAlign: 'center',
          fontSize: '13px',
          color: '#71717A',
          backgroundColor: '#FFFFFF'
        }}
      >
        <span>Cult UI • Powered by Swayambhu Satsang RAG Engine</span>
      </footer>
    </div>
  );
}
