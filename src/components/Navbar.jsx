import React, { useEffect, useRef } from "react";
import { Search, Calendar, Sparkles } from "lucide-react";
import gsap from "gsap";

export default function Navbar({ onOpenSearch }) {
  const navRef = useRef(null);

  useEffect(() => {
    let lastScrollY = window.scrollY;

    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      if (!navRef.current) return;

      if (currentScrollY > 100 && currentScrollY > lastScrollY) {
        gsap.to(navRef.current, { y: -80, duration: 0.3, ease: "power2.out" });
      } else {
        gsap.to(navRef.current, { y: 0, duration: 0.3, ease: "power2.out" });
      }
      lastScrollY = currentScrollY;
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      ref={navRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: "64px",
        backgroundColor: "rgba(250, 248, 245, 0.94)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        borderBottom: "1px solid var(--color-border-hairline)",
        zIndex: 50,
        transition: "box-shadow 0.2s ease"
      }}
    >
      <div
        className="container-rigid"
        style={{
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--space-4)"
        }}
      >
        {/* Left: Monogram & Live Status */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
          <a
            href="#"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              textDecoration: "none",
              color: "inherit"
            }}
          >
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "var(--radius-card)",
                backgroundColor: "var(--color-saffron-primary)",
                color: "#FFFFFF",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
                fontSize: "14px",
                fontFamily: "var(--font-serif)",
                letterSpacing: "-0.01em",
                border: "1px solid rgba(255, 255, 255, 0.2)"
              }}
            >
              श्री
            </div>
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span
                style={{
                  fontFamily: "var(--font-serif)",
                  fontWeight: 700,
                  fontSize: "15px",
                  lineHeight: "1.2",
                  color: "var(--color-navy-shyam)",
                  letterSpacing: "-0.01em"
                }}
              >
                श्री राधा केली कुंज
              </span>
              <span
                style={{
                  fontSize: "10px",
                  fontFamily: "var(--font-mono)",
                  color: "var(--color-text-muted)",
                  letterSpacing: "0.08em",
                  textTransform: "uppercase"
                }}
              >
                वृन्दावन धाम • Vrindavan
              </span>
            </div>
          </a>

          {/* Live Stream Status Pill */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "4px 10px",
              borderRadius: "var(--radius-pill)",
              backgroundColor: "var(--color-bg-subtle)",
              border: "1px solid var(--color-border-hairline)",
              fontSize: "11px",
              fontFamily: "var(--font-mono)",
              color: "var(--color-text-muted)"
            }}
            className="hide-mobile"
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                backgroundColor: "#10B981",
                display: "inline-block",
                boxShadow: "0 0 0 2px rgba(16, 185, 129, 0.2)"
              }}
            />
            <span>सत्संग प्रवाह सक्रिय</span>
          </div>
        </div>

        {/* Center: Desktop Nav Links */}
        <nav
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-6)",
            fontSize: "13px",
            fontWeight: 600,
            fontFamily: "var(--font-sans)"
          }}
          className="nav-links-desktop"
        >
          <a
            href="#teachings"
            style={{
              color: "var(--color-text-muted)",
              textDecoration: "none",
              transition: "color 0.15s ease"
            }}
            onMouseEnter={(e) => (e.target.style.color = "var(--color-saffron-primary)")}
            onMouseLeave={(e) => (e.target.style.color = "var(--color-text-muted)")}
          >
            साधना स्तम्भ
          </a>
          <a
            href="#discourses"
            style={{
              color: "var(--color-text-muted)",
              textDecoration: "none",
              transition: "color 0.15s ease"
            }}
            onMouseEnter={(e) => (e.target.style.color = "var(--color-saffron-primary)")}
            onMouseLeave={(e) => (e.target.style.color = "var(--color-text-muted)")}
          >
            सत्संग अभिलेखागार
          </a>
          <a
            href="#schedule"
            style={{
              color: "var(--color-text-muted)",
              textDecoration: "none",
              transition: "color 0.15s ease"
            }}
            onMouseEnter={(e) => (e.target.style.color = "var(--color-saffron-primary)")}
            onMouseLeave={(e) => (e.target.style.color = "var(--color-text-muted)")}
          >
            दैनिक दिनचर्या
          </a>
        </nav>

        {/* Right: 21st-Style Search Trigger & Schedule CTA */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
          {/* 21st Command Palette Search Button */}
          <button
            type="button"
            onClick={onOpenSearch}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              width: "220px",
              height: "38px",
              padding: "0 var(--space-3)",
              borderRadius: "var(--radius-card)",
              backgroundColor: "#FFFFFF",
              border: "1px solid var(--color-border-hairline)",
              color: "var(--color-text-muted)",
              cursor: "pointer",
              transition: "border-color 0.15s ease, box-shadow 0.15s ease",
              fontFamily: "var(--font-sans)"
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--color-saffron-primary)")}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--color-border-hairline)")}
            title="सत्संग खोजें (Cmd + K)"
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12.5px" }}>
              <Search size={14} color="var(--color-text-muted)" />
              <span>सत्संग खोजें...</span>
            </div>
            <kbd
              style={{
                display: "inline-flex",
                alignItems: "center",
                padding: "2px 6px",
                borderRadius: "3px",
                backgroundColor: "var(--color-bg-subtle)",
                fontSize: "10px",
                fontFamily: "var(--font-mono)",
                fontWeight: 600,
                color: "var(--color-text-muted)",
                border: "1px solid var(--color-border-hairline)"
              }}
            >
              ⌘K
            </kbd>
          </button>

          {/* Schedule CTA */}
          <a
            href="#schedule"
            className="btn-primary"
            style={{
              height: "38px",
              padding: "0 var(--space-4)",
              fontSize: "13px",
              fontWeight: 600
            }}
          >
            <Calendar size={14} />
            <span>दिनचर्या</span>
          </a>
        </div>
      </div>
    </header>
  );
}
