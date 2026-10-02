/**
 * Speech Synthesis (TTS) & Speech Recognition (STT) Utilities
 * For Interactive AI DSA Coach Voice Mode & Mock Interviews
 */

export const cleanMarkdownForSpeech = (text: string): string => {
  if (!text) return '';
  return text
    // Replace code blocks with descriptive text
    .replace(/```[\s\S]*?```/g, ' Code snippet omitted. ')
    // Replace inline code backticks
    .replace(/`([^`]+)`/g, '$1')
    // Remove bold and italics
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    // Remove markdown headers
    .replace(/^#+\s+/gm, '')
    // Remove blockquotes and list bullets
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*>\s+/gm, '')
    // Replace markdown links with just link text
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    // Clean up excessive whitespace and newlines
    .replace(/\n+/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim();
};

export const isSpeechSynthesisSupported = (): boolean => {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
};

export const stopSpeaking = (): void => {
  if (isSpeechSynthesisSupported()) {
    try {
      window.speechSynthesis.cancel();
    } catch {
      // Ignore
    }
  }
};

export const speak = (
  text: string,
  onStart?: () => void,
  onEnd?: () => void,
  onError?: (err: unknown) => void
): (() => void) => {
  if (!isSpeechSynthesisSupported()) {
    onError?.(new Error('Speech synthesis is not supported in this browser.'));
    return () => {};
  }

  // Cancel any currently playing audio
  stopSpeaking();

  const cleanText = cleanMarkdownForSpeech(text);
  if (!cleanText) {
    onEnd?.();
    return () => {};
  }

  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.lang = 'en-US';

  // Pick a natural sounding English voice if available
  const setVoice = () => {
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      const preferredVoice =
        voices.find(
          (v) =>
            v.lang.startsWith('en') &&
            (v.name.includes('Natural') ||
              v.name.includes('Google') ||
              v.name.includes('Samantha') ||
              v.name.includes('Daniel') ||
              v.name.includes('Aaron') ||
              v.name.includes('Karen'))
        ) || voices.find((v) => v.lang.startsWith('en'));

      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
    }
  };

  setVoice();
  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = setVoice;
  }

  utterance.onstart = () => {
    onStart?.();
  };

  utterance.onend = () => {
    onEnd?.();
  };

  utterance.onerror = (e) => {
    if (e.error !== 'canceled') {
      onError?.(e);
    }
    onEnd?.();
  };

  try {
    window.speechSynthesis.speak(utterance);
  } catch (err) {
    onError?.(err);
  }

  return () => {
    stopSpeaking();
  };
};

export const isSpeechRecognitionSupported = (): boolean => {
  if (typeof window === 'undefined') return false;
  return Boolean(
    (window as unknown as { SpeechRecognition?: unknown }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: unknown }).webkitSpeechRecognition
  );
};

export interface SpeechRecognizerController {
  start: () => void;
  stop: () => void;
  abort: () => void;
}

export const createSpeechRecognizer = (
  onTranscript: (transcript: string, isFinal: boolean) => void,
  onEnd?: () => void,
  onError?: (error: unknown) => void
): SpeechRecognizerController | null => {
  if (!isSpeechRecognitionSupported()) {
    return null;
  }

  const SpeechRecognitionClass =
    (window as unknown as { SpeechRecognition?: any }).SpeechRecognition ||
    (window as unknown as { webkitSpeechRecognition?: any }).webkitSpeechRecognition;

  if (!SpeechRecognitionClass) return null;

  const recognition = new SpeechRecognitionClass();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event: any) => {
    let fullTranscript = '';
    let isFinal = false;

    for (let i = 0; i < event.results.length; i++) {
      const result = event.results[i];
      if (result[0]) {
        fullTranscript += result[0].transcript;
      }
      if (result.isFinal) {
        isFinal = true;
      }
    }

    onTranscript(fullTranscript, isFinal);
  };

  recognition.onerror = (event: any) => {
    // 'no-speech' or 'aborted' are common non-fatal states
    if (event.error !== 'no-speech' && event.error !== 'aborted') {
      onError?.(event);
    }
  };

  recognition.onend = () => {
    onEnd?.();
  };

  return {
    start: () => {
      try {
        recognition.start();
      } catch (err) {
        console.warn('Recognition start exception:', err);
      }
    },
    stop: () => {
      try {
        recognition.stop();
      } catch (err) {
        console.warn('Recognition stop exception:', err);
      }
    },
    abort: () => {
      try {
        recognition.abort();
      } catch (err) {
        console.warn('Recognition abort exception:', err);
      }
    },
  };
};
