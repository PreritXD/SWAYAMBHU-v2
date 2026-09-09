import React from "react";
import { Clock, ShieldAlert, MapPin, CheckCircle2, Moon, Sparkles } from "lucide-react";
import { DAILY_SCHEDULE_DATA } from "../data/discourses";

const ASHRAM_REGULATIONS = [
  {
    titleHindi: "पूर्ण मौन एवं शांति मर्यादा",
    titleEnglish: "Strict Silence Inside Ashram Grounds",
    descHindi: "आश्रम परिसर एवं सत्संग कक्ष में अनावश्यक वार्तालाप, वाद-विवाद अथवा सांसारिक चर्चा पूर्णतः वर्जित है। केवल राधा नाम का मानसिक या मंद स्वर में जप करें।"
  },
  {
    titleHindi: "इलेक्ट्रॉनिक उपकरण एवं वीडियोग्राफी निषेध",
    titleEnglish: "Mobile Phones & Recording Devices Banned",
    descHindi: "सत्संग एवं दर्शन के समय मोबाइल फोन पूर्णतया स्विच ऑफ रखें। किसी भी प्रकार की अनधिकृत वीडियोग्राफी, रील्स अथवा फोटोग्राफी सख्त निषिद्ध है।"
  },
  {
    titleHindi: "पारंपरिक एवं मर्यादित वस्त्र परिधान",
    titleEnglish: "Sattvic & Modest Traditional Attire",
    descHindi: "साधकों के लिए मर्यादित वस्त्र (धोती-कुर्ता, कुर्ता-पायजामा, साड़ी, सलवार-कमीज) अनिवार्य हैं। पाश्चात्य परिधान या अनुचित वस्त्रों में प्रवेश वर्जित है।"
  },
  {
    titleHindi: "कोई शुल्क अथवा वीआईपी व्यवस्था नहीं",
    titleEnglish: "Absolute Sanctity: No VIP Tokens or Fees",
    descHindi: "दर्शन, सत्संग अथवा एकांतिक वार्तालाप के लिए किसी भी प्रकार का कोई शुल्क या दान नहीं लिया जाता। सभी भक्त एवं साधक श्री जी के दरबार में समान हैं।"
  }
];

export default function DailySchedule() {
  return (
    <section
      id="schedule"
      className="section-padding"
      style={{
        background: "linear-gradient(180deg, #070C18 0%, #0F1A30 50%, #070C18 100%)",
        color: "#FFFFFF",
        position: "relative",
        overflow: "hidden",
        borderTop: "3px solid #D97706",
        borderBottom: "3px solid #D97706"
      }}
    >
      {/* Background Subtle Constellation Mesh */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "radial-gradient(circle at 50% 20%, rgba(245, 158, 11, 0.12) 0%, transparent 60%)",
          pointerEvents: "none"
        }}
      />

      <div className="site-container" style={{ position: "relative", zIndex: 1 }}>
        {/* Section Header */}
        <div style={{ marginBottom: "var(--space-10)" }}>
          <div
            className="section-label"
            style={{
              backgroundColor: "rgba(245, 158, 11, 0.15)",
              borderColor: "rgba(245, 158, 11, 0.4)",
              color: "#FDE047"
            }}
          >
            <span
              className="bullet"
              style={{ backgroundColor: "#FDE047", boxShadow: "0 0 8px #FDE047" }}
            ></span>
            दैनिक आश्रम चर्या • ASHRAM TIMETABLE & PROTOCOLS
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-end",
              flexWrap: "wrap",
              gap: "var(--space-4)"
            }}
          >
            <div>
              <h2
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "clamp(2rem, 3.5vw, 2.75rem)",
                  fontWeight: "700",
                  color: "#FFFFFF",
                  letterSpacing: "-0.02em",
                  marginBottom: "var(--space-2)",
                  textShadow: "0 2px 10px rgba(0,0,0,0.5)"
                }}
              >
                श्री राधा केली कुंज दैनिक नियम व चर्या
              </h2>
              <p
                style={{
                  color: "rgba(255, 255, 255, 0.8)",
                  fontSize: "1rem",
                  maxWidth: "620px",
                  lineHeight: "1.6"
                }}
              >
                वृन्दावन धाम में पूज्य महाराज जी की उपस्थिति में सम्पन्न होने वाले प्रातः परिक्रमा, एकांतिक साधन, अमृत सत्संग एवं संध्या दर्शन का प्रामाणिक समय।
              </p>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 16px",
                backgroundColor: "rgba(245, 158, 11, 0.15)",
                border: "1.5px solid rgba(245, 158, 11, 0.4)",
                borderRadius: "var(--radius-pill)",
                fontFamily: "var(--font-mono)",
                fontSize: "0.8rem",
                fontWeight: 700,
                color: "#FDE047"
              }}
            >
              <MapPin size={15} />
              <span>Vrindavan Dham, Mathura (U.P.)</span>
            </div>
          </div>
        </div>

        {/* Schedule Table Container with Golden Hairlines */}
        <div
          style={{
            backgroundColor: "rgba(16, 26, 48, 0.7)",
            backdropFilter: "blur(12px)",
            border: "1.5px solid rgba(245, 158, 11, 0.3)",
            borderRadius: "10px",
            overflow: "hidden",
            boxShadow: "0 16px 40px rgba(0, 0, 0, 0.4)",
            marginBottom: "var(--space-10)"
          }}
        >
          {/* Table Header */}
          <div
            className="schedule-header-grid"
            style={{
              padding: "16px 24px",
              background: "linear-gradient(90deg, rgba(234, 88, 12, 0.25) 0%, rgba(245, 158, 11, 0.2) 100%)",
              borderBottom: "1.5px solid rgba(245, 158, 11, 0.3)",
              fontFamily: "var(--font-mono)",
              fontSize: "0.8rem",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: "#FDE047",
              fontWeight: 800
            }}
          >
            <div>समय • Time Slot</div>
            <div>अनुष्ठान एवं सेवा • Spiritual Activity</div>
            <div>साधक मर्यादा • Observance & Protocol</div>
          </div>

          {/* Table Rows */}
          {DAILY_SCHEDULE_DATA.map((slot, index) => (
            <div
              key={index}
              className="schedule-row-grid"
              style={{
                padding: "20px 24px",
                borderBottom:
                  index < DAILY_SCHEDULE_DATA.length - 1
                    ? "1px solid rgba(255, 255, 255, 0.08)"
                    : "none",
                backgroundColor: index % 2 === 0 ? "rgba(255, 255, 255, 0.02)" : "transparent",
                transition: "background 0.2s ease"
              }}
            >
              {/* Time Column */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.95rem",
                  color: "#FDE047",
                  fontWeight: 700
                }}
              >
                <Clock size={16} style={{ color: "#F59E0B" }} />
                <span>{slot.time}</span>
              </div>

              {/* Activity Column */}
              <div style={{ paddingRight: "var(--space-4)" }}>
                <div
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.15rem",
                    fontWeight: 700,
                    color: "#FFFFFF",
                    marginBottom: "3px"
                  }}
                >
                  {slot.activityHindi}
                </div>
                <div
                  style={{
                    fontSize: "0.825rem",
                    color: "rgba(254, 240, 138, 0.7)",
                    fontWeight: 500
                  }}
                >
                  {slot.activityEnglish}
                </div>
              </div>

              {/* Etiquette Column */}
              <div>
                <div
                  style={{
                    fontSize: "0.9rem",
                    color: "rgba(255, 255, 255, 0.9)",
                    marginBottom: "3px"
                  }}
                >
                  {slot.etiquetteHindi}
                </div>
                <div
                  style={{
                    fontSize: "0.8rem",
                    color: "rgba(255, 255, 255, 0.55)",
                    fontStyle: "italic"
                  }}
                >
                  {slot.etiquetteEnglish}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Ashram Regulations & Sanctity Box */}
        <div
          style={{
            background: "linear-gradient(135deg, rgba(234, 88, 12, 0.15) 0%, rgba(245, 158, 11, 0.08) 100%)",
            border: "2px solid rgba(245, 158, 11, 0.4)",
            borderRadius: "10px",
            padding: "var(--space-8)",
            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)"
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-3)",
              marginBottom: "var(--space-6)"
            }}
          >
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "8px",
                backgroundColor: "rgba(245, 158, 11, 0.2)",
                border: "1.5px solid #FCD34D",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#FDE047"
              }}
            >
              <ShieldAlert size={22} />
            </div>
            <div>
              <h3
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.4rem",
                  fontWeight: 700,
                  color: "#FFFFFF",
                  margin: 0
                }}
              >
                आश्रम मर्यादा एवं दर्शन नियम • Ashram Conduct & Protocols
              </h3>
              <p
                style={{
                  fontSize: "0.85rem",
                  color: "rgba(254, 240, 138, 0.85)",
                  margin: 0,
                  marginTop: "2px",
                  fontWeight: 500
                }}
              >
                श्री राधा केली कुंज में पधारने वाले सभी वैष्णवों एवं साधकों से सादर विनम्र अनुरोध
              </p>
            </div>
          </div>

          {/* 4 Regulation Cards */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
              gap: "var(--space-5)"
            }}
          >
            {ASHRAM_REGULATIONS.map((rule, idx) => (
              <div
                key={idx}
                style={{
                  padding: "var(--space-4)",
                  backgroundColor: "rgba(10, 17, 32, 0.6)",
                  border: "1px solid rgba(245, 158, 11, 0.2)",
                  borderRadius: "8px"
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    marginBottom: "6px"
                  }}
                >
                  <CheckCircle2 size={17} color="#F59E0B" />
                  <h4
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: "1.05rem",
                      fontWeight: 700,
                      color: "#FFFFFF",
                      margin: 0
                    }}
                  >
                    {rule.titleHindi}
                  </h4>
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.725rem",
                    color: "#FDE047",
                    letterSpacing: "0.04em",
                    marginBottom: "8px",
                    fontWeight: 700
                  }}
                >
                  {rule.titleEnglish}
                </div>
                <p
                  style={{
                    fontSize: "0.85rem",
                    color: "rgba(255, 255, 255, 0.8)",
                    lineHeight: "1.6",
                    margin: 0
                  }}
                >
                  {rule.descHindi}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
