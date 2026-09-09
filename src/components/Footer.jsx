import React from "react";
import { Heart, ExternalLink, ShieldCheck, MapPin, Command, Sparkles } from "lucide-react";

export default function Footer({ onOpenSearch }) {
  return (
    <footer
      style={{
        background: "linear-gradient(180deg, #090E1A 0%, #050810 100%)",
        borderTop: "2px solid #D97706",
        color: "#FFFFFF",
        padding: "var(--space-16) 0 var(--space-8) 0",
        position: "relative"
      }}
    >
      <div className="site-container">
        {/* 4-Column Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "var(--space-8)",
            marginBottom: "var(--space-10)"
          }}
        >
          {/* Column 1: Brand & Tradition */}
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-3)",
                marginBottom: "var(--space-4)"
              }}
            >
              <div
                style={{
                  width: "38px",
                  height: "38px",
                  borderRadius: "8px",
                  background: "linear-gradient(135deg, #EA580C 0%, #C2410C 100%)",
                  color: "#FFFFFF",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontFamily: "var(--font-serif)",
                  fontWeight: "700",
                  fontSize: "1rem",
                  border: "1.5px solid #FCD34D",
                  boxShadow: "0 2px 10px rgba(234, 88, 12, 0.4)"
                }}
              >
                श्री
              </div>
              <span
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.25rem",
                  fontWeight: "700",
                  color: "#FFFFFF"
                }}
              >
                श्री राधा केली कुंज
              </span>
            </div>

            <p
              style={{
                fontSize: "0.85rem",
                color: "rgba(255, 255, 255, 0.75)",
                lineHeight: "1.7",
                marginBottom: "var(--space-4)"
              }}
            >
              पूज्य श्री हित प्रेमानंद जी महाराज के पावन मार्गदर्शन में श्री हित हरिवंश महाप्रभु की रस-रीति एवं राधा नाम के अनन्य आश्रय का डिजिटल संरक्षण।
            </p>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-2)",
                fontSize: "0.8rem",
                fontFamily: "var(--font-mono)",
                color: "#FDE047",
                fontWeight: 600
              }}
            >
              <MapPin size={15} color="#F59E0B" />
              <span>Vrindavan Dham, Mathura, UP</span>
            </div>
          </div>

          {/* Column 2: Quick Index */}
          <div>
            <h4
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.8rem",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: "#FDE047",
                fontWeight: 800,
                marginBottom: "var(--space-4)"
              }}
            >
              विषय सूची • EXPLORE
            </h4>

            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: 0,
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-3)",
                fontSize: "0.85rem"
              }}
            >
              <li>
                <a
                  href="#teachings"
                  style={{ color: "rgba(255, 255, 255, 0.8)", textDecoration: "none" }}
                  onMouseEnter={(e) => (e.target.style.color = "#F59E0B")}
                  onMouseLeave={(e) => (e.target.style.color = "rgba(255, 255, 255, 0.8)")}
                >
                  साधना के चार स्तम्भ (Pillars)
                </a>
              </li>
              <li>
                <a
                  href="#discourses"
                  style={{ color: "rgba(255, 255, 255, 0.8)", textDecoration: "none" }}
                  onMouseEnter={(e) => (e.target.style.color = "#F59E0B")}
                  onMouseLeave={(e) => (e.target.style.color = "rgba(255, 255, 255, 0.8)")}
                >
                  सत्संग अभिलेखागार (Discourses)
                </a>
              </li>
              <li>
                <a
                  href="#schedule"
                  style={{ color: "rgba(255, 255, 255, 0.8)", textDecoration: "none" }}
                  onMouseEnter={(e) => (e.target.style.color = "#F59E0B")}
                  onMouseLeave={(e) => (e.target.style.color = "rgba(255, 255, 255, 0.8)")}
                >
                  दैनिक आश्रम चर्या (Daily Schedule)
                </a>
              </li>
              <li>
                <button
                  type="button"
                  onClick={onOpenSearch}
                  style={{
                    padding: 0,
                    cursor: "pointer",
                    fontSize: "0.85rem",
                    color: "#F59E0B",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontWeight: 600
                  }}
                >
                  <Command size={14} /> सर्व-प्रवचन खोज (Cmd + K)
                </button>
              </li>
            </ul>
          </div>

          {/* Column 3: Verified Channels */}
          <div>
            <h4
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.8rem",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: "#FDE047",
                fontWeight: 800,
                marginBottom: "var(--space-4)"
              }}
            >
              प्रामाणिक स्त्रोत • VERIFIED MEDIA
            </h4>

            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: 0,
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-3)",
                fontSize: "0.85rem"
              }}
            >
              <li>
                <a
                  href="https://www.youtube.com/@BhajanMargOfficial"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: "rgba(255, 255, 255, 0.8)",
                    textDecoration: "none",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px"
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "#F59E0B")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255, 255, 255, 0.8)")}
                >
                  Bhajan Marg Official YouTube <ExternalLink size={14} />
                </a>
              </li>
              <li>
                <a
                  href="https://vrindavanrasmahiman.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: "rgba(255, 255, 255, 0.8)",
                    textDecoration: "none",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px"
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "#F59E0B")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255, 255, 255, 0.8)")}
                >
                  Vrindavan Ras Mahiman <ExternalLink size={14} />
                </a>
              </li>
              <li>
                <span style={{ color: "rgba(255, 255, 255, 0.6)" }}>
                  श्री हित हरिवंश महाप्रभु वाणी पाठ
                </span>
              </li>
              <li>
                <span style={{ color: "rgba(255, 255, 255, 0.6)" }}>
                  नित्य प्रातः सत्संग प्रसारण (Live)
                </span>
              </li>
            </ul>
          </div>

          {/* Column 4: Sanctity Declaration */}
          <div>
            <div
              style={{
                background: "rgba(245, 158, 11, 0.08)",
                border: "1.5px solid rgba(245, 158, 11, 0.3)",
                borderRadius: "8px",
                padding: "var(--space-4)"
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  marginBottom: "8px"
                }}
              >
                <ShieldCheck size={18} color="#F59E0B" />
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.8rem",
                    fontWeight: 700,
                    color: "#FDE047",
                    textTransform: "uppercase"
                  }}
                >
                  सेवा एवं मर्यादा घोषणा
                </span>
              </div>

              <p
                style={{
                  fontSize: "0.8rem",
                  lineHeight: "1.65",
                  color: "rgba(255, 255, 255, 0.75)",
                  margin: 0
                }}
              >
                यह मंच केवल साधकों एवं भगवत्-प्रेमियों के मार्गदर्शन हेतु समर्पित है। यहाँ किसी भी प्रकार का विज्ञापन, वाणिज्यिक उत्पाद अथवा दान स्वीकार नहीं किया जाता। सर्वस्व श्री राधा रानी के चरणों में समर्पित है।
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Hairline & Disclaimer */}
        <div
          style={{
            borderTop: "1px solid rgba(245, 158, 11, 0.25)",
            paddingTop: "var(--space-6)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "var(--space-4)",
            fontSize: "0.85rem",
            color: "#FDE047",
            fontFamily: "var(--font-mono)",
            fontWeight: 600
          }}
        >
          <div>
            ॥ सर्वोपरि श्री राधा नाम ॥ श्री हित हरिवंश चन्द्रो विजयतेतराम ॥
          </div>

          <div style={{ color: "rgba(255, 255, 255, 0.6)", fontSize: "0.75rem" }}>
            Shri Radha Keli Kunj Ashram • Digital Sanctuary 2026
          </div>
        </div>
      </div>
    </footer>
  );
}
