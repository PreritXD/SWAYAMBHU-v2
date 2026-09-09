import React from "react";
import { VANI_QUOTES } from "../data/discourses";

export default function VaniMarquee() {
  const quotesStream = [...VANI_QUOTES, ...VANI_QUOTES];

  return (
    <div
      style={{
        background: "linear-gradient(90deg, #7C2D12 0%, #9A3412 15%, #C2410C 35%, #EA580C 50%, #C2410C 65%, #9A3412 85%, #7C2D12 100%)",
        borderTop: "2px solid #FCD34D",
        borderBottom: "2px solid #FCD34D",
        boxShadow: "0 4px 20px rgba(194, 65, 12, 0.25)",
        overflow: "hidden",
        position: "relative",
        padding: "14px 0",
        whiteSpace: "nowrap"
      }}
      className="vani-marquee-container"
    >
      <div
        className="marquee-track"
        style={{
          display: "inline-flex",
          alignItems: "center",
          animation: "marqueeScroll 40s linear infinite",
          willChange: "transform"
        }}
      >
        {quotesStream.map((item, idx) => {
          const isGlyph = item === "◆";
          return (
            <span
              key={idx}
              style={{
                display: "inline-flex",
                alignItems: "center",
                margin: "0 20px",
                fontFamily: "var(--font-serif)",
                fontSize: isGlyph ? "0.9rem" : "1.05rem",
                fontWeight: isGlyph ? "800" : "600",
                color: isGlyph ? "#FDE047" : "#FFFFFF",
                textShadow: isGlyph ? "0 0 10px rgba(253, 224, 71, 0.8)" : "0 1px 3px rgba(0, 0, 0, 0.4)",
                letterSpacing: "0.03em"
              }}
            >
              {isGlyph ? "❖" : item}
            </span>
          );
        })}
      </div>

      <style>{`
        @keyframes marqueeScroll {
          0% {
            transform: translateX(0%);
          }
          100% {
            transform: translateX(-50%);
          }
        }
        .vani-marquee-container:hover .marquee-track {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
}
