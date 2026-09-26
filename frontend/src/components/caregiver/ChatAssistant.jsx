import React, { useState, useRef, useEffect } from "react";
import { sendChatQuery } from "../../api/caregiver";

export default function ChatAssistant({ patientId = "patient-101" }) {
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content: (
        "Hello! I am your clinical RAG-grounded medication assistant. " +
        "I can answer questions regarding scheduled doses, food and administration instructions, " +
        "or perform cross-checks for potential drug interactions based on your on-file health records."
      ),
      sources: [],
      severity: "none",
      timestamp: new Date(),
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedSources, setExpandedSources] = useState({});

  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (queryToSend = null) => {
    const text = (queryToSend || inputQuery).trim();
    if (!text || loading) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery("");
    setError(null);
    setLoading(true);

    try {
      const response = await sendChatQuery({
        patient_id: patientId,
        query: text,
      });

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        sources: response.sources || [],
        severity: response.severity || "none",
        requires_escalation: response.requires_escalation || false,
        timestamp: new Date(response.timestamp || Date.now()),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error("Chat assistant error:", err);
      setError(err.message || "Failed to reach medication assistant.");
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: "I apologize, but I encountered an issue retrieving clinical records. Please consult your physician directly regarding any urgent medication questions.",
          severity: "medium",
          sources: [],
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSourceExpand = (msgId, srcIdx) => {
    const key = `${msgId}-${srcIdx}`;
    setExpandedSources((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const demoChips = [
    "What do I take now?",
    "Can I take this with paracetamol and ibuprofen?",
    "What are the food instructions for Metformin?",
    "Did I miss any medication today?",
  ];

  const getModuleLabel = (mod) => {
    switch (mod) {
      case "schedule_service":
        return "📅 Timetable & Schedule";
      case "prescription_explainer":
        return "💊 Prescription Explainer";
      case "risk_interaction":
        return "⚠️ Interaction Engine";
      default:
        return "📄 Grounding Context";
    }
  };

  return (
    <div className="chat-assistant-container">
      <div className="chat-header">
        <div className="chat-header-info">
          <div className="avatar-ai">🤖</div>
          <div>
            <h3 className="chat-title">Grounded Medication Assistant</h3>
            <p className="chat-subtitle">
              Grounding: Person 1 (Explainer) • Person 2 (Schedule) • Person 3 (Interactions)
            </p>
          </div>
        </div>
        <div className="patient-tag">
          Patient: <strong>{patientId}</strong>
        </div>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="suggestion-chips-bar">
        <span className="chips-label">Quick Inquiries:</span>
        <div className="chips-row">
          {demoChips.map((chip, idx) => (
            <button
              key={idx}
              className="chip-btn"
              onClick={() => handleSend(chip)}
              disabled={loading}
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* Scrollable Message History */}
      <div className="chat-messages-viewport">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-bubble-wrapper ${
              msg.role === "user" ? "bubble-user" : "bubble-assistant"
            }`}
          >
            <div className="bubble-avatar">
              {msg.role === "user" ? "👤" : "🤖"}
            </div>
            
            <div className="bubble-content-col">
              {/* High Severity Risk Warning Banner */}
              {msg.role === "assistant" && (msg.severity === "high" || msg.severity === "critical") && (
                <div className="risk-alert-banner">
                  <span className="risk-icon">🚨</span>
                  <div>
                    <strong>High Clinical Risk Interaction Flagged</strong>
                    <p>Potential drug interaction detected between active medications.</p>
                  </div>
                </div>
              )}

              <div className="bubble-text">
                {msg.content.split("\n\n").map((para, i) => (
                  <p key={i} className="mb-2">{para}</p>
                ))}
              </div>

              {/* RAG Grounding Sources Display */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="grounding-sources-section">
                  <div className="sources-header">
                    <span className="sources-icon">🔍</span>
                    <span>Retrieved Clinical Evidence ({msg.sources.length} sources):</span>
                  </div>
                  <div className="sources-list">
                    {msg.sources.map((src, sIdx) => {
                      const isExpanded = expandedSources[`${msg.id}-${sIdx}`];
                      return (
                        <div key={sIdx} className="source-citation-card">
                          <div 
                            className="source-summary-row"
                            onClick={() => toggleSourceExpand(msg.id, sIdx)}
                          >
                            <span className="source-module-badge">
                              {getModuleLabel(src.module)}
                            </span>
                            <span className="source-title">{src.title}</span>
                            <span className="source-expand-toggle">
                              {isExpanded ? "▲ Hide" : "▼ Evidence"}
                            </span>
                          </div>
                          {isExpanded && (
                            <div className="source-expanded-snippet">
                              <pre>{src.snippet}</pre>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              <span className="message-timestamp">
                {msg.timestamp?.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="chat-bubble-wrapper bubble-assistant">
            <div className="bubble-avatar">🤖</div>
            <div className="bubble-content-col">
              <div className="bubble-text loading-bubble">
                <span className="dot dot-1"></span>
                <span className="dot dot-2"></span>
                <span className="dot dot-3"></span>
                <span className="loading-label">Grounding response from records...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {error && (
        <div className="chat-error-bar">
          <span>⚠️ {error}</span>
        </div>
      )}

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="chat-input-bar"
      >
        <input
          type="text"
          placeholder="Ask a question (e.g. 'Can I take this with paracetamol?' or 'What do I take now?')..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          disabled={loading}
          className="chat-text-input"
        />
        <button
          type="submit"
          disabled={loading || !inputQuery.trim()}
          className="btn-send"
        >
          <span>Send</span>
          <span className="send-arrow">➤</span>
        </button>
      </form>
    </div>
  );
}
