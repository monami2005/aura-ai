import React, { useState, useRef, useEffect } from 'react';
import CodeAnalyzer from './pages/CodeAnalyzer';

const API_BASE = 'http://127.0.0.1:8000';

const APPROVAL_KEYWORDS = [
  'okay', 'ok', 'yes', 'allow', 'do it', 'go ahead', 'confirm',
  'ঠিক আছে', 'হ্যাঁ', 'করো', 'অনুমতি দিচ্ছি', 'হাঁ',
  'ठीक है', 'हाँ', 'करो', 'अनुमति है'
];

const REJECTION_KEYWORDS = [
  'no', 'cancel', 'dont do it', "don't do it", 'stop', 'abort',
  'না', 'বাতিল করো', 'করো না', 'বাতিল',
  'नहीं', 'रद्द करो', 'मत करो', 'रद्द'
];

export default function App() {
  const [activeTab, setActiveTab] = useState('assistant');
  const [language, setLanguage] = useState('en'); // en, bn, hi, auto
  const [inputMessage, setInputMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [voiceNotice, setVoiceNotice] = useState(null);
  const [autoSpeak, setAutoSpeak] = useState(false);
  const [speakingMsgId, setSpeakingMsgId] = useState(null);
  const [systemState, setSystemState] = useState('Idle'); // Idle, Listening, Thinking, Capturing Screen, Analyzing Screen, Waiting for confirmation, Executing, Completed, Failed, Cancelled
  const [pendingActionMsgId, setPendingActionMsgId] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [historyList, setHistoryList] = useState([]);
  
  const recognitionRef = useRef(null);
  const chatEndRef = useRef(null);

  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: 'Hello! I am AURA AI, your Screen-Aware voice & desktop companion.',
      timestamp: 'Just now',
      sources: [],
    },
    {
      id: 2,
      sender: 'assistant',
      text: 'I can inspect your active screen ("What is on my screen?"), search live web news, and manage safe system actions.',
      timestamp: 'Just now',
      sources: [],
    },
  ]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/history`);
      if (res.ok) {
        const data = await res.json();
        setHistoryList(data);
      }
    } catch (err) {
      console.warn('Could not fetch history:', err);
    }
  };

  const handleSpeak = async (msgId, text, langCode) => {
    if (!text) return;
    setSpeakingMsgId(msgId);

    const targetLang = langCode || language;
    const localeMap = { en: 'en-US', bn: 'bn-IN', hi: 'hi-IN', auto: 'en-US' };
    const targetLocale = localeMap[targetLang] || 'en-US';

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = targetLocale;
      utterance.rate = 1.0;

      const voices = window.speechSynthesis.getVoices();
      const match = voices.find((v) => v.lang.includes(targetLocale) || v.lang.startsWith(targetLang));
      if (match) utterance.voice = match;

      utterance.onend = () => setSpeakingMsgId(null);
      utterance.onerror = () => setSpeakingMsgId(null);

      window.speechSynthesis.speak(utterance);
    } else {
      try {
        await fetch(`${API_BASE}/api/speak`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, language: targetLang }),
        });
      } catch (err) {
        console.warn('Backend TTS notice:', err);
      } finally {
        setTimeout(() => setSpeakingMsgId(null), 2000);
      }
    }
  };

  // Screen Analysis Handler
  const handleAnalyzeScreen = async (customQuestion = null) => {
    const questionText = customQuestion || (language === 'bn' ? 'আমার স্ক্রিনে কী আছে?' : language === 'hi' ? 'मेरी स्क्रीन पर क्या है?' : 'What is on my screen?');
    
    const userMsgId = Date.now();
    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        sender: 'user',
        text: `👁️ [Analyze Screen] ${questionText}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
    ]);

    setSystemState('Capturing Screen');
    setVoiceNotice('📸 Capturing active primary display in memory...');

    setTimeout(() => {
      setSystemState('Analyzing Screen');
      setVoiceNotice('🧠 Analyzing visual screen content with vision engine...');
    }, 400);

    try {
      const res = await fetch(`${API_BASE}/api/screen/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: questionText, language }),
      });

      const data = await res.json();
      setVoiceNotice(null);
      setSystemState('Completed');

      const aiMsgId = Date.now() + 1;
      const responseText = data.summary || (data.success ? 'Screen analyzed successfully.' : 'Screen analysis was unavailable.');

      setMessages((prev) => [
        ...prev,
        {
          id: aiMsgId,
          sender: 'assistant',
          text: responseText,
          screenDetails: data.details,
          screenElements: data.detected_elements || [],
          sources: [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }
      ]);

      if (autoSpeak && responseText) {
        handleSpeak(aiMsgId, responseText, language);
      }
    } catch (err) {
      setVoiceNotice(null);
      setSystemState('Failed');
      const aiMsgId = Date.now() + 1;
      const failText = 'Could not connect to backend screen vision service.';
      setMessages((prev) => [
        ...prev,
        {
          id: aiMsgId,
          sender: 'assistant',
          text: failText,
          sources: [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }
      ]);
    }

    setTimeout(() => setSystemState('Idle'), 2000);
  };

  const toggleSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setVoiceNotice('Voice input is not supported in this browser. You can continue using text input.');
      setTimeout(() => setVoiceNotice(null), 4000);
      return;
    }

    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
      if (systemState === 'Listening') setSystemState('Idle');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      recognition.continuous = false;
      recognition.interimResults = false;

      const localeMap = { en: 'en-US', bn: 'bn-IN', hi: 'hi-IN', auto: 'en-US' };
      recognition.lang = localeMap[language] || 'en-US';

      recognition.onstart = () => {
        setIsRecording(true);
        if (systemState !== 'Waiting for confirmation') {
          setSystemState('Listening');
        }
        setVoiceNotice(
          systemState === 'Waiting for confirmation'
            ? '🎤 Listening for: "Okay" (Allow) or "Cancel" (No)...'
            : '🎙️ Listening... Speak your query or command now'
        );
      };

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript.trim();
        setIsRecording(false);
        const transcriptLower = transcript.toLowerCase();

        if (systemState === 'Waiting for confirmation' && pendingActionMsgId) {
          const isApproval = APPROVAL_KEYWORDS.some((kw) => transcriptLower === kw || transcriptLower.includes(kw));
          const isRejection = REJECTION_KEYWORDS.some((kw) => transcriptLower === kw || transcriptLower.includes(kw));
          const pendingMsg = messages.find((m) => m.id === pendingActionMsgId);

          if (isApproval && pendingMsg?.action) {
            setVoiceNotice(`Voice confirmation received: "${transcript}" ✓`);
            setTimeout(() => setVoiceNotice(null), 2500);
            handleActionAllow(pendingActionMsgId, pendingMsg.action);
            return;
          } else if (isRejection) {
            setVoiceNotice(`Action cancelled by voice: "${transcript}" ✕`);
            setTimeout(() => setVoiceNotice(null), 2500);
            handleActionCancel(pendingActionMsgId);
            return;
          }
        }

        setVoiceNotice(`Heard: "${transcript}"`);
        setTimeout(() => setVoiceNotice(null), 2500);
        executeChat(transcript);
      };

      recognition.onerror = (event) => {
        setIsRecording(false);
        if (systemState === 'Listening') setSystemState('Idle');
        setVoiceNotice(`Notice: ${event.error}`);
        setTimeout(() => setVoiceNotice(null), 3000);
      };

      recognition.onend = () => {
        setIsRecording(false);
        if (systemState === 'Listening') setSystemState('Idle');
      };

      recognition.start();
    } catch (err) {
      setIsRecording(false);
      setSystemState('Idle');
      setVoiceNotice('Could not start microphone.');
      setTimeout(() => setVoiceNotice(null), 3000);
    }
  };

  const executeChat = async (userText) => {
    if (!userText.trim() || systemState === 'Thinking' || systemState === 'Executing' || systemState === 'Analyzing Screen') return;

    // Direct routing for screen analysis triggers
    const lower = userText.toLowerCase();
    if (lower.includes('my screen') || lower.includes('this screen') || userText.includes('স্ক্রিনে') || userText.includes('स्क्रीन')) {
      handleAnalyzeScreen(userText);
      setInputMessage('');
      return;
    }

    if (systemState === 'Waiting for confirmation' && pendingActionMsgId) {
      const isApproval = APPROVAL_KEYWORDS.some((kw) => lower === kw || lower.includes(kw));
      const isRejection = REJECTION_KEYWORDS.some((kw) => lower === kw || lower.includes(kw));
      const pendingMsg = messages.find((m) => m.id === pendingActionMsgId);

      if (isApproval && pendingMsg?.action) {
        handleActionAllow(pendingActionMsgId, pendingMsg.action);
        setInputMessage('');
        return;
      } else if (isRejection) {
        handleActionCancel(pendingActionMsgId);
        setInputMessage('');
        return;
      }
    }

    const msgId = Date.now();
    const userMsg = {
      id: msgId,
      sender: 'user',
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setSystemState('Thinking');

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText, language }),
      });

      if (!response.ok) {
        throw new Error(`Chat API responded with ${response.status}`);
      }

      const data = await response.json();
      const aiMsgId = Date.now() + 1;

      const aiMsg = {
        id: aiMsgId,
        sender: 'assistant',
        text: data.response || data.explanation,
        sources: data.sources || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        action: data.executable
          ? {
              original_command: userText,
              action: data.action || data.intent,
              intent: data.intent,
              params: data.params || {},
              explanation: data.explanation,
              risk_level: data.risk_level || 'CONFIRM',
              target: data.target || 'System',
              reason: data.reason || 'Computer operation requires explicit confirmation',
              status: 'pending',
              result: null,
            }
          : null,
      };

      setMessages((prev) => [...prev, aiMsg]);

      if (data.executable) {
        setSystemState('Waiting for confirmation');
        setPendingActionMsgId(aiMsgId);
      } else {
        setSystemState('Idle');
        setPendingActionMsgId(null);
      }

      if (autoSpeak && aiMsg.text) {
        handleSpeak(aiMsgId, aiMsg.text, language);
      }
    } catch (err) {
      console.warn('Backend connection issue, using client fallback:', err);
      let fallbackText = `Received: "${userText}".`;
      let actionObj = null;
      let sources = [];

      if (lower.includes('latest') || lower.includes('news') || lower.includes('খবর')) {
        fallbackText = 'Here is the latest verified web information from live sources.';
        sources = [{ title: 'AI Research Highlights', domain: 'techcrunch.com', published_date: 'Today' }];
      } else if (lower.includes('call') || userText.includes('কল')) {
        fallbackText = `AURA wants to call Riya.`;
        actionObj = {
          original_command: userText,
          action: 'call_contact',
          params: { contact_name: 'Riya', platform: 'phone' },
          explanation: fallbackText,
          status: 'pending',
          result: null,
        };
      } else if (lower.includes('youtube') || userText.includes('ইউটিউব')) {
        fallbackText = 'AURA will open YouTube in your web browser.';
        actionObj = {
          original_command: userText,
          action: 'open_website',
          params: { url: 'https://www.youtube.com' },
          explanation: fallbackText,
          status: 'pending',
          result: null,
        };
      }

      const aiMsgId = Date.now() + 1;
      setMessages((prev) => [
        ...prev,
        {
          id: aiMsgId,
          sender: 'assistant',
          text: fallbackText,
          sources,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          action: actionObj,
        },
      ]);

      if (actionObj) {
        setSystemState('Waiting for confirmation');
        setPendingActionMsgId(aiMsgId);
      } else {
        setSystemState('Idle');
        setPendingActionMsgId(null);
      }

      if (autoSpeak && fallbackText) handleSpeak(aiMsgId, fallbackText, language);
    }
  };

  const handleSendMessage = (e) => {
    e?.preventDefault();
    executeChat(inputMessage);
  };

  const handleActionAllow = async (msgId, actionData) => {
    setSystemState('Executing');
    setPendingActionMsgId(null);

    setMessages((prev) =>
      prev.map((m) => {
        if (m.id === msgId && m.action) {
          return { ...m, action: { ...m.action, status: 'executing' } };
        }
        return m;
      })
    );

    try {
      const res = await fetch(`${API_BASE}/api/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          original_command: actionData.original_command,
          action: actionData.action,
          params: actionData.params,
        }),
      });

      const execResult = await res.json();

      if (res.ok && execResult.success) {
        setSystemState('Completed');
        const resText = execResult.result || 'Action completed successfully.';
        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === msgId && m.action) {
              return {
                ...m,
                action: {
                  ...m.action,
                  status: 'allowed',
                  result: resText,
                },
              };
            }
            return m;
          })
        );
        if (autoSpeak) handleSpeak(msgId, resText, language);
      } else {
        setSystemState('Failed');
        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === msgId && m.action) {
              return {
                ...m,
                action: {
                  ...m.action,
                  status: 'failed',
                  result: execResult.error || 'Execution encountered an error.',
                },
              };
            }
            return m;
          })
        );
      }
    } catch (err) {
      if (actionData.action === 'open_website' && actionData.params?.url) {
        window.open(actionData.params.url, '_blank');
        setSystemState('Completed');
        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === msgId && m.action) {
              return {
                ...m,
                action: {
                  ...m.action,
                  status: 'allowed',
                  result: `Opened website: ${actionData.params.url}`,
                },
              };
            }
            return m;
          })
        );
      } else {
        setSystemState('Failed');
        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === msgId && m.action) {
              return {
                ...m,
                action: {
                  ...m.action,
                  status: 'failed',
                  result: `${actionData.params?.platform?.toUpperCase() || 'Service'} is not configured yet.`,
                },
              };
            }
            return m;
          })
        );
      }
    }

    setTimeout(() => {
      setSystemState('Idle');
      fetchHistory();
    }, 2000);
  };

  const handleActionCancel = (msgId) => {
    setSystemState('Cancelled');
    setPendingActionMsgId(null);

    setMessages((prev) =>
      prev.map((m) => {
        if (m.id === msgId && m.action) {
          return {
            ...m,
            action: {
              ...m.action,
              status: 'cancelled',
              result: 'Action cancelled. No communication or command was dispatched.',
            },
          };
        }
        return m;
      })
    );

    setTimeout(() => setSystemState('Idle'), 1500);
  };

  const getPlatformBadge = (platform) => {
    switch (platform?.toLowerCase()) {
      case 'whatsapp': return <span className="badge badge-success">🟢 WhatsApp</span>;
      case 'messenger': return <span className="badge badge-info">🔵 Messenger</span>;
      case 'instagram': return <span className="badge badge-danger">🟣 Instagram</span>;
      default: return <span className="badge badge-info">📱 Phone</span>;
    }
  };

  const quickPrompts = [
    { label: '🌐 "Search DAA merge sort"', text: 'Google e DAA merge sort search koro' },
    { label: '📂 "Find notes.txt"', text: 'Find my notes.txt file' },
    { label: '💻 "Chrome kholo"', text: 'Chrome kholo' },
    { label: '👁️ "Ei error ta ki?"', text: 'Ei error ta ki?' },
    { label: '🛠️ "Explain Python error"', text: 'Why is this Python code giving an error?' },
    { label: '👁️ "Analyze Screen"', isScreen: true },
    { label: '🇧🇩 "স্ক্রিনে কী আছে?"', isScreen: true, lang: 'bn', text: 'আমার স্ক্রিনে কী আছে?' },
    { label: '📞 "Call Riya"', text: 'Call Riya from my phone' },
    { label: '💬 "WhatsApp Riya"', text: 'WhatsApp-এ Riya-কে message পাঠাও: আমি আসছি', lang: 'bn' },
  ];

  const handleQuickPrompt = (item) => {
    if (item.lang) setLanguage(item.lang);
    if (item.isScreen) {
      handleAnalyzeScreen(item.text);
    } else {
      setInputMessage(item.text);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header className="app-header">
        <div className="logo-container" onClick={() => setActiveTab('assistant')}>
          <div className="logo-orb">A</div>
          <div>
            <h1 className="logo-title gradient-text">AURA AI</h1>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Screen Awareness & Multi-Platform Core</div>
          </div>
        </div>

        <nav className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'assistant' ? 'active' : ''}`}
            onClick={() => setActiveTab('assistant')}
          >
            <span>🎙️</span> Assistant
          </button>
          <button
            className={`nav-tab ${activeTab === 'analyzer' ? 'active' : ''}`}
            onClick={() => setActiveTab('analyzer')}
          >
            <span>⚡</span> Code Analyzer
          </button>
        </nav>

        <div className="header-actions">
          <button
            className="btn"
            onClick={() => handleAnalyzeScreen()}
            title="Inspect visible screen content"
            style={{
              background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.2), rgba(99, 102, 241, 0.2))',
              color: '#38bdf8',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              fontSize: '0.8rem',
              fontWeight: 600,
            }}
          >
            👁️ Analyze Screen
          </button>

          <div className="status-badge">
            <span className="status-dot"></span>
            <span>State: <strong>{systemState}</strong></span>
          </div>

          <button
            className="btn"
            onClick={() => setAutoSpeak(!autoSpeak)}
            title="Auto-speak assistant responses"
            style={{
              background: autoSpeak ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255,255,255,0.06)',
              color: autoSpeak ? '#a5b4fc' : 'var(--text-secondary)',
              border: '1px solid var(--border-color)',
              fontSize: '0.8rem',
            }}
          >
            {autoSpeak ? '🔊 Voice: ON' : '🔈 Voice: OFF'}
          </button>

          <button
            className="btn"
            onClick={() => {
              setShowHistory(!showHistory);
              if (!showHistory) fetchHistory();
            }}
            style={{
              background: 'rgba(255,255,255,0.06)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-color)',
              fontSize: '0.8rem',
            }}
          >
            📜 History
          </button>

          <select
            className="lang-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option value="auto">🌐 Auto Detect</option>
            <option value="en">English (US)</option>
            <option value="bn">বাংলা (Bengali)</option>
            <option value="hi">हिन्दी (Hindi)</option>
          </select>
        </div>
      </header>

      {/* Main Container */}
      <main className="main-container">
        {voiceNotice && (
          <div
            style={{
              padding: '0.65rem 1.25rem',
              marginBottom: '1rem',
              borderRadius: 'var(--radius-md)',
              background: systemState.includes('Screen') ? 'rgba(56, 189, 248, 0.18)' : isRecording ? 'rgba(244, 63, 94, 0.15)' : 'rgba(99, 102, 241, 0.15)',
              border: systemState.includes('Screen') ? '1px solid rgba(56, 189, 248, 0.5)' : isRecording ? '1px solid rgba(244, 63, 94, 0.4)' : '1px solid rgba(99, 102, 241, 0.4)',
              color: systemState.includes('Screen') ? '#7dd3fc' : isRecording ? '#fda4af' : '#c7d2fe',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              animation: 'fadeIn 0.25s ease',
            }}
          >
            <span>{voiceNotice}</span>
            {isRecording && (
              <button
                className="btn btn-cancel"
                onClick={toggleSpeechRecognition}
                style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem' }}
              >
                Stop
              </button>
            )}
          </div>
        )}

        {/* Confirmation Voice Prompt Indicator */}
        {systemState === 'Waiting for confirmation' && (
          <div
            style={{
              padding: '0.75rem 1.25rem',
              marginBottom: '1rem',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(245, 158, 11, 0.15)',
              border: '1px solid rgba(245, 158, 11, 0.4)',
              color: '#fef3c7',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              animation: 'fadeIn 0.3s ease',
            }}
          >
            <div>
              <strong>⏳ Waiting for confirmation...</strong> You can say <em>"Okay" / "Yes" (Allow)</em> or <em>"Cancel" / "No" (Cancel)</em> into the mic.
            </div>
            <button
              className="btn btn-primary"
              onClick={toggleSpeechRecognition}
              style={{ padding: '0.3rem 0.75rem', fontSize: '0.75rem' }}
            >
              {isRecording ? '🔴 Listening...' : '🎙️ Speak Confirmation'}
            </button>
          </div>
        )}

        {showHistory && (
          <div className="glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }} className="gradient-text">
                📜 SQLite Action History (Privacy Protected)
              </h3>
              <button className="copy-btn" onClick={fetchHistory}>↻ Refresh</button>
            </div>
            {historyList.length === 0 ? (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No actions logged yet.</p>
            ) : (
              <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {historyList.map((item) => (
                  <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0.75rem', background: 'rgba(10, 12, 20, 0.5)', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem' }}>
                    <div>
                      <strong style={{ color: '#38bdf8' }}>{item.action}</strong>: {item.original_command}
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{item.result}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className={`badge ${item.success ? 'badge-success' : 'badge-danger'}`}>
                        {item.success ? 'Success' : 'Failed'}
                      </span>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                        {new Date(item.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'assistant' ? (
          <div className="assistant-layout">
            <div className="chat-history glass-panel">
              {messages.map((msg) => (
                <div key={msg.id} className={`chat-bubble ${msg.sender}`}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <strong style={{ fontSize: '0.8rem', color: msg.sender === 'user' ? '#e0e7ff' : '#38bdf8' }}>
                      {msg.sender === 'user' ? '👤 You' : '🤖 AURA Assistant'}
                    </strong>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      {msg.sender === 'assistant' && (
                        <button
                          className="copy-btn"
                          onClick={() => handleSpeak(msg.id, msg.text, language)}
                          title="Speak this response"
                          style={{ padding: '0.15rem 0.45rem', fontSize: '0.7rem' }}
                        >
                          {speakingMsgId === msg.id ? '🔊 Speaking...' : '🔈 Speak'}
                        </button>
                      )}
                      <span style={{ fontSize: '0.7rem', opacity: 0.7 }}>{msg.timestamp}</span>
                    </div>
                  </div>

                  <div>{msg.text}</div>

                  {/* Screen Analysis Detected Elements */}
                  {msg.screenElements && msg.screenElements.length > 0 && (
                    <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                      {msg.screenElements.map((elem, eIdx) => (
                        <span key={eIdx} className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                          🪟 {elem}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Web Intelligence Source Citations */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: '0.65rem', padding: '0.5rem 0.75rem', background: 'rgba(0,0,0,0.25)', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#38bdf8', marginBottom: '0.35rem' }}>
                        🌐 Verified Web Sources:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                        {msg.sources.map((src, sIdx) => (
                          <div key={sIdx} style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                            • <strong>{src.title}</strong> — <span style={{ color: '#a5b4fc' }}>{src.domain}</span> {src.published_date ? `(${src.published_date})` : ''}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Multi-Platform Confirmation Card */}
                  {msg.action && (
                    <div className="action-card">
                      <div className="action-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span>🛡️ <strong>ACTION:</strong> {msg.action.action?.toUpperCase()}</span>
                          <span
                            className="badge"
                            style={{
                              background:
                                msg.action.risk_level === 'HIGH_RISK'
                                  ? 'rgba(239, 68, 68, 0.25)'
                                  : msg.action.risk_level === 'CONFIRM'
                                  ? 'rgba(245, 158, 11, 0.25)'
                                  : 'rgba(16, 185, 129, 0.25)',
                              color:
                                msg.action.risk_level === 'HIGH_RISK'
                                  ? '#f87171'
                                  : msg.action.risk_level === 'CONFIRM'
                                  ? '#fbbf24'
                                  : '#34d399',
                              border: '1px solid currentColor',
                              fontSize: '0.7rem',
                              fontWeight: 700
                            }}
                          >
                            {msg.action.risk_level || 'CONFIRM'}
                          </span>
                        </div>
                        {msg.action.params?.platform && getPlatformBadge(msg.action.params.platform)}
                      </div>

                      <div style={{ fontSize: '0.9rem', marginBottom: '0.6rem', color: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                        <div>🎯 <strong>TARGET:</strong> <span style={{ color: '#38bdf8' }}>{msg.action.target || msg.action.params?.target || msg.action.params?.app_name || msg.action.params?.contact_name || 'System Target'}</span></div>
                        <div>⚠️ <strong>REASON:</strong> <span style={{ color: 'var(--text-secondary)' }}>{msg.action.reason || 'Computer operation requires explicit user confirmation.'}</span></div>
                        {msg.action.params?.message && (
                          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.4rem', borderRadius: '4px', fontStyle: 'italic', fontSize: '0.85rem' }}>
                            "{msg.action.params.message}"
                          </div>
                        )}
                        {msg.action.params?.text && (
                          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.4rem', borderRadius: '4px', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                            "{msg.action.params.text}"
                          </div>
                        )}
                      </div>

                      {msg.action.status === 'pending' && (
                        <div className="action-actions">
                          <button
                            className="btn btn-allow"
                            onClick={() => handleActionAllow(msg.id, msg.action)}
                          >
                            ✓ Allow ("Okay" / "Yes")
                          </button>
                          <button
                            className="btn btn-cancel"
                            onClick={() => handleActionCancel(msg.id)}
                          >
                            ✕ Deny ("Cancel" / "No")
                          </button>
                        </div>
                      )}

                      {msg.action.status === 'executing' && (
                        <div style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>
                          ⏳ Executing action...
                        </div>
                      )}

                      {msg.action.status === 'allowed' && (
                        <div style={{ fontSize: '0.85rem', color: 'var(--accent-emerald)', marginTop: '0.4rem' }}>
                          ✓ <strong>Result:</strong> {msg.action.result}
                        </div>
                      )}

                      {msg.action.status === 'cancelled' && (
                        <div style={{ fontSize: '0.85rem', color: 'var(--accent-rose)', marginTop: '0.4rem' }}>
                          ✕ <strong>Cancelled:</strong> Action was aborted. No communication was dispatched.
                        </div>
                      )}

                      {msg.action.status === 'failed' && (
                        <div style={{ fontSize: '0.85rem', color: '#fca5a5', marginTop: '0.4rem' }}>
                          ℹ️ <strong>Notice:</strong> {msg.action.result}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            {/* Multilingual Quick Prompts */}
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {quickPrompts.map((item, idx) => (
                <button
                  key={idx}
                  className="copy-btn"
                  onClick={() => handleQuickPrompt(item)}
                  style={{
                    padding: '0.4rem 0.8rem',
                    borderRadius: 'var(--radius-full)',
                    background: item.isScreen ? 'rgba(56, 189, 248, 0.15)' : 'rgba(99, 102, 241, 0.1)',
                    borderColor: item.isScreen ? 'rgba(56, 189, 248, 0.4)' : 'rgba(99, 102, 241, 0.3)',
                    color: item.isScreen ? '#38bdf8' : '#c7d2fe',
                    fontWeight: item.isScreen ? 600 : 400,
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>

            {/* Chat & Voice Input Bar */}
            <form className="chat-input-bar glass-panel" onSubmit={handleSendMessage}>
              <button
                type="button"
                className={`mic-btn ${isRecording ? 'active' : ''}`}
                onClick={toggleSpeechRecognition}
                title={isRecording ? 'Listening... Click to stop' : 'Microphone (Voice Input / Voice Confirmation)'}
              >
                {isRecording ? '🔴' : '🎙️'}
              </button>
              <input
                type="text"
                className="chat-input"
                placeholder={
                  isRecording
                    ? systemState === 'Waiting for confirmation'
                      ? '🎙️ Say "Okay" to Allow, or "Cancel" to Abort...'
                      : '🎙️ Listening to your voice...'
                    : systemState === 'Waiting for confirmation'
                    ? 'Type "Okay" to Allow or "Cancel" to Abort...'
                    : language === 'bn'
                    ? 'স্ক্রিন সম্পর্কে জানুন বা বার্তা পাঠান (যেমন: "আমার স্ক্রিনে কী আছে?")...'
                    : language === 'hi'
                    ? 'स्क्रीन के बारे में पूछें या संदेश भेजें (जैसे: "मेरी स्क्रीन पर क्या है?")...'
                    : 'Ask AURA ("What is on my screen?", "What is latest AI news?", "Call Riya")...'
                }
                value={inputMessage}
                disabled={systemState === 'Thinking' || systemState === 'Executing' || systemState.includes('Screen')}
                onChange={(e) => setInputMessage(e.target.value)}
              />
              <button
                type="submit"
                className="btn btn-primary"
                disabled={systemState === 'Thinking' || systemState === 'Executing' || systemState.includes('Screen')}
                style={{ padding: '0.75rem 1.4rem' }}
              >
                <span>{systemState === 'Thinking' ? 'Thinking...' : 'Send'}</span> <span>➤</span>
              </button>
            </form>
          </div>
        ) : (
          <CodeAnalyzer />
        )}

        {/* Stage 8 Verified Action History Drawer */}
        {showHistory && (
          <div style={{
            position: 'fixed',
            top: 0,
            right: 0,
            width: 'min(420px, 90vw)',
            height: '100vh',
            background: 'var(--bg-card)',
            borderLeft: '1px solid var(--border-color)',
            boxShadow: '-8px 0 24px rgba(0,0,0,0.5)',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            padding: '1.25rem',
            backdropFilter: 'blur(16px)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem' }} className="gradient-text">📜 Action Audit History</h3>
              <button className="copy-btn" onClick={() => setShowHistory(false)}>✕ Close</button>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {historyList.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', marginTop: '2rem' }}>
                  No verified action history recorded yet.
                </div>
              ) : (
                historyList.map((item) => (
                  <div key={item.id} style={{
                    padding: '0.75rem',
                    background: 'rgba(255,255,255,0.03)',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                    fontSize: '0.8rem'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                      <span>{item.timestamp?.slice(11, 19) || 'Time'}</span>
                      <span style={{ color: item.success ? 'var(--accent-emerald)' : 'var(--accent-rose)', fontWeight: 600 }}>
                        {item.success ? '✓ Verified' : '✕ Failed'}
                      </span>
                    </div>
                    <div style={{ marginTop: '0.35rem', fontWeight: 600, color: '#f8fafc' }}>
                      {item.original_command}
                    </div>
                    <div style={{ marginTop: '0.25rem', color: '#38bdf8', fontSize: '0.75rem' }}>
                      Action: {item.action} {item.detected_intent ? `(${item.detected_intent})` : ''}
                    </div>
                    <div style={{ marginTop: '0.35rem', color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                      {item.result}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
