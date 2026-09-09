import React from "react";
import { Sparkles, Shield, Compass, Heart, ArrowUpRight } from "lucide-react";

const TEACHINGS = [
  {
    id: "naam-mahiman",
    number: "०१",
    icon: Sparkles,
    tag: "Radha Naam",
    accentColor: "#EA580C",
    accentBg: "#FFF7ED",
    borderColor: "#FDBA74",
    titleHindi: "नाम महिमा की सर्वोपरिता",
    titleEnglish: "The Supreme Efficacy of the Holy Name",
    verse: "॥ कलि केवल नाम अधारा, सुमिरि सुमिरि नर उतरहिं पारा ॥",
    summaryHindi:
      "कलियुग में किसी कठिन तप या यज्ञ की आवश्यकता नहीं। श्वास-श्वास में निरंतर 'श्री राधा' नाम का जप ही समस्त विकारों, पूर्व संचित पापों और जन्म-मरण के बंधन को नष्ट करने का एकमात्र अचूक साधन है।",
    summaryEnglish:
      "In this age, elaborate rituals yield to the singular shelter of the Divine Name. Incessant inner repetition of 'Shri Radha' with every breath purifies latent karmic impressions and dissolves worldly attachment.",
    queryKey: "Radha Naam"
  },
  {
    id: "mana-nigraha",
    number: "०२",
    icon: Shield,
    tag: "Mind Discipline",
    accentColor: "#D97706",
    accentBg: "#FEF3C7",
    borderColor: "#FCD34D",
    titleHindi: "मन का निग्रह एवं साक्षी भाव",
    titleEnglish: "Restraint of Mind & Detached Witnessing",
    verse: "॥ मन जीते जग जीत, मन हारे सब हार ॥",
    summaryHindi:
      "मन का स्वभाव चंचल है। अनचाहे या कलुषित विचार आने पर उनसे द्वेष या युद्ध मत करो। तटस्थ साक्षी बनकर केवल नाम की गति तीव्र करो। नाम रूपी सूर्य के समक्ष विचारों का अंधकार स्वतः विलीन हो जाएगा।",
    summaryEnglish:
      "The mind naturally wanders. When negative or intrusive thoughts surface, do not combat them with frustration. Remain the detached observer and intensify the inner cadence of Radha Naam until they dissolve.",
    queryKey: "Mind Discipline"
  },
  {
    id: "satsang-maryada",
    number: "०३",
    icon: Compass,
    tag: "Spiritual Conduct",
    accentColor: "#C2410C",
    accentBg: "#FFEDD5",
    borderColor: "#FB923C",
    titleHindi: "सहनशीलता एवं आचरण मर्यादा",
    titleEnglish: "Endurance, Forbearance & Noble Conduct",
    verse: "॥ तुलसी मीठे बचन ते सुख उपजत चहुँ ओर ॥",
    summaryHindi:
      "कटु वचन, अपमान और सांसारिक निंदा को प्रारब्ध का शोधन मानकर मौन सहना ही उच्च कोटि की तपस्या है। किसी का दिल न दुखाना और समस्त जीवों में प्रिया-प्रियतम का भाव रखना ही साधक का सच्चा धर्म है।",
    summaryEnglish:
      "Accepting harsh speech and criticism with stoic silence is the swiftest purifier of past debts. True spiritual demeanor lies in never causing grief to another soul, seeing the Divine present in all beings.",
    queryKey: "Ekantik Vartalaap"
  },
  {
    id: "nitya-upasana",
    number: "०४",
    icon: Heart,
    tag: "Surrender",
    accentColor: "#E11D48",
    accentBg: "#FFE4E6",
    borderColor: "#FDA4AF",
    titleHindi: "अनन्य भाव एवं नित्य शरणागति",
    titleEnglish: "Exclusive Refuge & Daily Surrender",
    verse: "॥ जाहि विधि राखे राम ताहि विधि रहिए ॥",
    summaryHindi:
      "प्रिया जी के चरणों में सर्वस्व समर्पण कर देना ही शरणागति है। जो परिस्थिति मिले, उसे लाड़ली जू का प्रसाद मानकर संतुष्ट रहो। वासनाओं का त्याग और सेवा ही रस-मार्ग की पराकाष्ठा है।",
    summaryEnglish:
      "Complete surrender at Shri Radha's lotus feet means embracing every life condition as Her benign will. Detachment from transient desires and quiet, loving remembrance form the pinnacle of Rasik devotion.",
    queryKey: "Youth Guidance"
  }
];

export default function CoreTeachings({ onSelectTopic }) {
  return (
    <section
      id="teachings"
      className="section-padding"
      style={{
        backgroundColor: "#FFFDF9",
        backgroundImage: "radial-gradient(circle at 50% 10%, rgba(254, 243, 199, 0.4) 0%, transparent 60%)"
      }}
    >
      <div className="site-container">
        {/* Editorial Section Header */}
        <div style={{ marginBottom: "var(--space-10)" }}>
          <div className="section-label">
            <span className="bullet"></span>
            सिद्धान्त एवं स्तम्भ • FUNDAMENTAL PILLARS
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
                  color: "var(--color-navy-shyam)",
                  letterSpacing: "-0.02em",
                  marginBottom: "var(--space-2)"
                }}
              >
                साधना के चार आधार स्तम्भ
              </h2>
              <p
                style={{
                  color: "var(--color-text-muted)",
                  fontSize: "1rem",
                  maxWidth: "620px",
                  lineHeight: "1.6"
                }}
              >
                पूज्य महाराज जी द्वारा प्रतिपादित चार नित्य साधना स्तम्भ जो माया के वेग से रक्षा कर अंतःकरण में निर्मल प्रेम का प्राकट्य करते हैं।
              </p>
            </div>

            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.8rem",
                fontWeight: 700,
                color: "#B45309",
                letterSpacing: "0.08em",
                backgroundColor: "#FEF3C7",
                padding: "6px 14px",
                borderRadius: "var(--radius-pill)",
                border: "1px solid #FCD34D"
              }}
            >
              RADHA KELI KUNJ DOCTRINE [IV]
            </div>
          </div>
        </div>

        {/* 4-Column Vibrant Planar Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "var(--space-6)"
          }}
        >
          {TEACHINGS.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.id}
                className="planar-card"
                style={{
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  height: "100%",
                  backgroundColor: "#FFFFFF",
                  border: `1.5px solid ${item.borderColor}`,
                  borderRadius: "10px",
                  padding: "var(--space-6)",
                  boxShadow: "0 8px 24px rgba(180, 83, 9, 0.07)",
                  position: "relative",
                  overflow: "hidden",
                  cursor: "pointer"
                }}
                onClick={() => onSelectTopic && onSelectTopic(item.queryKey)}
              >
                {/* Vibrant Top Accent Bar */}
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    height: "5px",
                    background: `linear-gradient(90deg, ${item.accentColor}, #F59E0B)`
                  }}
                />

                {/* Card Content */}
                <div>
                  {/* Icon & Category Header */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "var(--space-4)"
                    }}
                  >
                    <div
                      style={{
                        width: "42px",
                        height: "42px",
                        borderRadius: "8px",
                        backgroundColor: item.accentBg,
                        border: `1.5px solid ${item.borderColor}`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: item.accentColor,
                        boxShadow: `0 2px 10px ${item.accentColor}25`
                      }}
                    >
                      <Icon size={20} strokeWidth={2.2} />
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span
                        style={{
                          padding: "3px 10px",
                          borderRadius: "9999px",
                          backgroundColor: item.accentBg,
                          border: `1px solid ${item.borderColor}`,
                          color: item.accentColor,
                          fontSize: "11px",
                          fontFamily: "var(--font-mono)",
                          fontWeight: 700,
                          letterSpacing: "0.04em"
                        }}
                      >
                        {item.tag}
                      </span>
                      <span
                        style={{
                          fontFamily: "var(--font-serif)",
                          fontSize: "1.3rem",
                          fontWeight: 800,
                          color: item.accentColor
                        }}
                      >
                        {item.number}
                      </span>
                    </div>
                  </div>

                  {/* Title */}
                  <h3
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: "1.35rem",
                      fontWeight: 700,
                      color: "var(--color-navy-shyam)",
                      marginBottom: "3px",
                      lineHeight: "1.3"
                    }}
                  >
                    {item.titleHindi}
                  </h3>

                  <div
                    style={{
                      fontSize: "0.825rem",
                      fontWeight: 600,
                      color: item.accentColor,
                      marginBottom: "var(--space-4)"
                    }}
                  >
                    {item.titleEnglish}
                  </div>

                  {/* Sacred Shloka Box with Rich Warm Glow */}
                  <div
                    className="shloka-box"
                    style={{
                      marginBottom: "var(--space-4)"
                    }}
                  >
                    {item.verse}
                  </div>

                  {/* Summaries */}
                  <p
                    style={{
                      fontSize: "0.875rem",
                      lineHeight: "1.65",
                      color: "#292524",
                      marginBottom: "var(--space-3)",
                      fontWeight: 400
                    }}
                  >
                    {item.summaryHindi}
                  </p>

                  <p
                    style={{
                      fontSize: "0.8125rem",
                      lineHeight: "1.55",
                      color: "#78716C"
                    }}
                  >
                    {item.summaryEnglish}
                  </p>
                </div>

                {/* Footer Action */}
                <div
                  style={{
                    paddingTop: "var(--space-3)",
                    marginTop: "var(--space-4)",
                    borderTop: "1px solid rgba(245, 158, 11, 0.2)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center"
                  }}
                >
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      color: item.accentColor
                    }}
                  >
                    प्रवचन देखें • View Discourses
                  </span>
                  <div
                    style={{
                      width: "28px",
                      height: "28px",
                      borderRadius: "50%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      backgroundColor: item.accentBg,
                      color: item.accentColor,
                      border: `1px solid ${item.borderColor}`
                    }}
                  >
                    <ArrowUpRight size={15} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
