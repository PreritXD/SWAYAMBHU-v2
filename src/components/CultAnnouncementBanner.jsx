import React from 'react';
import { ArrowRight } from 'lucide-react';

export default function CultAnnouncementBanner({ onBannerClick }) {
  return (
    <aside
      className="cult-announcement-bar"
      onClick={(e) => {
        if (onBannerClick) {
          e.preventDefault();
          onBannerClick();
        }
      }}
      style={{ cursor: 'pointer' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ opacity: 0.35 }}>—</span>
        <span className="cult-announcement-badge">NEW</span>
        <span style={{ fontWeight: 700 }}>SATSANG RAG v2.0</span>
        <span style={{ opacity: 0.5 }}>/</span>
        <span>13,968+ Verbatim Discourses & 438+ Audio Files — Just ask</span>
        <ArrowRight size={13} style={{ display: 'inline-block', marginLeft: '2px' }} />
        <span style={{ opacity: 0.35 }}>—</span>
      </div>
    </aside>
  );
}
