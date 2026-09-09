import React, { useState, useRef, useEffect } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  RotateCw,
  Volume2,
  VolumeX,
  ExternalLink,
  Copy,
  Check,
  Tag,
  Clock,
  Calendar,
  Search,
  Sparkles,
  Radio
} from "lucide-react";
import { DISCOURSE_DATA } from "../data/discourses";

const CATEGORIES = [
  "All",
  "Radha Naam",
  "Ekantik Vartalaap",
  "Youth Guidance",
  "Mind Discipline",
  "Daily Discipline"
];

const PLAYBACK_SPEEDS = [1.0, 1.25, 1.5, 1.75];

export default function DiscourseArchive({
  selectedDiscourseId,
  onSelectDiscourse,
  activeCategoryFilter,
  onFilterCategory
}) {
  const [activeId, setActiveId] = useState(selectedDiscourseId || DISCOURSE_DATA[0].id);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [speedIndex, setSpeedIndex] = useState(0);
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState(activeCategoryFilter || "All");

  const audioRef = useRef(null);

  useEffect(() => {
    if (selectedDiscourseId && selectedDiscourseId !== activeId) {
      setActiveId(selectedDiscourseId);
      setIsPlaying(true);
    }
  }, [selectedDiscourseId]);

  useEffect(() => {
    if (activeCategoryFilter) {
      setActiveCategory(activeCategoryFilter);
    }
  }, [activeCategoryFilter]);

  const currentDiscourse =
    DISCOURSE_DATA.find((d) => d.id === activeId) || DISCOURSE_DATA[0];

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch((err) => {
          console.warn("Audio play prevented:", err);
          setIsPlaying(false);
        });
    }
  };

  const skipTime = (delta) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.max(
      0,
      Math.min(audioRef.current.duration || 0, audioRef.current.currentTime + delta)
    );
  };

  const cycleSpeed = () => {
    const nextIdx = (speedIndex + 1) % PLAYBACK_SPEEDS.length;
    setSpeedIndex(nextIdx);
    if (audioRef.current) {
      audioRef.current.playbackRate = PLAYBACK_SPEEDS[nextIdx];
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    audioRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
      setDuration(audioRef.current.duration || 0);
    }
  };

  const handleSeek = (e) => {
    const newTime = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const handleSelect = (discourse) => {
    setActiveId(discourse.id);
    if (onSelectDiscourse) onSelectDiscourse(discourse);
    setIsPlaying(true);
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      setTimeout(() => {
        audioRef.current
          ?.play()
          .then(() => setIsPlaying(true))
          .catch(() => setIsPlaying(false));
      }, 50);
    }
  };

  const handleCopyCitation = () => {
    const text = `"${currentDiscourse.snippetHindi}"\n\n- पूज्य श्री हित प्रेमानंद जी महाराज, राधा केली कुंज, वृन्दावन धाम\nप्रवचन: ${currentDiscourse.titleHindi} (${currentDiscourse.date})`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredDiscourses = DISCOURSE_DATA.filter((d) => {
    const matchesCategory =
      activeCategory === "All" || d.category === activeCategory;
    const q = searchQuery.toLowerCase().trim();
    const matchesQuery =
      !q ||
      d.titleHindi.toLowerCase().includes(q) ||
      d.titleEnglish.toLowerCase().includes(q) ||
      d.snippetHindi.toLowerCase().includes(q) ||
      d.snippetEnglish.toLowerCase().includes(q) ||
      d.tags.some((t) => t.toLowerCase().includes(q));

    return matchesCategory && matchesQuery;
  });

  const formatSeconds = (sec) => {
    if (!sec || isNaN(sec)) return "00:00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <section
      id="discourses"
      className="section-padding"
      style={{
        backgroundColor: "#FEFBF6",
        backgroundImage: "radial-gradient(circle at 80% 20%, rgba(254, 240, 138, 0.3) 0%, transparent 50%)"
      }}
    >
      <div className="site-container">
        {/* Section Header */}
        <div style={{ marginBottom: "var(--space-8)" }}>
          <div className="section-label">
            <span className="bullet"></span>
            सत्संग अभिलेखागार • ARCHIVAL REPOSITORY
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
                प्रामाणिक सत्संग एवं एकांतिक वार्तालाप
              </h2>
              <p
                style={{
                  color: "var(--color-text-muted)",
                  fontSize: "1rem",
                  maxWidth: "640px",
                  lineHeight: "1.6"
                }}
              >
                पूज्य महाराज जी के श्रीमुख से अमृतमयी वाणी, शंका-समाधान एवं साधना-रहस्य का प्रामाणिक ऑडियो एवं वाणी संग्रह।
              </p>
            </div>

            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.8rem",
                fontWeight: 700,
                color: "#C2410C",
                letterSpacing: "0.06em",
                backgroundColor: "#FFEDD5",
                padding: "6px 14px",
                borderRadius: "var(--radius-pill)",
                border: "1px solid #FDBA74"
              }}
            >
              {filteredDiscourses.length} of {DISCOURSE_DATA.length} DISCOURSES INDEXED
            </div>
          </div>
        </div>

        {/* Two-Column Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
            gap: "var(--space-8)",
            alignItems: "start"
          }}
        >
          {/* LEFT: Vibrant Devotional Audio Deck */}
          <div
            style={{
              backgroundColor: "#FFFFFF",
              border: "2px solid #FCD34D",
              borderRadius: "12px",
              padding: "var(--space-6)",
              boxShadow: "0 12px 36px rgba(180, 83, 9, 0.12)",
              position: "sticky",
              top: "84px"
            }}
          >
            {/* Shrine Artwork Banner */}
            <div
              style={{
                width: "100%",
                height: "180px",
                borderRadius: "8px",
                backgroundImage: "url('./images/shrine_altar.jpg')",
                backgroundSize: "cover",
                backgroundPosition: "center",
                position: "relative",
                overflow: "hidden",
                marginBottom: "var(--space-5)",
                border: "1px solid #FCD34D",
                boxShadow: "inset 0 0 20px rgba(0, 0, 0, 0.4)"
              }}
            >
              {/* Overlay Gradient */}
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  background: "linear-gradient(to top, rgba(9, 14, 26, 0.9) 0%, rgba(9, 14, 26, 0.3) 60%, transparent 100%)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  padding: "12px 16px"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span
                    style={{
                      padding: "3px 10px",
                      borderRadius: "9999px",
                      backgroundColor: "rgba(234, 88, 12, 0.9)",
                      color: "#FFFFFF",
                      fontSize: "11px",
                      fontFamily: "var(--font-mono)",
                      fontWeight: 700,
                      letterSpacing: "0.06em"
                    }}
                  >
                    {currentDiscourse.category}
                  </span>

                  {/* Animated Waveform Bars */}
                  <div style={{ display: "flex", alignItems: "flex-end", gap: "3px", height: "24px" }}>
                    <div className="wave-bar" style={{ animationPlayState: isPlaying ? "running" : "paused" }} />
                    <div className="wave-bar" style={{ animationDelay: "0.2s", animationPlayState: isPlaying ? "running" : "paused" }} />
                    <div className="wave-bar" style={{ animationDelay: "0.4s", animationPlayState: isPlaying ? "running" : "paused" }} />
                    <div className="wave-bar" style={{ animationDelay: "0.1s", animationPlayState: isPlaying ? "running" : "paused" }} />
                    <div className="wave-bar" style={{ animationDelay: "0.3s", animationPlayState: isPlaying ? "running" : "paused" }} />
                  </div>
                </div>

                <div>
                  <div style={{ color: "#FDE047", fontSize: "11px", fontFamily: "var(--font-mono)", fontWeight: 700, letterSpacing: "0.08em" }}>
                    श्री राधा केली कुंज • सत्संग ध्वनि
                  </div>
                  <div style={{ color: "#FFFFFF", fontFamily: "var(--font-serif)", fontSize: "1.15rem", fontWeight: 700, textShadow: "0 2px 4px rgba(0,0,0,0.8)" }}>
                    {currentDiscourse.titleHindi}
                  </div>
                </div>
              </div>
            </div>

            {/* Hidden HTML Audio element */}
            <audio
              ref={audioRef}
              src={currentDiscourse.audioUrl}
              onTimeUpdate={handleTimeUpdate}
              onEnded={() => setIsPlaying(false)}
              preload="metadata"
            />

            {/* Sub-header meta */}
            <div style={{ marginBottom: "var(--space-4)" }}>
              <p style={{ fontSize: "0.875rem", color: "#78716C", fontWeight: 600 }}>
                {currentDiscourse.titleEnglish}
              </p>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-4)",
                  marginTop: "var(--space-2)",
                  fontSize: "0.8rem",
                  color: "#B45309",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 600
                }}
              >
                <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <Calendar size={13} /> {currentDiscourse.date}
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <Clock size={13} /> {currentDiscourse.duration}
                </span>
              </div>
            </div>

            {/* Playback Scrub Bar */}
            <div style={{ marginBottom: "var(--space-4)" }}>
              <input
                type="range"
                min={0}
                max={duration || 100}
                value={currentTime}
                onChange={handleSeek}
                style={{
                  width: "100%",
                  accentColor: "var(--color-saffron-primary)",
                  cursor: "pointer",
                  height: "6px",
                  borderRadius: "3px"
                }}
              />
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "0.75rem",
                  fontFamily: "var(--font-mono)",
                  color: "#78716C",
                  marginTop: "4px",
                  fontWeight: 600
                }}
              >
                <span>{formatSeconds(currentTime)}</span>
                <span>{duration ? formatSeconds(duration) : currentDiscourse.duration}</span>
              </div>
            </div>

            {/* Audio Deck Controls with Golden Glow */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "10px 16px",
                background: "linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)",
                borderRadius: "8px",
                border: "1px solid #FCD34D",
                marginBottom: "var(--space-5)"
              }}
            >
              {/* Skip Back 10s */}
              <button
                type="button"
                onClick={() => skipTime(-10)}
                title="10s पीछे"
                style={{
                  color: "#78350F",
                  display: "flex",
                  alignItems: "center",
                  gap: "3px",
                  fontSize: "0.8rem",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 700
                }}
              >
                <RotateCcw size={17} /> 10s
              </button>

              {/* Master Play / Pause with Saffron Radiant Glow */}
              <button
                type="button"
                onClick={togglePlay}
                style={{
                  width: "52px",
                  height: "52px",
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, #EA580C 0%, #C2410C 100%)",
                  color: "#FFFFFF",
                  border: "2px solid #FCD34D",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 4px 18px rgba(234, 88, 12, 0.4)",
                  transition: "all 0.15s ease"
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.08)")}
                onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
              >
                {isPlaying ? <Pause size={22} /> : <Play size={22} style={{ marginLeft: "2px" }} />}
              </button>

              {/* Skip Forward 10s */}
              <button
                type="button"
                onClick={() => skipTime(10)}
                title="10s आगे"
                style={{
                  color: "#78350F",
                  display: "flex",
                  alignItems: "center",
                  gap: "3px",
                  fontSize: "0.8rem",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 700
                }}
              >
                10s <RotateCw size={17} />
              </button>

              {/* Playback Speed Pill */}
              <button
                type="button"
                onClick={cycleSpeed}
                title="गति बदलें"
                style={{
                  padding: "4px 10px",
                  backgroundColor: "#FFFFFF",
                  border: "1.5px solid #FCD34D",
                  borderRadius: "4px",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.8rem",
                  fontWeight: 800,
                  color: "#C2410C",
                  cursor: "pointer"
                }}
              >
                {PLAYBACK_SPEEDS[speedIndex]}x
              </button>

              {/* Volume Mute */}
              <button
                type="button"
                onClick={toggleMute}
                style={{ color: "#78350F", padding: "4px" }}
              >
                {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
              </button>
            </div>

            {/* Verified Transcript Card with Warm Sandalwood Callout */}
            <div
              style={{
                backgroundColor: "#FFFDF9",
                border: "1px solid #FDE68A",
                borderLeft: "4px solid #EA580C",
                padding: "var(--space-4)",
                borderRadius: "6px",
                marginBottom: "var(--space-4)"
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "8px"
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.75rem",
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    color: "#C2410C",
                    fontWeight: 800
                  }}
                >
                  वाणी अमृत • VERIFIED TRANSCRIPT
                </span>

                <button
                  type="button"
                  onClick={handleCopyCitation}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                    fontSize: "0.75rem",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                    color: copied ? "#16A34A" : "#B45309"
                  }}
                >
                  {copied ? (
                    <>
                      <Check size={13} color="#16A34A" /> कॉपी हुआ
                    </>
                  ) : (
                    <>
                      <Copy size={13} /> उद्धरण कॉपी करें
                    </>
                  )}
                </button>
              </div>

              <p
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.05rem",
                  lineHeight: "1.7",
                  color: "#1C1917",
                  marginBottom: "8px"
                }}
              >
                "{currentDiscourse.snippetHindi}"
              </p>

              <p
                style={{
                  fontSize: "0.825rem",
                  lineHeight: "1.6",
                  color: "#78716C",
                  borderTop: "1px dashed #FDE68A",
                  paddingTop: "6px"
                }}
              >
                "{currentDiscourse.snippetEnglish}"
              </p>
            </div>

            {/* External YouTube Link */}
            <a
              href={`https://www.youtube.com/watch?v=${currentDiscourse.videoId}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary"
              style={{
                width: "100%",
                height: "44px",
                fontSize: "0.85rem"
              }}
            >
              भजन मार्ग आधिकारिक वीडियो देखें <ExternalLink size={15} />
            </a>
          </div>

          {/* RIGHT: Filterable Discourse Feed */}
          <div>
            {/* Search Input Bar */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                backgroundColor: "#FFFFFF",
                border: "1.5px solid #FCD34D",
                borderRadius: "8px",
                padding: "8px 14px",
                marginBottom: "var(--space-4)",
                gap: "10px",
                boxShadow: "0 2px 12px rgba(180, 83, 9, 0.06)"
              }}
            >
              <Search size={18} color="var(--color-saffron-primary)" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="प्रवचन, विषय अथवा प्रश्न खोजें... Search archive..."
                style={{
                  border: "none",
                  outline: "none",
                  backgroundColor: "transparent",
                  fontSize: "0.9rem",
                  width: "100%",
                  color: "var(--color-navy-shyam)",
                  fontWeight: 500
                }}
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  style={{
                    fontSize: "0.75rem",
                    color: "var(--color-saffron-primary)",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700
                  }}
                >
                  Clear
                </button>
              )}
            </div>

            {/* Category Filter Pills */}
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "8px",
                marginBottom: "var(--space-6)"
              }}
            >
              {CATEGORIES.map((cat) => {
                const isActive = activeCategory === cat;
                return (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => {
                      setActiveCategory(cat);
                      if (onFilterCategory) onFilterCategory(cat);
                    }}
                    style={{
                      padding: "8px 16px",
                      borderRadius: "9999px",
                      fontSize: "0.8rem",
                      fontWeight: 700,
                      letterSpacing: "0.02em",
                      border: isActive ? "1.5px solid #EA580C" : "1.5px solid #FDE68A",
                      background: isActive
                        ? "linear-gradient(135deg, #EA580C 0%, #C2410C 100%)"
                        : "#FFFDF9",
                      color: isActive ? "#FFFFFF" : "#78350F",
                      boxShadow: isActive ? "0 4px 14px rgba(234, 88, 12, 0.3)" : "none",
                      cursor: "pointer",
                      transition: "all 0.2s ease"
                    }}
                  >
                    {cat}
                  </button>
                );
              })}
            </div>

            {/* Discourse Cards Feed */}
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
              {filteredDiscourses.map((disc) => {
                const isSelected = disc.id === activeId;
                return (
                  <div
                    key={disc.id}
                    onClick={() => handleSelect(disc)}
                    className="planar-card"
                    style={{
                      padding: "16px 20px",
                      backgroundColor: isSelected ? "#FFFBEB" : "#FFFFFF",
                      borderColor: isSelected ? "#EA580C" : "#FDE68A",
                      borderLeftWidth: isSelected ? "5px" : "1.5px",
                      boxShadow: isSelected
                        ? "0 8px 28px rgba(234, 88, 12, 0.15)"
                        : "0 2px 10px rgba(180, 83, 9, 0.05)",
                      cursor: "pointer",
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px"
                    }}
                  >
                    {/* Top Meta Line */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span className="badge-pill">{disc.category}</span>
                        <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "#78716C", fontWeight: 600 }}>
                          {disc.date}
                        </span>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                          fontSize: "0.75rem",
                          fontFamily: "var(--font-mono)",
                          fontWeight: 700,
                          color: isSelected ? "#EA580C" : "#B45309"
                        }}
                      >
                        <Clock size={12} />
                        {disc.duration}
                        {isSelected && isPlaying && (
                          <span
                            style={{
                              display: "inline-block",
                              width: "7px",
                              height: "7px",
                              borderRadius: "50%",
                              backgroundColor: "#EA580C",
                              marginLeft: "4px",
                              boxShadow: "0 0 8px #EA580C"
                            }}
                          />
                        )}
                      </div>
                    </div>

                    {/* Titles */}
                    <div>
                      <h4
                        style={{
                          fontFamily: "var(--font-serif)",
                          fontSize: "1.25rem",
                          fontWeight: 700,
                          color: isSelected ? "#C2410C" : "var(--color-navy-shyam)",
                          marginBottom: "2px",
                          lineHeight: "1.3"
                        }}
                      >
                        {disc.titleHindi}
                      </h4>
                      <div style={{ fontSize: "0.825rem", color: "#57534E", fontWeight: 600 }}>
                        {disc.titleEnglish}
                      </div>
                    </div>

                    {/* Excerpt */}
                    <p
                      style={{
                        fontSize: "0.85rem",
                        color: "#292524",
                        lineHeight: "1.55",
                        display: "-webkit-box",
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden"
                      }}
                    >
                      {disc.snippetHindi}
                    </p>

                    {/* Tags */}
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "4px" }}>
                      {disc.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          style={{
                            fontSize: "0.7rem",
                            padding: "3px 8px",
                            backgroundColor: "#FEF3C7",
                            borderRadius: "4px",
                            color: "#92400E",
                            fontFamily: "var(--font-mono)",
                            fontWeight: 600
                          }}
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
