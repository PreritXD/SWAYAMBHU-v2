import React, { useState, useRef, useEffect, type FormEvent } from "react";
import { createPortal } from "react-dom";
import { Streamdown } from "streamdown";
import {
  Send,
  MessageCircle,
  Sparkles,
  RotateCcw,
  Check,
  Copy,
  ThumbsUp,
  Flag,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Zap,
  Layers,
  AlertCircle,
  Clock,
  Maximize2,
  Minimize2,
  SendHorizontal,
} from "lucide-react";
import {
  sendChatMessage,
  sendFeedback,
  checkBackendHealth,
  type Citation,
  type ChatMessage as ApiChatMessage,
} from "@/lib/api";

interface MessageItem {
  id: string;
  from: "user" | "assistant";
  text: string;
  citations?: Citation[];
  isGrounded?: boolean;
  modelUsed?: string;
  latencyMs?: number;
  timestamp: string;
}

// Custom Sacred Line Icons (Uniform 1.6px stroke width, saffron/maroon spiritual iconography)
function IconLotusPeace({ size = 14, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M12 4c-1.5 3.5-2 6-2 8.5 0 2 1 3.5 2 3.5s2-1.5 2-3.5C14 10 13.5 7.5 12 4z" />
      <path d="M10 12.5C7.5 11 5 11.5 3.5 13.5c-1 1.5-.5 3.5 1.5 4 2.5.5 4.5-.5 5-2.5" />
      <path d="M14 12.5c2.5-1.5 5-1 6.5 1 1 1.5.5 3.5-1.5 4-2.5.5-4.5-.5-5-2.5" />
      <path d="M8.5 19c2.3 1.3 4.7 1.3 7 0" />
    </svg>
  );
}

function IconJapMala({ size = 14, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <circle cx="12" cy="4.5" r="1.3" />
      <circle cx="16.5" cy="6.2" r="1.3" />
      <circle cx="19" cy="10" r="1.3" />
      <circle cx="18" cy="14.5" r="1.3" />
      <circle cx="14.5" cy="17.8" r="1.3" />
      <circle cx="12" cy="18.5" r="1.5" />
      <circle cx="9.5" cy="17.8" r="1.3" />
      <circle cx="6" cy="14.5" r="1.3" />
      <circle cx="5" cy="10" r="1.3" />
      <circle cx="7.5" cy="6.2" r="1.3" />
      <path d="M12 19.8v2.2" />
      <path d="M10.5 22h3" />
    </svg>
  );
}

function IconSahanSheelta({ size = 14, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M12 3a9 9 0 0 0-9 9c0 5 4 8.5 9 10 5-1.5 9-5 9-10a9 9 0 0 0-9-9z" />
      <path d="M12 8v4l2.5 2.5" />
    </svg>
  );
}

function IconIndriyaSanyam({ size = 14, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5v9" />
      <path d="M7.5 12h9" />
      <circle cx="12" cy="12" r="2.5" />
    </svg>
  );
}

function IconSharanagati({ size = 14, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M12 3v3" />
      <path d="M12 18v3" />
      <path d="M4.5 7.5l2.2 2.2" />
      <path d="M17.3 14.3l2.2 2.2" />
      <path d="M3 12h3" />
      <path d="M18 12h3" />
      <circle cx="12" cy="12" r="4" />
    </svg>
  );
}

interface SuggestionItem {
  text: string;
  tag: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}

const SUGGESTIONS: SuggestionItem[] = [
  {
    text: "मन में अशांति और बुरे विचार आएं तो क्या करें?",
    tag: "चित्त शुद्धि",
    icon: IconLotusPeace,
  },
  {
    text: "श्वास-श्वास में राधा नाम जप करने की वास्तविक विधि क्या है?",
    tag: "नाम जप",
    icon: IconJapMala,
  },
  {
    text: "पारिवारिक कलह और कटु वचनों को कैसे सहें?",
    tag: "सहनशीलता",
    icon: IconSahanSheelta,
  },
  {
    text: "काम, क्रोध और वासना पर विजय कैसे प्राप्त करें?",
    tag: "इंद्रिय संयम",
    icon: IconIndriyaSanyam,
  },
  {
    text: "भगवान पर पूर्ण विश्वास और अनन्य शरणागति कैसे हो?",
    tag: "शरणागति",
    icon: IconSharanagati,
  },
];

const CHANNEL_LABELS: Record<string, string> = {
  bhajan_marg: "भजन मार्ग",
  sadhan_path: "साधन पथ",
  vrindavan_ras: "वृंदावन रस",
  shri_hit_radha_kripa: "राधा कृपा",
};

function parseTimestampToSeconds(ts: string): number | null {
  if (!ts) return null;
  const parts = ts.trim().split(":");
  if (parts.length === 2) {
    const m = parseInt(parts[0], 10);
    const s = parseInt(parts[1], 10);
    if (!isNaN(m) && !isNaN(s)) return m * 60 + s;
  } else if (parts.length === 3) {
    const h = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    const s = parseInt(parts[2], 10);
    if (!isNaN(h) && !isNaN(m) && !isNaN(s)) return h * 3600 + m * 60 + s;
  }
  return null;
}

const TS_CHANNEL_MAP: Record<string, string> = {
  "bhajan marg": "bhajan_marg",
  "bhajan_marg": "bhajan_marg",
  "bhajanmarg": "bhajan_marg",
  "भजन मार्ग": "bhajan_marg",
  "भजनमार्ग": "bhajan_marg",
  "भजन": "bhajan_marg",

  "sadhan path": "sadhan_path",
  "sadhan_path": "sadhan_path",
  "sadhanpath": "sadhan_path",
  "साधन पथ": "sadhan_path",
  "साधनपथ": "sadhan_path",
  "साधन": "sadhan_path",

  "vrindavan ras": "vrindavan_ras",
  "vrindavan ras mahima": "vrindavan_ras",
  "vrindavan_ras": "vrindavan_ras",
  "वृन्दावन रस": "vrindavan_ras",
  "वृंदावन रस": "vrindavan_ras",
  "वृन्दावन रस महिमा": "vrindavan_ras",
  "वृंदावन रस महिमा": "vrindavan_ras",
  "वृन्दावन": "vrindavan_ras",
  "वृंदावन": "vrindavan_ras",

  "shri hit radha kripa": "shri_hit_radha_kripa",
  "shrihit radha kripa": "shri_hit_radha_kripa",
  "radha kripa": "shri_hit_radha_kripa",
  "shri_hit_radha_kripa": "shri_hit_radha_kripa",
  "श्री हित राधा कृपा": "shri_hit_radha_kripa",
  "श्रीहित राधा कृपा": "shri_hit_radha_kripa",
  "राधा कृपा": "shri_hit_radha_kripa",
};

function normalizeSpacingAndDashes(s: string): string {
  return s
    .replace(/[\u00a0\u202f\u2000-\u200b\ufeff]/g, " ")
    .replace(/[\u2010-\u2015\u2212]/g, "-");
}

function linkifyCitationsInText(text: string, citations?: Citation[]): string {
  if (!text || !citations || citations.length === 0) return text;

  const makeLink = (innerRaw: string): string | null => {
    const innerNorm = normalizeSpacingAndDashes(innerRaw).trim();
    let trailingPunct = "";
    let cleanNorm = innerNorm;
    if (/[.,;:!]$/.test(cleanNorm)) {
      trailingPunct = cleanNorm.slice(-1);
      cleanNorm = cleanNorm.slice(0, -1).trim();
    }

    const timeMatch = cleanNorm.match(/(\d{1,2}:\d{2}(?::\d{2})?)/);
    if (!timeMatch) return null;

    const seconds = parseTimestampToSeconds(timeMatch[1]);
    const lowerInner = cleanNorm.toLowerCase();

    let channelKey: string | null = null;
    for (const [k, v] of Object.entries(TS_CHANNEL_MAP)) {
      if (lowerInner.includes(k)) {
        channelKey = v;
        break;
      }
    }

    let bestCit: Citation | null = null;
    if (channelKey) {
      const channelCits = citations.filter((c) => c.channel === channelKey);
      if (channelCits.length > 0) {
        if (seconds !== null) {
          bestCit = channelCits.reduce((closest, curr) =>
            Math.abs(curr.start_sec - seconds) < Math.abs(closest.start_sec - seconds) ? curr : closest
          );
        } else {
          bestCit = channelCits[0];
        }
      }
    }

    if (!bestCit && citations.length > 0) {
      if (seconds !== null) {
        bestCit = citations.reduce((closest, curr) =>
          Math.abs(curr.start_sec - seconds) < Math.abs(closest.start_sec - seconds) ? curr : closest
        );
      } else {
        bestCit = citations[0];
      }
    }

    if (bestCit) {
      const vid = bestCit.video_id;
      const url =
        vid && seconds !== null ? `https://youtu.be/${vid}?t=${seconds}` : bestCit.url || `https://youtu.be/${vid}`;
      let cleanDisplay = innerRaw.trim();
      if (/[.,;:!]$/.test(cleanDisplay)) {
        cleanDisplay = cleanDisplay.slice(0, -1).trim();
      }
      return `[${cleanDisplay}](${url})${trailingPunct}`;
    }

    return null;
  };

  // 1. Bracketed or parenthesized citations: [Bhajan Marg • 22:14] or (Sadhan Path • 12:30)
  const bracketPattern = /(\[|\()([^\]\)\r\n]+?(\d{1,2}:\d{2}(?::\d{2})?)[^\]\)\r\n]*?)(\]|\))(?!\s*\()/g;
  let result = text.replace(bracketPattern, (fullMatch, _openBracket, inner) => {
    const link = makeLink(inner);
    return link ? link : fullMatch;
  });

  // 2. Bold citations e.g. in tables: **Bhajan Marg • 07:50-08:41**
  const boldPattern = /\*\*((?:Bhajan|भजन|Sadhan|साधन|Vrindavan|वृन्दावन|वृंदावन|Shri\s*Hit|श्री\s*हित|राधा)[^*\r\n]+?(\d{1,2}:\d{2}(?::\d{2})?)[^*\r\n]*?)\*\*(?!\s*\()/gi;
  result = result.replace(boldPattern, (fullMatch, inner) => {
    const link = makeLink(inner);
    return link ? `**${link}**` : fullMatch;
  });

  return result;
}

function cleanAssistantText(text: string, citations?: Citation[]): string {
  if (!text) return "";
  let clean = text.trim();
  // 1. Strip leading question blocks with separator (e.g. **प्रश्न:** ... \n\n--- or **Question:** ... ---)
  clean = clean.replace(
    /^\s*(?:\*{0,2}(?:प्रश्न|Question|साधक का प्रश्न)\s*[:：]\*{0,2})[\s\S]*?(?:--{2,}\s*|\n{2,})(?=(?:#{1,3}\s*[१-५1-5]|\b[१-५1-5]\.|\S))/i,
    ""
  );
  // 2. Strip single line echoed question with quotes
  clean = clean.replace(
    /^\s*(?:\*{0,2}(?:प्रश्न|Question|साधक का प्रश्न)\s*[:：]\*{0,2})\s*["“'‘][^"”'’\n]+["”'’]\s*(?:--{2,}\s*|\n+)/i,
    ""
  );
  // 3. Strip any leading orphan horizontal divider line
  clean = clean.replace(/^\s*--{2,}\s*\n+/, "");

  // 4. Transform unlinked citations into clickable video links using returned citations
  if (citations && citations.length > 0) {
    clean = linkifyCitationsInText(clean, citations);
  }

  return clean.trim();
}

export default function SatsangChat() {
  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: "initial_greeting",
      from: "assistant",
      text: "श्री राधे। पूज्य श्री हित प्रेमानंद गोविंद शरण जी महाराज के सत्संग वचनों में आपका स्वागत है। आप भक्ति, नाम जप, मन के विकार, साधना अथवा जीवन के संशय से संबंधित कोई भी जिज्ञासा पूछ सकते हैं।",
      timestamp: "अब",
    },
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [useCouncil, setUseCouncil] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [feedbackMap, setFeedbackMap] = useState<Record<string, "helpful" | "flagged">>({});
  const [expandedCitationId, setExpandedCitationId] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<"connected" | "connecting" | "offline">("connecting");
  const [activeModel, setActiveModel] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close full view on Escape key and handle body scroll locking
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isExpanded) {
        setIsExpanded(false);
      }
    };
    if (isExpanded) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [isExpanded]);

  // Poll / check backend health on mount
  useEffect(() => {
    let isMounted = true;
    async function checkHealth() {
      try {
        const health = await checkBackendHealth();
        if (isMounted) {
          setBackendStatus("connected");
          setActiveModel(health.llm_provider || "Gemma 27B");
        }
      } catch {
        if (isMounted) {
          setBackendStatus("offline");
        }
      }
    }
    checkHealth();
    return () => {
      isMounted = false;
    };
  }, []);

  // Auto-scroll when messages change or loading
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, isLoading]);

  const handleSendMessage = async (customText?: string) => {
    const textToSend = (customText ?? input).trim();
    if (!textToSend || isLoading) return;

    setErrorMessage(null);
    setInput("");

    const userMsgId = `user_${Date.now()}`;
    const asstMsgId = `asst_${Date.now() + 1}`;

    const userMessage: MessageItem = {
      id: userMsgId,
      from: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Build history for context resolution (exclude initial system greeting)
      const historyPayload: ApiChatMessage[] = messages
        .filter((m) => m.id !== "initial_greeting")
        .map((m) => ({
          role: m.from === "user" ? "user" : "assistant",
          content: m.text,
        }));

      const res = await sendChatMessage({
        message: textToSend,
        history: historyPayload,
        use_council: useCouncil,
      });

      const assistantMessage: MessageItem = {
        id: asstMsgId,
        from: "assistant",
        text: res.answer,
        citations: res.citations || [],
        isGrounded: res.is_grounded,
        modelUsed: res.model_used || activeModel,
        latencyMs: res.latency_ms,
        timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setBackendStatus("connected");
    } catch (err: unknown) {
      const errDetail = err instanceof Error ? err.message : "सत्संग शोध में त्रुटि आई। कृपया पुनः प्रयास करें।";
      setErrorMessage(errDetail);
      setBackendStatus("offline");
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleFormSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    handleSendMessage();
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleFeedbackClick = async (msgId: string, query: string, answer: string, flagged: boolean) => {
    if (feedbackMap[msgId]) return;
    setFeedbackMap((prev) => ({ ...prev, [msgId]: flagged ? "flagged" : "helpful" }));
    try {
      await sendFeedback({
        query,
        answer,
        flagged,
        note: flagged ? "User marked inaccurate" : "User marked helpful",
      });
    } catch {
      // Non-critical, ignore UI failure
    }
  };

  const handleResetChat = () => {
    if (messages.length > 1) {
      setMessages([
        {
          id: "initial_greeting",
          from: "assistant",
          text: "श्री राधे। नवीन संवाद प्रारंभ हो गया है। आप कोई भी जिज्ञासा पूछ सकते हैं।",
          timestamp: "अब",
        },
      ]);
      setErrorMessage(null);
    }
  };

  const chatContent = (
    <div
      className={`satsang-chat-container ${isExpanded ? "is-expanded" : ""}`}
      aria-label="सत्संग वाणी जिज्ञासा संकुल"
    >
        {/* Header */}
        <div className="satsang-chat-header">
          <div className="satsang-chat-header-info">
            <div className="satsang-chat-badge">
              <span
                className={`satsang-status-dot ${
                  backendStatus === "connected"
                    ? "dot-connected"
                    : backendStatus === "connecting"
                    ? "dot-connecting"
                    : "dot-offline"
                }`}
              />
              <span>
                {backendStatus === "connected"
                  ? "सत्संग वाणी सक्रिय"
                  : backendStatus === "connecting"
                  ? "जुड़ रहे हैं..."
                  : "ऑफलाइन"}
              </span>
            </div>
            <div className="satsang-chat-title-group">
              <span className="satsang-chat-title-kicker">श्री राधे</span>
              <h3 className="satsang-chat-title-main">सत्संग जिज्ञासा</h3>
            </div>
          </div>

          {/* Unified Action Toolbar */}
          <div className="satsang-header-toolbar" role="toolbar" aria-label="सत्संग नियंत्रण">
            <button
              type="button"
              className={`satsang-toolbar-btn satsang-council-toggle ${useCouncil ? "active" : ""}`}
              onClick={() => setUseCouncil((prev) => !prev)}
              title="गहन चिंतन (Council of LLMs) चालू/बंद करें"
            >
              <Layers size={13} />
              <span className="hide-mobile">गहन चिंतन</span>
            </button>

            <div className="satsang-toolbar-divider" />

            <button
              type="button"
              className="satsang-toolbar-btn satsang-toolbar-icon-btn"
              onClick={handleResetChat}
              title="नया संवाद प्रारंभ करें"
              aria-label="नया संवाद प्रारंभ करें"
            >
              <RotateCcw size={14} />
            </button>

            <div className="satsang-toolbar-divider" />

            <button
              type="button"
              className={`satsang-toolbar-btn satsang-toolbar-icon-btn satsang-toolbar-expand ${isExpanded ? "active" : ""}`}
              onClick={() => setIsExpanded((prev) => !prev)}
              title={isExpanded ? "सामान्य आकार में लौटें (Esc)" : "विस्तृत कैनवास दृश्य"}
              aria-label={isExpanded ? "सामान्य आकार में लौटें" : "विस्तृत दृश्य में देखें"}
            >
              {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
            </button>
          </div>
        </div>

      {/* Messages Scroll Area */}
      <div className="satsang-chat-body" ref={messagesContainerRef} aria-live="polite">
        {messages.map((msg, index) => {
          // Find preceding user question for feedback
          const prevUserMsg = messages
            .slice(0, index)
            .reverse()
            .find((m) => m.from === "user");

          if (msg.id === "initial_greeting") {
            return (
              <div
                key={msg.id}
                className="satsang-msg-row satsang-msg-assistant satsang-welcome-row"
              >
                <div className="satsang-msg-bubble satsang-welcome-bubble">
                  <div className="satsang-welcome-top">
                    <div className="satsang-welcome-badge">
                      <Sparkles size={13} className="satsang-accent-icon" />
                      <span>श्री हित हरिवंश · सत्संग संदेश</span>
                    </div>
                    <span className="satsang-welcome-ornament">श्री राधे</span>
                  </div>
                  <div className="satsang-msg-content satsang-welcome-content">
                    {msg.text}
                  </div>
                </div>
              </div>
            );
          }

          return (
            <div
              key={msg.id}
              className={`satsang-msg-row satsang-msg-${msg.from}`}
            >
              <div className="satsang-msg-bubble">
                {msg.from === "assistant" ? (
                  <div className="satsang-msg-content satsang-asst-content">
                    <Streamdown
                      className="satsang-markdown-body"
                      components={{
                        table: ({ children, ...props }) => (
                          <div className="satsang-table-wrapper">
                            <table {...props}>{children}</table>
                          </div>
                        ),
                        a: ({ href, children, ...props }) => {
                          const isYouTube = href && (href.includes("youtu.be") || href.includes("youtube.com"));
                          return (
                            <a
                              href={href}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={isYouTube ? "satsang-inline-video-link" : "satsang-inline-link"}
                              title={isYouTube ? "यूट्यूब पर यह सत्संग सुनें (सटीक समय से)" : undefined}
                              {...props}
                            >
                              {isYouTube && <span className="satsang-link-play-icon">▶</span>}
                              <span>{children}</span>
                            </a>
                          );
                        },
                      }}
                    >
                      {cleanAssistantText(msg.text, msg.citations)}
                    </Streamdown>
                  </div>
                ) : (
                  <div className="satsang-msg-content">{msg.text}</div>
                )}

                {/* Verified Citations List if present */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="satsang-citations-block">
                    <div className="satsang-citations-header">
                      <Sparkles size={11} className="satsang-accent-icon" />
                      <span>प्रमाणित सत्संग संदर्भ ({msg.citations.length})</span>
                    </div>

                    <div className="satsang-citations-list">
                      {msg.citations.map((citation, cIndex) => {
                        const citId = `${msg.id}_c_${cIndex}`;
                        const isExpanded = expandedCitationId === citId;
                        const channelName =
                          CHANNEL_LABELS[citation.channel] || citation.channel;

                        return (
                          <div key={citId} className="satsang-citation-card">
                            <div className="satsang-citation-top">
                              <span className="satsang-citation-channel">
                                {channelName}
                              </span>
                              <a
                                href={citation.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="satsang-timestamp-link"
                                title="यूट्यूब पर सटीक समय से सुनें"
                              >
                                <span>▶ {citation.timestamp_start}</span>
                                <ExternalLink size={10} />
                              </a>
                            </div>

                            <p className="satsang-citation-title">{citation.title}</p>

                            {citation.excerpt && (
                              <button
                                type="button"
                                className="satsang-excerpt-toggle"
                                onClick={() =>
                                  setExpandedCitationId(isExpanded ? null : citId)
                                }
                              >
                                <span>
                                  {isExpanded ? "उद्धरण छिपाएं" : "सटीक वचन देखें"}
                                </span>
                                {isExpanded ? (
                                  <ChevronUp size={11} />
                                ) : (
                                  <ChevronDown size={11} />
                                )}
                              </button>
                            )}

                            {isExpanded && citation.excerpt && (
                              <blockquote className="satsang-citation-quote">
                                “{citation.excerpt}”
                              </blockquote>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Assistant Message Footer with Actions */}
                {msg.from === "assistant" && msg.id !== "initial_greeting" && (
                  <div className="satsang-msg-footer">
                    <div className="satsang-msg-meta">
                      {msg.latencyMs && (
                        <span className="satsang-meta-tag">
                          <Clock size={10} /> {msg.latencyMs}ms
                        </span>
                      )}
                      {msg.modelUsed && (
                        <span className="satsang-meta-tag">{msg.modelUsed}</span>
                      )}
                    </div>

                    <div className="satsang-msg-actions">
                      <button
                        type="button"
                        className="satsang-subtle-btn"
                        onClick={() => handleCopy(msg.id, cleanAssistantText(msg.text))}
                        title="उत्तर कॉपी करें"
                      >
                        {copiedId === msg.id ? (
                          <>
                            <Check size={12} color="#15803d" />
                            <span className="copied-text">कॉपी हो गया</span>
                          </>
                        ) : (
                          <Copy size={12} />
                        )}
                      </button>

                      <button
                        type="button"
                        className={`satsang-subtle-btn ${
                          feedbackMap[msg.id] === "helpful" ? "rated-active" : ""
                        }`}
                        onClick={() =>
                          handleFeedbackClick(
                            msg.id,
                            prevUserMsg?.text || "",
                            msg.text,
                            false
                          )
                        }
                        title="उपयोगी है"
                      >
                        <ThumbsUp size={12} />
                      </button>

                      <button
                        type="button"
                        className={`satsang-subtle-btn ${
                          feedbackMap[msg.id] === "flagged" ? "flagged-active" : ""
                        }`}
                        onClick={() =>
                          handleFeedbackClick(
                            msg.id,
                            prevUserMsg?.text || "",
                            msg.text,
                            true
                          )
                        }
                        title="त्रुटि रिपोर्ट करें"
                      >
                        <Flag size={12} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="satsang-msg-row satsang-msg-assistant">
            <div className="satsang-loading-box">
              <div className="satsang-breathing-orb" />
              <span>सत्संग वचनों में खोज हो रही है...</span>
            </div>
          </div>
        )}

        {/* Error message banner */}
        {errorMessage && (
          <div className="satsang-error-banner">
            <AlertCircle size={14} />
            <div className="satsang-error-text">
              <span>{errorMessage}</span>
              <button
                type="button"
                className="satsang-retry-link"
                onClick={() => handleSendMessage()}
              >
                पुनः प्रयास करें
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Cohesive Unified Compose Zone (Suggestions + Input integrated) */}
      <div className="satsang-compose-dock">
        {/* Suggested Inquiries (single-line pills flowing seamlessly above input) */}
        {messages.length <= 2 && !isLoading && (
          <div className="satsang-suggestions-flow">
            <div className="satsang-suggestions-chips">
              {SUGGESTIONS.map((item) => {
                const IconComp = item.icon;
                return (
                  <button
                    key={item.text}
                    type="button"
                    className="satsang-chip"
                    onClick={() => handleSendMessage(item.text)}
                    title={item.text}
                  >
                    <span className="satsang-chip-icon">
                      <IconComp size={14} />
                    </span>
                    <span className="satsang-chip-text">{item.text}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Integrated Composer Form */}
        <form className="satsang-compose-form" onSubmit={handleFormSubmit}>
          <input
            id="satsang-query-input"
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="अपनी जिज्ञासा लिखें (उदा. मन को एकाग्र कैसे करें)..."
            aria-label="सत्संग जिज्ञासा इनपुट"
            disabled={isLoading}
            className="satsang-compose-input"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="satsang-send-btn"
            aria-label="जिज्ञासा भेजें"
            title="जिज्ञासा भेजें"
          >
            <SendHorizontal size={20} strokeWidth={2.3} />
          </button>
        </form>
      </div>

      {/* Official Satsang Disclaimer Footer */}
      <div className="satsang-chat-disclaimer">
        <ShieldCheck size={11} className="satsang-disclaimer-icon" />
        <span>
          यह शोध प्रणाली पूज्य श्री हित प्रेमानंद गोविंद शरण जी महाराज के सार्वजनिक
          सत्संग वचनों पर आधारित है। किसी भी संशय की स्थिति में दिए गए मूल वीडियो
          प्रमाण से ही प्रामाणिकता प्राप्त करें।
        </span>
      </div>
    </div>
  );

  if (isExpanded) {
    return (
      <>
        <div className="satsang-chat-placeholder" style={{ height: "860px", width: "100%" }} />
        {createPortal(
          <>
            <div
              className="satsang-chat-backdrop"
              onClick={() => setIsExpanded(false)}
              aria-label="कैनवास बंद करें"
            />
            {chatContent}
          </>,
          document.body
        )}
      </>
    );
  }

  return chatContent;
}
