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

/**
 * Normalizes acoustic speech recognition errors for DSA / coding interviews.
 * Specifically corrects phonetic misrecognitions of technical terms
 * without modifying the candidate's actual conceptual intention, claims, or errors.
 */
export const normalizeDsaSpeech = (rawText: string): string => {
  if (!rawText) return '';

  let text = rawText;

  // 1. Common acoustic misrecognitions for "brute force"
  text = text.replace(/\b(?:root|route|brew|fruit|brood|rude)\s*(?:force|froze|frost)\b/gi, 'brute force');
  text = text.replace(/\bbrut\s+force\b/gi, 'brute force');

  // 2. Misrecognitions for "iterate" / "iteration"
  text = text.replace(/\bhydrate(?:\s+through|\s+from|\s+over|\s+across|\s+the)?\b/gi, 'iterate through');
  text = text.replace(/\bhydrate\b/gi, 'iterate');
  text = text.replace(/\b(?:eye\s*iterate|eye\s*rate)\b/gi, 'iterate');
  text = text.replace(/\brate\s+through\s+the\s+array\b/gi, 'iterate through the array');

  // 3. Two Pointers terminology (keep singular/plural clean without changing concept)
  text = text.replace(/\b(?:to|too)\s+pointers?\b/gi, 'two pointers');
  text = text.replace(/\btwo\s+pointer\b/gi, 'two pointers');
  text = text.replace(/\btwo\s+point\b/gi, 'two pointers');

  // 4. Hash Map / Hash Table terminology
  text = text.replace(/\b(?:cash|hush)\s*maps?\b/gi, 'hash map');
  text = text.replace(/\bhashmap\b/gi, 'hash map');
  text = text.replace(/\b(?:cash|hush)\s*tables?\b/gi, 'hash table');
  text = text.replace(/\bhashtable\b/gi, 'hash table');
  text = text.replace(/\bhash\s*sets?\b/gi, 'hash set');
  text = text.replace(/\bhashset\b/gi, 'hash set');

  // 5. Complement in arithmetic/sum context
  text = text.replace(/\bcompliments?\b/gi, 'complement');

  // 6. Time and Space Complexity notation
  // O(n^2) / O(n squared)
  text = text.replace(/\b(?:big\s*)?(?:oh|o|order)\s+of\s+n\s*(?:squared|square|\^2|2)\b/gi, 'O(n²)');
  text = text.replace(/\b(?:big\s*)?o\s*\(\s*n\s*(?:squared|square|\^2|2)\s*\)/gi, 'O(n²)');
  text = text.replace(/\boh\s*of\s*n\s*square\b/gi, 'O(n²)');
  text = text.replace(/\boh\s*of\s*n\s*squared\b/gi, 'O(n²)');

  // O(n log n)
  text = text.replace(/\b(?:big\s*)?(?:oh|o|order)\s+of\s+n\s*log\s*n\b/gi, 'O(n log n)');
  text = text.replace(/\b(?:big\s*)?o\s*\(\s*n\s*log\s*n\s*\)/gi, 'O(n log n)');

  // O(log n)
  text = text.replace(/\b(?:big\s*)?(?:oh|o|order)\s+of\s+log\s*n\b/gi, 'O(log n)');
  text = text.replace(/\b(?:big\s*)?o\s*\(\s*log\s*n\s*\)/gi, 'O(log n)');

  // O(n)
  text = text.replace(/\b(?:big\s*)?(?:oh|o|order)\s+of\s+n\b/gi, 'O(n)');
  text = text.replace(/\b(?:big\s*)?o\s*\(\s*n\s*\)/gi, 'O(n)');

  // O(1)
  text = text.replace(/\b(?:big\s*)?(?:oh|o|order)\s+of\s+(?:one|1)\b/gi, 'O(1)');
  text = text.replace(/\b(?:big\s*)?o\s*\(\s*1\s*\)/gi, 'O(1)');

  // Complexity terms
  text = text.replace(/\btime\s+complexly\b/gi, 'time complexity');
  text = text.replace(/\bspace\s+complexly\b/gi, 'space complexity');
  text = text.replace(/\bauxiliary\s+space\b/gi, 'auxiliary space');

  // 7. Other common DSA acoustic errors
  text = text.replace(/\bbinary\s+surge\b/gi, 'binary search');
  text = text.replace(/\b(?:link|lynx)\s+list\b/gi, 'linked list');
  text = text.replace(/\bcall\s+stuck\b/gi, 'call stack');
  text = text.replace(/\bkey\s*values?\b/gi, 'key-value');

  // 8. Clean up extra spaces
  text = text.replace(/\s{2,}/g, ' ').trim();

  return text;
};

export const isSpeechRecognitionSupported = (): boolean => {
  if (typeof window === 'undefined') return false;
  return Boolean(
    (window as unknown as { SpeechRecognition?: unknown }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: unknown }).webkitSpeechRecognition
  );
};

export interface SpeechTranscriptResult {
  final: string;
  interim: string;
  full: string;
}

export interface SpeechRecognizerController {
  start: () => void;
  stop: () => void;
  abort: () => void;
}

export const createSpeechRecognizer = (
  onTranscript: (result: SpeechTranscriptResult) => void,
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
  recognition.maxAlternatives = 1;

  recognition.onresult = (event: any) => {
    let sessionFinal = '';
    let sessionInterim = '';

    for (let i = 0; i < event.results.length; i++) {
      const result = event.results[i];
      const text = result[0]?.transcript || '';
      if (result.isFinal) {
        sessionFinal += (sessionFinal ? ' ' : '') + text.trim();
      } else {
        sessionInterim += (sessionInterim ? ' ' : '') + text.trim();
      }
    }

    const normFinal = normalizeDsaSpeech(sessionFinal);
    const normInterim = normalizeDsaSpeech(sessionInterim);

    onTranscript({
      final: normFinal,
      interim: normInterim,
      full: [normFinal, normInterim].filter(Boolean).join(' ').trim(),
    });
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
