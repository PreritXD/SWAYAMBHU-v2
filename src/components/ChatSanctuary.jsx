import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  RefreshCw,
  ExternalLink,
  PlayCircle,
  Copy,
  Check,
  ThumbsUp,
  Flag,
  ShieldCheck,
  Layers,
  Zap
} from 'lucide-react';

const SUGGESTED_QUESTIONS = [
  {
    icon: '🌸',
    text: 'मन में वासना और बुरे विचार आएं तो क्या करें?'
  },
  {
    icon: '📿',
    text: 'श्वास-श्वास में राधा नाम जप करने की वास्तविक विधि क्या है?'
  },
  {
    icon: '🕊️',
    text: 'पारिवारिक कलह और कटु वचनों को कैसे सहें?'
  },
  {
    icon: '🌟',
    text: 'काम, क्रोध और वासना पर विजय कैसे प्राप्त करें?'
  },
  {
    icon: '🌿',
    text: 'भगवान पर पूर्ण विश्वास और अनन्य शरणागति कैसे हो?'
  },
  {
    icon: '⚠️',
    text: 'मृत्यु, असाध्य रोग और शोक के समय साधक की क्या दृष्टि हो?'
  }
];

export default function ChatSanctuary() {
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [useCouncil, setUseCouncil] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const [feedbackMap, setFeedbackMap] = useState({});
  const [errorMsg, setErrorMsg] = useState(null);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Adjust textarea height dynamically
  const handleInputChange = (e) => {
    setInputQuery(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSendMessage = async (customQuery) => {
    const queryToSend = (customQuery || inputQuery).trim();
    if (!queryToSend || isLoading) return;

    setErrorMsg(null);
    setInputQuery('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    const userMessageId = `user_${Date.now()}`;
    const assistantMessageId = `asst_${Date.now() + 1}`;

    const newMessages = [
      ...messages,
      {
        id: userMessageId,
        role: 'user',
        text: queryToSend,
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      }
    ];

    setMessages(newMessages);
    setIsLoading(true);

    try {
      const historyPayload = messages.map((m) => ({
        role: m.role,
        content: m.text
      }));

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: queryToSend,
          history: historyPayload,
          use_council: useCouncil
        })
      });

      if (!res.ok) {
        let errText = 'उत्तर प्राप्त करने में बाधा आई। कृपया पुनः प्रयास करें।';
        try {
          const errData = await res.json();
          if (errData.detail) errText = errData.detail;
        } catch (_) {}
        throw new Error(errText);
      }

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          id: assistantMessageId,
          role: 'assistant',
          text: data.answer,
          citations: data.citations || [],
          is_grounded: data.is_grounded !== false,
          model_used: data.model_used,
          latency_ms: data.latency_ms,
          timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } catch (err) {
      setErrorMsg(err.message || 'त्रुटि उत्पन्न हुई। कृपया पुनः प्रयास करें।');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyText = (msgId, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2500);
  };

  const handleFeedback = async (msgId, query, answer, isFlagged) => {
    if (feedbackMap[msgId]) return;
    setFeedbackMap((prev) => ({ ...prev, [msgId]: isFlagged ? 'flagged' : 'helpful' }));

    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query || '',
          answer: answer || '',
          flagged: isFlagged,
          note: isFlagged ? 'User marked inaccurate' : 'User marked helpful'
        })
      });
    } catch (_) {}
  };

  const handleResetChat = () => {
    if (messages.length > 0 && window.confirm('क्या आप नया संवाद प्रारंभ करना चाहते हैं?')) {
      setMessages([]);
      setErrorMsg(null);
    }
  };

  return (
    <div
      id="satsang-chat"
      style={{
        width: '100%',
        minHeight: '600px',
        maxHeight: '780px',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#FFFFFF',
        border: '1px solid #E4E4E7',
        borderRadius: '16px',
        overflow: 'hidden',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.03)'
      }}
    >
      {/* Top Header */}
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid #F4F4F5',
          backgroundColor: '#FFFFFF'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              backgroundColor: '#18181B',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '14px',
              fontWeight: 700,
              fontFamily: 'var(--font-devanagari)'
            }}
          >
            राधा
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: '14.5px',
                  fontWeight: 700,
                  color: '#09090B',
                  margin: 0
                }}
              >
                श्री राधा केली कुंज • सत्संग संवाद
              </h3>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  backgroundColor: '#F4F4F5',
                  color: '#18181B',
                  fontSize: '10.5px',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '9999px',
                  border: '1px solid #E4E4E7'
                }}
              >
                <span
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor: '#22C55E'
                  }}
                />
                Online
              </span>
            </div>
            <p
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '12px',
                color: '#71717A',
                margin: 0
              }}
            >
              Grounded in recorded discourses of Pujya Shri Hit Premanand Ji Maharaj
            </p>
          </div>
        </div>

        {/* Right Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Mode Switcher */}
          <button
            onClick={() => setUseCouncil(!useCouncil)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '9999px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              border: useCouncil ? '1px solid #18181B' : '1px solid #E4E4E7',
              backgroundColor: useCouncil ? '#18181B' : '#FFFFFF',
              color: useCouncil ? '#FFFFFF' : '#52525B',
              transition: 'all 0.15s ease'
            }}
          >
            {useCouncil ? (
              <>
                <Layers size={13} color="#BEF264" />
                <span>Council Mode</span>
              </>
            ) : (
              <>
                <Zap size={13} color="#71717A" />
                <span>Fast Mode</span>
              </>
            )}
          </button>

          {messages.length > 0 && (
            <button
              onClick={handleResetChat}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '6px 12px',
                borderRadius: '9999px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                backgroundColor: '#FFFFFF',
                border: '1px solid #E4E4E7',
                color: '#71717A',
                transition: 'all 0.15s ease'
              }}
              title="Reset Conversation"
            >
              <RefreshCw size={12} />
              <span>Reset</span>
            </button>
          )}
        </div>
      </header>

      {/* Messages Scroll Area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
          backgroundColor: '#FAFAFA'
        }}
      >
        {/* Welcome Empty State */}
        {messages.length === 0 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              padding: '28px 16px',
              margin: 'auto 0'
            }}
          >
            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                backgroundColor: '#FFFFFF',
                border: '1px solid #E4E4E7',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '26px',
                marginBottom: '16px',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)'
              }}
            >
              🙏
            </div>

            <h3
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '1.35rem',
                fontWeight: 700,
                color: '#09090B',
                marginBottom: '6px'
              }}
            >
              राधे राधे! Ask any spiritual inquiry
            </h3>

            <p
              style={{
                maxWidth: '520px',
                fontSize: '14px',
                color: '#71717A',
                lineHeight: 1.6,
                marginBottom: '28px'
              }}
            >
              Receive authentic, verbatim guidance cited from 13,968+ verified satsang records
              with direct YouTube timestamp video references.
            </p>

            {/* Quick Starter Chips */}
            <div style={{ width: '100%', maxWidth: '680px' }}>
              <div
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: '#A1A1AA',
                  marginBottom: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
              >
                <Sparkles size={13} color="#18181B" />
                <span>SUGGESTED DISCOURSE INQUIRIES</span>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                  gap: '10px'
                }}
              >
                {SUGGESTED_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(q.text)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '10px 14px',
                      borderRadius: '10px',
                      backgroundColor: '#FFFFFF',
                      border: '1px solid #E4E4E7',
                      color: '#18181B',
                      fontSize: '13px',
                      fontWeight: 500,
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.15s ease',
                      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.02)'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = '#09090B';
                      e.currentTarget.style.transform = 'translateY(-1px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = '#E4E4E7';
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >
                    <span>{q.icon}</span>
                    <span>{q.text}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Conversation Messages */}
        {messages.map((msg, index) => {
          if (msg.role === 'user') {
            return (
              <div
                key={msg.id || index}
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '80%',
                  backgroundColor: '#18181B',
                  color: '#FFFFFF',
                  padding: '12px 16px',
                  borderRadius: '16px 16px 4px 16px',
                  fontSize: '14.5px',
                  lineHeight: '1.6'
                }}
              >
                <div style={{ wordBreak: 'break-word' }}>{msg.text}</div>
                <div
                  style={{
                    fontSize: '10.5px',
                    color: 'rgba(255, 255, 255, 0.6)',
                    textAlign: 'right',
                    marginTop: '4px',
                    fontFamily: 'var(--font-mono)'
                  }}
                >
                  {msg.timestamp}
                </div>
              </div>
            );
          }

          // Assistant Response Card
          const queryUserMsg = messages[index - 1]?.text || '';
          const isFeedbackSent = feedbackMap[msg.id];

          return (
            <div
              key={msg.id || index}
              style={{
                alignSelf: 'flex-start',
                maxWidth: '92%',
                backgroundColor: '#FFFFFF',
                border: '1px solid #E4E4E7',
                borderRadius: '16px 16px 16px 4px',
                padding: '20px',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.02)',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px'
              }}
            >
              {/* Header */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderBottom: '1px solid #F4F4F5',
                  paddingBottom: '10px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '6px',
                      backgroundColor: '#18181B',
                      color: '#FFFFFF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px'
                    }}
                  >
                    🪷
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--font-sans)',
                      fontWeight: 700,
                      fontSize: '13.5px',
                      color: '#09090B'
                    }}
                  >
                    पूज्य श्री हित प्रेमानंद जी महाराज वचनामृत
                  </span>
                  {msg.latency_ms && (
                    <span
                      style={{
                        fontSize: '11px',
                        color: '#A1A1AA',
                        fontFamily: 'var(--font-mono)'
                      }}
                    >
                      ({(msg.latency_ms / 1000).toFixed(1)}s)
                    </span>
                  )}
                </div>

                <button
                  onClick={() => handleCopyText(msg.id, msg.text)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '3px 8px',
                    borderRadius: '6px',
                    backgroundColor: '#F4F4F5',
                    border: '1px solid #E4E4E7',
                    color: '#52525B',
                    fontSize: '11px',
                    cursor: 'pointer'
                  }}
                  title="Copy response"
                >
                  {copiedId === msg.id ? (
                    <>
                      <Check size={12} color="#16A34A" />
                      <span style={{ color: '#16A34A', fontWeight: 600 }}>Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy size={12} />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>

              {/* Text */}
              <div
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: '14.5px',
                  lineHeight: '1.7',
                  color: '#18181B',
                  whiteSpace: 'pre-line',
                  wordBreak: 'break-word'
                }}
              >
                {msg.text}
              </div>

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div
                  style={{
                    marginTop: '4px',
                    paddingTop: '12px',
                    borderTop: '1px solid #F4F4F5'
                  }}
                >
                  <div
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      color: '#71717A',
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      marginBottom: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px'
                    }}
                  >
                    <ShieldCheck size={13} color="#09090B" />
                    <span>VERIFIED DISCOURSE CITATIONS ({msg.citations.length})</span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {msg.citations.map((cite, cIdx) => (
                      <div
                        key={cIdx}
                        style={{
                          backgroundColor: '#FAFAFA',
                          border: '1px solid #E4E4E7',
                          borderRadius: '8px',
                          padding: '10px 12px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px'
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            flexWrap: 'wrap',
                            gap: '8px'
                          }}
                        >
                          <span
                            style={{
                              fontWeight: 600,
                              fontSize: '12.5px',
                              color: '#18181B'
                            }}
                          >
                            {cite.title || 'सत्संग प्रवचन'}
                          </span>

                          <a
                            href={cite.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              padding: '4px 10px',
                              borderRadius: '9999px',
                              backgroundColor: '#FFFFFF',
                              border: '1px solid #E4E4E7',
                              color: '#09090B',
                              fontSize: '11.5px',
                              fontWeight: 600,
                              textDecoration: 'none'
                            }}
                          >
                            <PlayCircle size={13} color="#DC2626" />
                            <span>
                              {cite.timestamp_start
                                ? `Time: ${cite.timestamp_start}`
                                : 'Watch Video'}
                            </span>
                            <ExternalLink size={11} />
                          </a>
                        </div>

                        {cite.excerpt && (
                          <div
                            style={{
                              fontSize: '12px',
                              color: '#52525B',
                              fontStyle: 'italic',
                              backgroundColor: '#FFFFFF',
                              padding: '6px 10px',
                              borderRadius: '6px',
                              borderLeft: '2px solid #09090B'
                            }}
                          >
                            "{cite.excerpt.length > 180 ? `${cite.excerpt.slice(0, 180)}...` : cite.excerpt}"
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Feedback and Disclaimer */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingTop: '8px',
                  borderTop: '1px solid #F4F4F5',
                  fontSize: '11px',
                  color: '#A1A1AA',
                  flexWrap: 'wrap',
                  gap: '8px'
                }}
              >
                <span>Grounded strictly in authentic Bhajan Marg recordings.</span>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    onClick={() => handleFeedback(msg.id, queryUserMsg, msg.text, false)}
                    disabled={Boolean(isFeedbackSent)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '3px 8px',
                      borderRadius: '4px',
                      backgroundColor: isFeedbackSent === 'helpful' ? '#DCFCE7' : 'transparent',
                      color: isFeedbackSent === 'helpful' ? '#16A34A' : '#71717A',
                      border: '1px solid #E4E4E7',
                      cursor: isFeedbackSent ? 'default' : 'pointer',
                      fontSize: '11px'
                    }}
                    title="Mark helpful"
                  >
                    <ThumbsUp size={11} />
                    <span>{isFeedbackSent === 'helpful' ? 'Helpful' : 'Helpful'}</span>
                  </button>

                  <button
                    onClick={() => handleFeedback(msg.id, queryUserMsg, msg.text, true)}
                    disabled={Boolean(isFeedbackSent)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '3px 8px',
                      borderRadius: '4px',
                      backgroundColor: isFeedbackSent === 'flagged' ? '#FEE2E2' : 'transparent',
                      color: isFeedbackSent === 'flagged' ? '#DC2626' : '#71717A',
                      border: '1px solid #E4E4E7',
                      cursor: isFeedbackSent ? 'default' : 'pointer',
                      fontSize: '11px'
                    }}
                    title="Report issue"
                  >
                    <Flag size={11} />
                    <span>{isFeedbackSent === 'flagged' ? 'Reported' : 'Flag'}</span>
                  </button>
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {isLoading && (
          <div
            style={{
              alignSelf: 'flex-start',
              maxWidth: '380px',
              backgroundColor: '#FFFFFF',
              border: '1px solid #E4E4E7',
              borderRadius: '16px',
              padding: '16px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span className="thinking-lotus" style={{ fontSize: '20px' }}>
                🪷
              </span>
              <div>
                <div
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontWeight: 600,
                    fontSize: '13.5px',
                    color: '#09090B'
                  }}
                >
                  {useCouncil
                    ? 'Council deliberating across channels...'
                    : 'Searching authentic satsang archives...'}
                </div>
                <div style={{ fontSize: '11px', color: '#71717A' }}>
                  Matching verbatim transcript chunks
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              backgroundColor: '#FEF2F2',
              border: '1px solid #FCA5A5',
              color: '#991B1B',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <span>⚠️ {errorMsg}</span>
            <button
              onClick={() => setErrorMsg(null)}
              style={{
                color: '#991B1B',
                fontWeight: 700,
                cursor: 'pointer',
                background: 'none',
                border: 'none'
              }}
            >
              ✕
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Sticky Bottom Input */}
      <footer
        style={{
          padding: '14px 18px',
          backgroundColor: '#FFFFFF',
          borderTop: '1px solid #F4F4F5',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px'
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: '8px',
            backgroundColor: '#FAFAFA',
            border: '1px solid #E4E4E7',
            borderRadius: '12px',
            padding: '6px 12px'
          }}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputQuery}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about sadhana, naam japa, or life guidance... (Press Enter)"
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              resize: 'none',
              fontFamily: 'var(--font-sans)',
              fontSize: '14px',
              lineHeight: '1.5',
              color: '#09090B',
              backgroundColor: 'transparent',
              maxHeight: '120px',
              padding: '4px 0'
            }}
          />

          <button
            onClick={() => handleSendMessage()}
            disabled={!inputQuery.trim() || isLoading}
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              backgroundColor: !inputQuery.trim() || isLoading ? '#E4E4E7' : '#18181B',
              color: !inputQuery.trim() || isLoading ? '#A1A1AA' : '#FFFFFF',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: !inputQuery.trim() || isLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s ease'
            }}
            title="Send query"
          >
            <Send size={15} />
          </button>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '11px',
            color: '#A1A1AA'
          }}
        >
          <span>॥ श्री राधा नाम परम सुखदाई • श्री हित हरिवंश चंद्र जयतितराम ॥</span>
        </div>
      </footer>
    </div>
  );
}
