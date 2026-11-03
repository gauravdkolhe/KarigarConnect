import React, { useState, useEffect, useRef } from 'react';
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

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      setIsSupported(true);
      const recog = new SpeechRecognition();
      recog.continuous = false;
      recog.interimResults = false;
      recog.lang = lang;

      recog.onresult = (event: any) => {
        const transcript = event.results?.[0]?.[0]?.transcript || '';
        if (transcript) {
          onTranscript(transcript);
        }
        setIsListening(false);
      };

      recog.onerror = (err: any) => {
        console.warn('Speech recognition error:', err);
        setIsListening(false);
      };

      recog.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recog;
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // quiet abort
        }
      }
    };
  }, [lang, onTranscript]);

  const toggleListening = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isSupported) {
      alert('Voice-to-text is supported on Google Chrome, Samsung Internet, Microsoft Edge, and Safari. Please use a supported browser or grant microphone permissions.');
      return;
    }

    if (isListening) {
      try {
        recognitionRef.current?.stop();
      } catch {
        // quiet
      }
      setIsListening(false);
    } else {
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch (err) {
        console.warn('Failed to start speech recognition:', err);
        setIsListening(false);
      }
    }
  };

  if (!isSupported) {
    return null;
  }

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
      title={isListening ? 'Listening... click to stop' : 'Click to speak (Voice-to-Text)'}
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
        boxShadow: isListening ? '0 0 10px rgba(220, 38, 38, 0.3)' : 'var(--shadow-sm)',
      }}
    >
      {isListening ? (
        <>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: '#DC2626',
              animation: 'pulse 1s infinite',
            }}
          />
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
