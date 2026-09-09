import React, { useEffect, useRef } from "react";
import { Search, Clock, ArrowRight, ShieldCheck, Sparkles } from "lucide-react";
import gsap from "gsap";
import ThreeCanvas from "./ThreeCanvas";

export default function HeroSection({ onOpenSearch, onExploreDiscourses }) {
  const heroRef = useRef(null);
  const badgeRef = useRef(null);
  const headingRef = useRef(null);
  const paragraphRef = useRef(null);
  const actionsRef = useRef(null);
  const metricsRef = useRef(null);
  const canvasWrapperRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      tl.from(badgeRef.current, {
        opacity: 0,
        y: -14,
        duration: 0.5
      })
        .from(
          headingRef.current,
          {
            opacity: 0,
            y: 24,
            duration: 0.7
          },
          "-=0.2"
        )
        .from(
          paragraphRef.current,
          {
            opacity: 0,
            y: 16,
            duration: 0.6
          },
          "-=0.3"
        )
        .from(
          actionsRef.current,
          {
            opacity: 0,
            y: 12,
            duration: 0.5
          },
          "-=0.3"
        )
        .from(
          metricsRef.current,
          {
            opacity: 0,
            y: 10,
            duration: 0.5
          },
          "-=0.2"
        )
        .from(
          canvasWrapperRef.current,
          {
            opacity: 0,
            scale: 0.94,
            duration: 0.8,
            ease: "back.out(1.2)"
          },
          "-=0.6"
        );
    }, heroRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={heroRef}
      style={{
        position: "relative",
        paddingTop: "calc(64px + var(--space-8))",
        paddingBottom: "var(--space-12)",
        borderBottom: "1px solid var(--color-border-gold)",
        backgroundColor: "var(--color-bg-base)",
        backgroundImage: `
          radial-gradient(circle at 90% 25%, rgba(254, 240, 138, 0.45) 0%, rgba(255, 237, 213, 0.35) 45%, rgba(255, 253, 249, 0.96) 75%),
          radial-gradient(circle at 10% 80%, rgba(254, 215, 170, 0.25) 0%, transparent 60%),
          url("./images/vrindavan_sanctum.jpg")
        `,
        backgroundSize: "cover, cover, cover",
        backgroundPosition: "center, center, center right",
        backgroundRepeat: "no-repeat",
        overflow: "hidden"
      }}
    >
      <div className="container-rigid">
        {/* Editorial 60/40 Asymmetrical Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
            gap: "var(--space-10)",
            alignItems: "center"
          }}
          className="hero-grid"
        >
          {/* Left Column (Editorial Typography) */}
          <div style={{ maxWidth: "660px" }}>
            {/* Category Overline Badge with Glow */}
            <div ref={badgeRef} style={{ marginBottom: "var(--space-4)" }}>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "5px 14px",
                  borderRadius: "var(--radius-pill)",
                  backgroundColor: "rgba(255, 255, 255, 0.92)",
                  border: "1.5px solid #FB923C",
                  boxShadow: "0 2px 12px rgba(234, 88, 12, 0.18)",
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  fontWeight: 700,
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  color: "#C2410C"
                }}
              >
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: "var(--color-saffron-primary)",
                    boxShadow: "0 0 8px var(--color-saffron-primary)"
                  }}
                />
                श्री राधा केली कुंज • एकांतिक वार्तालाप
              </span>
            </div>

            {/* Monumental Editorial Headline */}
            <h1
              ref={headingRef}
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "clamp(2.75rem, 5.5vw, 4.25rem)",
                fontWeight: 700,
                lineHeight: "1.12",
                color: "var(--color-navy-shyam)",
                letterSpacing: "-0.025em",
                marginBottom: "var(--space-4)",
                textShadow: "0 1px 2px rgba(255, 255, 255, 0.8)"
              }}
            >
              मार्ग भजन का, <br />
              <span
                style={{
                  background: "linear-gradient(135deg, #EA580C 0%, #D97706 50%, #F59E0B 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  fontStyle: "italic",
                  fontWeight: 700,
                  filter: "drop-shadow(0 2px 8px rgba(245, 158, 11, 0.3))"
                }}
              >
                समाधान
              </span>{" "}
              जीवन का।
            </h1>

            {/* Subheading / Exposition */}
            <p
              ref={paragraphRef}
              style={{
                fontSize: "clamp(1rem, 1.25vw, 1.15rem)",
                lineHeight: "1.75",
                color: "#44403C",
                marginBottom: "var(--space-8)",
                fontFamily: "var(--font-sans)",
                fontWeight: 500,
                backgroundColor: "rgba(255, 255, 255, 0.75)",
                backdropFilter: "blur(6px)",
                padding: "12px 18px",
                borderRadius: "8px",
                borderLeft: "4px solid var(--color-saffron-primary)"
              }}
            >
              पूज्य श्री हित प्रेमानंद गोविंद शरण जी महाराज के मुखारविंद से प्रमाणित
              सत्संग, नाम जप की महिमा, और जीवन की कठिनतम परिस्थितियों में आध्यात्मिक
              मार्गदर्शन। 13,968+ शब्दशः संदर्भों एवं 438+ वचनों का प्रामाणिक डिजिटल संग्रह।
            </p>

            {/* Dual Action Triggers */}
            <div
              ref={actionsRef}
              style={{
                display: "flex",
                flexWrap: "wrap",
                alignItems: "center",
                gap: "var(--space-4)",
                marginBottom: "var(--space-10)"
              }}
            >
              <button
                type="button"
                onClick={onOpenSearch}
                className="btn-primary"
                style={{
                  height: "48px",
                  padding: "0 28px",
                  fontSize: "14.5px"
                }}
              >
                <Search size={17} />
                <span>प्रवचन खोजें (Cmd + K)</span>
              </button>

              <button
                type="button"
                onClick={onExploreDiscourses}
                className="btn-outline"
                style={{
                  height: "48px",
                  padding: "0 28px",
                  fontSize: "14.5px"
                }}
              >
                <Clock size={17} color="var(--color-saffron-primary)" />
                <span>सत्संग संग्रह देखें</span>
              </button>
            </div>

            {/* 3-Column Metrics Strip */}
            <div
              ref={metricsRef}
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: "var(--space-4)",
                padding: "var(--space-4) var(--space-5)",
                backgroundColor: "rgba(255, 255, 255, 0.88)",
                backdropFilter: "blur(8px)",
                borderRadius: "8px",
                border: "1px solid var(--color-border-gold)",
                boxShadow: "0 4px 20px rgba(180, 83, 9, 0.08)"
              }}
            >
              <div>
                <span
                  style={{
                    display: "block",
                    fontFamily: "var(--font-mono)",
                    fontSize: "1.85rem",
                    fontWeight: 800,
                    color: "var(--color-navy-shyam)",
                    lineHeight: "1.2"
                  }}
                >
                  438+
                </span>
                <span
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--color-text-muted)",
                    fontWeight: 600,
                    fontFamily: "var(--font-sans)"
                  }}
                >
                  सत्संग प्रवचन
                </span>
              </div>

              <div>
                <span
                  style={{
                    display: "block",
                    fontFamily: "var(--font-mono)",
                    fontSize: "1.85rem",
                    fontWeight: 800,
                    background: "linear-gradient(135deg, #EA580C, #C2410C)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    lineHeight: "1.2"
                  }}
                >
                  13,968
                </span>
                <span
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--color-text-muted)",
                    fontWeight: 600,
                    fontFamily: "var(--font-sans)"
                  }}
                >
                  शब्दशः संदर्भ
                </span>
              </div>

              <div>
                <span
                  style={{
                    display: "block",
                    fontFamily: "var(--font-mono)",
                    fontSize: "1.85rem",
                    fontWeight: 800,
                    color: "var(--color-gold)",
                    lineHeight: "1.2"
                  }}
                >
                  100%
                </span>
                <span
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--color-text-muted)",
                    fontWeight: 600,
                    fontFamily: "var(--font-sans)"
                  }}
                >
                  प्रामाणिक संत सेवा
                </span>
              </div>
            </div>
          </div>

          {/* Right Column (Three.js WebGL Interactive Medallion Card with Golden Glow) */}
          <div
            ref={canvasWrapperRef}
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              position: "relative"
            }}
          >
            {/* Luminous Golden Aura behind the card */}
            <div
              style={{
                position: "absolute",
                width: "480px",
                height: "480px",
                borderRadius: "50%",
                background: "radial-gradient(circle, rgba(245, 158, 11, 0.4) 0%, rgba(234, 88, 12, 0.2) 40%, transparent 70%)",
                filter: "blur(30px)",
                zIndex: 0,
                pointerEvents: "none"
              }}
            />

            <div
              style={{
                position: "relative",
                zIndex: 1,
                width: "100%",
                maxWidth: "470px",
                backgroundColor: "rgba(255, 255, 255, 0.95)",
                backdropFilter: "blur(16px)",
                WebkitBackdropFilter: "blur(16px)",
                borderRadius: "12px",
                border: "2px solid #FCD34D",
                padding: "var(--space-4)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                boxShadow: "0 16px 48px rgba(180, 83, 9, 0.16), 0 0 0 1px rgba(245, 158, 11, 0.25)"
              }}
            >
              {/* Corner Architectural Frame Marks in Gold */}
              <div
                style={{
                  position: "absolute",
                  top: "6px",
                  left: "10px",
                  fontFamily: "var(--font-mono)",
                  fontSize: "13px",
                  fontWeight: 700,
                  color: "#D97706",
                  userSelect: "none"
                }}
              >
                ┌
              </div>
              <div
                style={{
                  position: "absolute",
                  top: "6px",
                  right: "10px",
                  fontFamily: "var(--font-mono)",
                  fontSize: "13px",
                  fontWeight: 700,
                  color: "#D97706",
                  userSelect: "none"
                }}
              >
                ┐
              </div>
              <div
                style={{
                  position: "absolute",
                  bottom: "6px",
                  left: "10px",
                  fontFamily: "var(--font-mono)",
                  fontSize: "13px",
                  fontWeight: 700,
                  color: "#D97706",
                  userSelect: "none"
                }}
              >
                └
              </div>
              <div
                style={{
                  position: "absolute",
                  bottom: "6px",
                  right: "10px",
                  fontFamily: "var(--font-mono)",
                  fontSize: "13px",
                  fontWeight: 700,
                  color: "#D97706",
                  userSelect: "none"
                }}
              >
                ┘
              </div>

              {/* Card Header with Golden Highlight */}
              <div
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  paddingBottom: "var(--space-3)",
                  borderBottom: "1px solid rgba(245, 158, 11, 0.25)",
                  fontSize: "12px",
                  fontFamily: "var(--font-mono)",
                  color: "var(--color-text-muted)"
                }}
              >
                <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <ShieldCheck size={16} color="var(--color-saffron-primary)" />
                  <strong style={{ color: "var(--color-navy-shyam)", fontSize: "12.5px" }}>
                    श्री राधा यंत्र • WebGL 3D
                  </strong>
                </span>
                <span
                  style={{
                    fontSize: "10px",
                    padding: "3px 8px",
                    borderRadius: "4px",
                    backgroundColor: "linear-gradient(135deg, #FEF3C7, #FDE68A)",
                    background: "#FEF3C7",
                    border: "1px solid #FCD34D",
                    color: "#B45309",
                    fontWeight: 700,
                    letterSpacing: "0.06em"
                  }}
                >
                  INTERACTIVE 3D
                </span>
              </div>

              {/* Three.js Interactive Medallion Canvas Container */}
              <div
                style={{
                  width: "100%",
                  aspectRatio: "1 / 1",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  position: "relative",
                  background: "radial-gradient(circle, rgba(254, 240, 138, 0.4) 0%, rgba(255, 237, 213, 0.2) 50%, transparent 75%)"
                }}
              >
                <ThreeCanvas />
              </div>

              {/* Card Bottom Instruction */}
              <div
                style={{
                  width: "100%",
                  paddingTop: "var(--space-3)",
                  borderTop: "1px solid rgba(245, 158, 11, 0.25)",
                  textAlign: "center",
                  fontSize: "11px",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 600,
                  color: "#B45309"
                }}
              >
                ✨ माउस अथवा उंगली घुमाकर पवित्र चक्र का 3D दर्शन करें
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
