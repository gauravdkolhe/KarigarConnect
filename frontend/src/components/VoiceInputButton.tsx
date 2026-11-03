import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, MicOff } from 'lucide-react';

interface VoiceInputButtonProps {
  onTranscript: (text: string) => void;
  lang?: string;
  placeholder?: string;
  className?: string;
  /** Render a large hero-style mic button */
  large?: boolean;
}

export const VoiceInputButton: React.FC<VoiceInputButtonProps> = ({
  onTranscript,
  lang = 'en-IN',
  placeholder = 'Speak now...',
  className = '',
  large = false,
}) => {
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isSupported, setIsSupported] = useState<boolean>(false);
  const recognitionRef = useRef<any>(null);

  // Store the callback in a ref so the effect never needs to re-run when
  // the parent re-renders (inline arrow functions always have a new reference).
  const onTranscriptRef = useRef(onTranscript);
  useEffect(() => {
    onTranscriptRef.current = onTranscript;
  });

  // Also store lang in a ref so we can update it without recreating recognition.
  const langRef = useRef(lang);
  useEffect(() => {
    langRef.current = lang;
    // If recognition already exists, update its lang live.
    if (recognitionRef.current) {
      recognitionRef.current.lang = lang;
    }
  }, [lang]);

  // Create the SpeechRecognition object exactly ONCE on mount.
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) return;

    setIsSupported(true);

    const recog = new SpeechRecognition();
    recog.continuous = false;
    recog.interimResults = false;
    recog.lang = langRef.current;

    recog.onresult = (event: any) => {
      const transcript: string = event.results?.[0]?.[0]?.transcript || '';
      if (transcript) {
        onTranscriptRef.current(transcript);
      }
      setIsListening(false);
    };

    recog.onerror = (err: any) => {
      console.warn('Speech recognition error:', err.error, err.message);
      setIsListening(false);
    };

    recog.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recog;

    return () => {
      try { recog.abort(); } catch { /* quiet */ }
    };
  }, []); // ← empty deps: runs only once

  const toggleListening = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!recognitionRef.current) {
      alert(
        'Voice-to-text is not supported in this browser.\n' +
        'Please use Google Chrome, Samsung Internet, Microsoft Edge, or Safari.'
      );
      return;
    }

    // Update lang right before starting, in case language changed.
    recognitionRef.current.lang = langRef.current;

    if (isListening) {
      try { recognitionRef.current.stop(); } catch { /* quiet */ }
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        console.warn('Failed to start speech recognition:', err);
        setIsListening(false);
      }
    }
  }, [isListening]);

  if (!isSupported) return null;

  // ── Large hero mic button ──────────────────────────────────────────────────
  if (large) {
    return (
      <button
        type="button"
        onClick={toggleListening}
        className={`voice-mic-btn ${className}`}
        title={isListening ? 'Listening… tap to stop' : 'Tap to speak'}
        style={{
          display: 'inline-flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.4rem',
          width: '88px',
          height: '88px',
          borderRadius: '50%',
          border: isListening ? '3px solid #DC2626' : '3px solid var(--color-primary)',
          backgroundColor: isListening ? '#FEF2F2' : 'var(--color-primary-subtle, #F5F3FF)',
          color: isListening ? '#DC2626' : 'var(--color-primary)',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: isListening
            ? '0 0 0 6px rgba(220,38,38,0.18), 0 0 20px rgba(220,38,38,0.25)'
            : '0 0 0 4px rgba(124,58,237,0.1)',
          fontSize: '0.72rem',
          fontWeight: 600,
        }}
      >
        {isListening ? (
          <>
            <MicOff size={28} />
            <span>Stop</span>
          </>
        ) : (
          <>
            <Mic size={28} />
            <span>Speak</span>
          </>
        )}
      </button>
    );
  }

  // ── Small inline button (default) ─────────────────────────────────────────
  return (
    <button
      type="button"
      onClick={toggleListening}
      className={`voice-mic-btn ${className}`}
      title={isListening ? 'Listening... click to stop' : 'Click to speak'}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.35rem',
        padding: '0.4rem 0.75rem',
        borderRadius: 'var(--radius-full)',
        border: isListening ? '1px solid #DC2626' : '1px solid var(--color-border)',
        backgroundColor: isListening ? '#FEF2F2' : '#FFFFFF',
        color: isListening ? '#DC2626' : 'var(--color-text-muted)',
        fontSize: '0.8rem',
        fontWeight: 500,
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        boxShadow: isListening ? '0 0 10px rgba(220,38,38,0.3)' : 'var(--shadow-sm)',
      }}
    >
      {isListening ? (
        <>
          <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#DC2626', animation: 'pulse 1s infinite' }} />
          <MicOff size={14} />
          <span>{placeholder}</span>
        </>
      ) : (
        <>
          <Mic size={14} style={{ color: 'var(--color-primary)' }} />
          <span>Speak</span>
        </>
      )}
    </button>
  );
};
