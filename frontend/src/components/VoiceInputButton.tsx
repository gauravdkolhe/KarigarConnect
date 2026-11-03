import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';

interface VoiceInputButtonProps {
  onTranscript: (text: string) => void;
  lang?: string;
  placeholder?: string;
  className?: string;
  large?: boolean;
}

export const VoiceInputButton: React.FC<VoiceInputButtonProps> = ({
  onTranscript,
  lang = 'en-IN',
  placeholder = 'Speak now...',
  className = '',
  large = false,
}) => {
  const [isListening, setIsListening] = useState(false);
  // Always render — show mic even before we know if it's supported
  const [supported, setSupported] = useState<boolean | null>(null);
  const recogRef = useRef<any>(null);
  const callbackRef = useRef(onTranscript);
  const langRef = useRef(lang);

  // Keep refs fresh without re-running the setup effect
  useEffect(() => { callbackRef.current = onTranscript; });
  useEffect(() => {
    langRef.current = lang;
    if (recogRef.current) recogRef.current.lang = lang;
  }, [lang]);

  // Setup ONCE on mount
  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setSupported(false); return; }

    setSupported(true);
    const r = new SR();
    r.continuous = false;
    r.interimResults = false;
    r.lang = langRef.current;

    r.onresult = (e: any) => {
      const txt: string = e.results?.[0]?.[0]?.transcript || '';
      if (txt) callbackRef.current(txt);
      setIsListening(false);
    };
    r.onerror = () => setIsListening(false);
    r.onend   = () => setIsListening(false);
    recogRef.current = r;

    return () => { try { r.abort(); } catch { /**/ } };
  }, []); // empty — run once

  const toggle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!recogRef.current) {
      alert('Voice input not supported in this browser. Please use Chrome or Samsung Internet.');
      return;
    }

    if (isListening) {
      try { recogRef.current.stop(); } catch { /**/ }
      setIsListening(false);
    } else {
      recogRef.current.lang = langRef.current;
      try { recogRef.current.start(); setIsListening(true); }
      catch (err) { console.warn('mic start failed', err); setIsListening(false); }
    }
  };

  // Don't hide even while "null" (checking) — just render with dim style
  const isUnsupported = supported === false;

  if (large) {
    return (
      <button type="button" onClick={toggle} className={`voice-mic-btn ${className}`}
        disabled={isUnsupported}
        title={isUnsupported ? 'Use Chrome / Samsung Internet for voice' : isListening ? 'Tap to stop' : 'Tap to speak'}
        style={{
          display: 'inline-flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', gap: '0.4rem',
          width: '88px', height: '88px', borderRadius: '50%',
          border: isListening ? '3px solid #DC2626' : '3px solid var(--color-primary)',
          backgroundColor: isListening ? '#FEF2F2' : 'var(--color-primary-subtle,#F5F3FF)',
          color: isListening ? '#DC2626' : 'var(--color-primary)',
          cursor: isUnsupported ? 'not-allowed' : 'pointer',
          opacity: isUnsupported ? 0.4 : 1,
          transition: 'all 0.2s ease',
          boxShadow: isListening
            ? '0 0 0 6px rgba(220,38,38,0.18),0 0 20px rgba(220,38,38,0.25)'
            : '0 0 0 4px rgba(124,58,237,0.1)',
          fontSize: '0.72rem', fontWeight: 600,
        }}>
        {isListening ? <><MicOff size={28} /><span>Stop</span></>
                     : <><Mic    size={28} /><span>Speak</span></>}
      </button>
    );
  }

  return (
    <button type="button" onClick={toggle} className={`voice-mic-btn ${className}`}
      disabled={isUnsupported}
      title={isUnsupported ? 'Use Chrome for voice input' : isListening ? 'Listening — click to stop' : 'Click to speak'}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
        padding: '0.4rem 0.75rem', borderRadius: 'var(--radius-full)',
        border: isListening ? '1px solid #DC2626' : '1px solid var(--color-border)',
        backgroundColor: isListening ? '#FEF2F2' : '#fff',
        color: isListening ? '#DC2626' : 'var(--color-text-muted)',
        fontSize: '0.8rem', fontWeight: 500, cursor: isUnsupported ? 'not-allowed' : 'pointer',
        opacity: isUnsupported ? 0.4 : 1,
        transition: 'all 0.2s ease',
        boxShadow: isListening ? '0 0 10px rgba(220,38,38,0.3)' : 'var(--shadow-sm)',
      }}>
      {isListening
        ? <><span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#DC2626', animation: 'pulse 1s infinite', flexShrink: 0 }} />
            <MicOff size={14} /><span>{placeholder}</span></>
        : <><Mic size={14} style={{ color: isUnsupported ? 'inherit' : 'var(--color-primary)' }} /><span>Speak</span></>}
    </button>
  );
};
