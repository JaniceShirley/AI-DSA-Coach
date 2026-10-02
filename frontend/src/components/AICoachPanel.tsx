import React, { useState, useEffect } from 'react';
import { coachingService } from '../services/coachingService';
import type { CoachingInteraction, AIFeedbackData } from '../types';
import {
  Sparkles,
  HelpCircle,
  BrainCircuit,
  Compass,
  CheckCircle,
  AlertCircle,
  Loader2,
  Send,
  MessageSquare,
  ChevronRight,
  ShieldCheck,
  Zap,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { speak, stopSpeaking } from '../utils/speech';

interface AICoachPanelProps {
  problemId: number;
  studentCode: string;
  latestSubmissionId?: number;
}

export const AICoachPanel: React.FC<AICoachPanelProps> = ({
  problemId,
  studentCode,
  latestSubmissionId
}) => {
  const [activeMode, setActiveMode] = useState<'hint' | 'challenge' | 'alternative' | 'feedback'>('hint');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [speakingText, setSpeakingText] = useState<string | null>(null);

  const handleSpeak = (text: string) => {
    if (speakingText === text) {
      stopSpeaking();
      setSpeakingText(null);
      return;
    }
    speak(
      text,
      () => setSpeakingText(text),
      () => setSpeakingText(null),
      () => setSpeakingText(null)
    );
  };

  useEffect(() => {
    return () => {
      stopSpeaking();
    };
  }, []);

  // Hints state
  const [hintText, setHintText] = useState<string | null>(null);
  const [currentHintLevel, setCurrentHintLevel] = useState<number>(0);
  const [hintsUsed, setHintsUsed] = useState<number>(0);

  // Challenge state
  const [challengeText, setChallengeText] = useState<string | null>(null);
  const [userAnswer, setUserAnswer] = useState<string>('');

  // Alternative Approach state
  const [alternativeText, setAlternativeText] = useState<string | null>(null);

  // Feedback state
  const [feedbackData, setFeedbackData] = useState<AIFeedbackData | null>(null);

  // History state
  const [history, setHistory] = useState<CoachingInteraction[]>([]);
  const [showHistory, setShowHistory] = useState<boolean>(false);

  useEffect(() => {
    // Load existing history on component mount / problem change
    loadHistory();
  }, [problemId]);

  const loadHistory = async () => {
    try {
      const data = await coachingService.getCoachingHistory(problemId);
      setHistory(data);
      // Find latest hint level if present
      const latestHint = data.find((h) => h.interaction_type === 'hint' && h.hint_level);
      if (latestHint && latestHint.hint_level) {
        setCurrentHintLevel(latestHint.hint_level);
      }
    } catch {
      // Silent error fallback for history loading
    }
  };

  const handleRequestHint = async (requestedLevel?: number) => {
    try {
      setLoading(true);
      setError(null);
      setActiveMode('hint');

      const targetLevel = requestedLevel || (currentHintLevel < 4 ? currentHintLevel + 1 : 4);
      const res = await coachingService.getHint(
        problemId,
        studentCode,
        latestSubmissionId,
        targetLevel
      );

      setHintText(res.hint);
      setCurrentHintLevel(res.hint_level);
      setHintsUsed(res.hints_used);
      await loadHistory();
    } catch (err: unknown) {
      console.error('Failed to get AI hint:', err);
      setError('AI Coach is temporarily unavailable. You can continue solving and submit your code normally.');
    } finally {
      setLoading(false);
    }
  };

  const handleChallenge = async (customAnswer?: string) => {
    try {
      setLoading(true);
      setError(null);
      setActiveMode('challenge');

      const answerToSubmit = customAnswer !== undefined ? customAnswer : userAnswer;
      const res = await coachingService.challengeUnderstanding(problemId, studentCode, answerToSubmit);

      setChallengeText(res.challenge);
      setUserAnswer('');
      await loadHistory();
    } catch (err: unknown) {
      console.error('Failed to get challenge:', err);
      setError('AI Coach is temporarily unavailable. You can continue solving and submit your code normally.');
    } finally {
      setLoading(false);
    }
  };

  const handleAlternative = async () => {
    try {
      setLoading(true);
      setError(null);
      setActiveMode('alternative');

      const res = await coachingService.getAlternativeApproach(problemId, studentCode);
      setAlternativeText(res.alternative_approach);
      await loadHistory();
    } catch (err: unknown) {
      console.error('Failed to get alternative approach:', err);
      setError('AI Coach is temporarily unavailable. You can continue solving and submit your code normally.');
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async () => {
    try {
      setLoading(true);
      setError(null);
      setActiveMode('feedback');

      const res = await coachingService.getFeedback(problemId, studentCode, latestSubmissionId);
      setFeedbackData(res.feedback);
      await loadHistory();
    } catch (err: unknown) {
      console.error('Failed to get feedback:', err);
      setError('AI Coach is temporarily unavailable. You can continue solving and submit your code normally.');
    } finally {
      setLoading(false);
    }
  };

  const getHintLevelBadge = (level: number) => {
    switch (level) {
      case 1:
        return { label: 'Level 1: Conceptual', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' };
      case 2:
        return { label: 'Level 2: Directional', color: 'bg-blue-500/20 text-blue-300 border-blue-500/40' };
      case 3:
        return { label: 'Level 3: Strategic', color: 'bg-amber-500/20 text-amber-300 border-amber-500/40' };
      case 4:
        return { label: 'Level 4: Detailed Guidance', color: 'bg-rose-500/20 text-rose-300 border-rose-500/40' };
      default:
        return { label: 'Hint Level', color: 'bg-slate-800 text-slate-300 border-slate-700' };
    }
  };

  return (
    <div className="bg-slate-900 border border-indigo-500/30 rounded-xl overflow-hidden shadow-xl transition-all">
      {/* Header */}
      <div className="bg-slate-950 border-b border-slate-800 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-indigo-600/20 border border-indigo-500/40 rounded-lg text-indigo-400">
            <Sparkles className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
              <span>AI DSA Coach</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">
                Guided Learning
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono flex items-center space-x-1" title="Model: Qwen2.5-Coder-0.5B + dsa-coach-lora-v1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                <span>QLoRA Active</span>
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Personalized progressive hints & code-aware analysis without solution leakage.
            </p>
          </div>
        </div>

        {/* Top Control Bar */}
        <div className="flex items-center space-x-2 text-xs">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="px-3 py-1.5 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg text-slate-300 font-medium transition-colors flex items-center space-x-1.5"
          >
            <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
            <span>History ({history.length})</span>
          </button>
        </div>
      </div>

      {/* Main Action Buttons Grid */}
      <div className="p-4 bg-slate-900/60 border-b border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <button
          onClick={() => handleRequestHint()}
          disabled={loading}
          className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${
            activeMode === 'hint'
              ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/20'
              : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-indigo-500/50 hover:bg-slate-900'
          }`}
        >
          <HelpCircle className="w-4 h-4 text-emerald-400" />
          <span>I'm Stuck</span>
        </button>

        <button
          onClick={() => handleChallenge()}
          disabled={loading}
          className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${
            activeMode === 'challenge'
              ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/20'
              : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-indigo-500/50 hover:bg-slate-900'
          }`}
        >
          <BrainCircuit className="w-4 h-4 text-amber-400" />
          <span>Challenge Me</span>
        </button>

        <button
          onClick={() => handleAlternative()}
          disabled={loading}
          className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${
            activeMode === 'alternative'
              ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/20'
              : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-indigo-500/50 hover:bg-slate-900'
          }`}
        >
          <Compass className="w-4 h-4 text-blue-400" />
          <span>Alternative Approach</span>
        </button>

        <button
          onClick={() => handleFeedback()}
          disabled={loading}
          className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${
            activeMode === 'feedback'
              ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/20'
              : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-indigo-500/50 hover:bg-slate-900'
          }`}
        >
          <Zap className="w-4 h-4 text-purple-400" />
          <span>AI Feedback</span>
        </button>
      </div>

      {/* Main Content Area */}
      <div className="p-5 space-y-4">
        {loading && (
          <div className="py-8 flex flex-col items-center justify-center space-y-3 text-indigo-400">
            <Loader2 className="w-7 h-7 animate-spin" />
            <p className="text-xs text-slate-400 font-medium">
              AI Coach is analyzing code & problem context...
            </p>
          </div>
        )}

        {error && !loading && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-xs flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-200">Coach Warning</p>
              <p className="mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* HISTORY PANEL DRAWER */}
        {showHistory && (
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider border-b border-slate-800 pb-2">
              Coaching Interaction Session History
            </h4>
            {history.length === 0 ? (
              <p className="text-xs text-slate-500">No interaction history for this problem yet.</p>
            ) : (
              <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                {history.map((item) => (
                  <div key={item.id} className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs space-y-1.5">
                    <div className="flex items-center justify-between text-slate-400 text-[11px]">
                      <span className="font-bold text-indigo-400 uppercase tracking-wider">{item.interaction_type}</span>
                      <span>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    {item.user_question && (
                      <p className="text-slate-400 italic">User: "{item.user_question}"</p>
                    )}
                    <p className="text-slate-200 whitespace-pre-line font-sans">{item.ai_response}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* HINT MODE DISPLAY */}
        {!loading && !error && activeMode === 'hint' && (
          <div className="space-y-4">
            {hintText ? (
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4 shadow-inner">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <span className={`text-xs px-3 py-1 rounded-full font-bold border ${getHintLevelBadge(currentHintLevel).color}`}>
                    {getHintLevelBadge(currentHintLevel).label}
                  </span>
                  <div className="flex items-center space-x-2.5">
                    <button
                      type="button"
                      onClick={() => handleSpeak(hintText)}
                      className="px-2 py-0.5 rounded text-[11px] font-semibold flex items-center space-x-1 bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/30 transition-colors"
                      title="Listen to hint spoken aloud"
                    >
                      {speakingText === hintText ? (
                        <>
                          <VolumeX className="w-3.5 h-3.5 text-rose-400" />
                          <span>Stop</span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-3.5 h-3.5" />
                          <span>Listen</span>
                        </>
                      )}
                    </button>
                    <span className="text-xs text-slate-400 font-mono">
                      Total Hints Used: {hintsUsed}
                    </span>
                  </div>
                </div>

                <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-line font-sans">
                  {hintText}
                </div>

                {/* Level Navigation / Next Hint Controls */}
                <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800/80">
                  <button
                    onClick={() => handleRequestHint(currentHintLevel)}
                    className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors"
                  >
                    Try Again
                  </button>

                  {currentHintLevel < 4 && (
                    <button
                      onClick={() => handleRequestHint(currentHintLevel + 1)}
                      className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-sm"
                    >
                      <span>Need Another Hint (Level {currentHintLevel + 1})</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-6 bg-slate-950/60 border border-dashed border-slate-800 rounded-xl text-center space-y-3">
                <ShieldCheck className="w-8 h-8 text-indigo-400 mx-auto opacity-80" />
                <h4 className="text-sm font-semibold text-white">Ready when you are!</h4>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  Click <strong className="text-indigo-300">"I'm Stuck"</strong> anytime to get conceptual guidance without revealing complete code solutions.
                </p>
              </div>
            )}
          </div>
        )}

        {/* CHALLENGE MODE DISPLAY */}
        {!loading && !error && activeMode === 'challenge' && (
          <div className="space-y-4">
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4 shadow-inner">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2 text-amber-400">
                  <BrainCircuit className="w-5 h-5" />
                  <h4 className="text-sm font-bold text-white">Challenge Your Understanding</h4>
                </div>
                {challengeText && (
                  <button
                    type="button"
                    onClick={() => handleSpeak(challengeText)}
                    className="px-2 py-0.5 rounded text-[11px] font-semibold flex items-center space-x-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/30 transition-colors"
                    title="Listen to challenge question"
                  >
                    {speakingText === challengeText ? (
                      <>
                        <VolumeX className="w-3.5 h-3.5 text-rose-400" />
                        <span>Stop</span>
                      </>
                    ) : (
                      <>
                        <Volume2 className="w-3.5 h-3.5" />
                        <span>Listen</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {challengeText ? (
                <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-line font-sans">
                  {challengeText}
                </div>
              ) : (
                <p className="text-xs text-slate-400">
                  Click the button below to generate conceptual edge-case questions for your code!
                </p>
              )}

              {/* Interactive Student Answer Input Box */}
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <label className="text-xs font-semibold text-slate-400 block">
                  Reply to AI Coach (Explain your reasoning or complexity):
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && userAnswer.trim()) {
                        handleChallenge(userAnswer);
                      }
                    }}
                    placeholder="e.g. 'My algorithm runs in O(N) time because hash map lookups take O(1)...'"
                    className="flex-grow bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    onClick={() => handleChallenge(userAnswer)}
                    disabled={!userAnswer.trim()}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center space-x-1 transition-colors"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Submit</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ALTERNATIVE APPROACH MODE DISPLAY */}
        {!loading && !error && activeMode === 'alternative' && (
          <div className="space-y-4">
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4 shadow-inner">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2 text-blue-400">
                  <Compass className="w-5 h-5" />
                  <h4 className="text-sm font-bold text-white">Explore Alternative Approaches</h4>
                </div>
                {alternativeText && (
                  <button
                    type="button"
                    onClick={() => handleSpeak(alternativeText)}
                    className="px-2 py-0.5 rounded text-[11px] font-semibold flex items-center space-x-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-200 border border-blue-500/30 transition-colors"
                    title="Listen to alternative approach"
                  >
                    {speakingText === alternativeText ? (
                      <>
                        <VolumeX className="w-3.5 h-3.5 text-rose-400" />
                        <span>Stop</span>
                      </>
                    ) : (
                      <>
                        <Volume2 className="w-3.5 h-3.5" />
                        <span>Listen</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {alternativeText ? (
                <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-line font-sans">
                  {alternativeText}
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-xs text-slate-400 mb-3">
                    Discover different algorithmic strategies (e.g. Hash Table vs Two Pointers).
                  </p>
                  <button
                    onClick={() => handleAlternative()}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold inline-flex items-center space-x-2"
                  >
                    <Compass className="w-4 h-4" />
                    <span>Generate Alternative Strategies</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* AI FEEDBACK MODE DISPLAY */}
        {!loading && !error && activeMode === 'feedback' && (
          <div className="space-y-4">
            {feedbackData ? (
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4 shadow-inner">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center space-x-2 text-purple-400">
                    <Zap className="w-5 h-5" />
                    <h4 className="text-sm font-bold text-white">AI Solution Feedback</h4>
                  </div>
                  <span className="text-xs px-2.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30">
                    Structured Review
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-1">
                    <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] block">Approach</span>
                    <p className="text-slate-200">{feedbackData.approach}</p>
                  </div>

                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-1">
                    <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] block">Correctness</span>
                    <p className="text-slate-200">{feedbackData.correctness}</p>
                  </div>

                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-1">
                    <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] block">Time Complexity</span>
                    <p className="text-emerald-400 font-mono font-semibold">{feedbackData.time_complexity}</p>
                  </div>

                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-1">
                    <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] block">Space Complexity</span>
                    <p className="text-blue-400 font-mono font-semibold">{feedbackData.space_complexity}</p>
                  </div>

                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-1 sm:col-span-2">
                    <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] block">Edge Cases & Testing</span>
                    <p className="text-slate-200">{feedbackData.edge_cases}</p>
                  </div>

                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-1 sm:col-span-2">
                    <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] block">Possible Optimizations</span>
                    <p className="text-slate-200">{feedbackData.optimization}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 bg-slate-950/60 border border-slate-800 rounded-xl text-center space-y-3">
                <CheckCircle className="w-8 h-8 text-purple-400 mx-auto opacity-80" />
                <h4 className="text-sm font-semibold text-white">Code Review & Feedback</h4>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  Click <strong className="text-indigo-300">"AI Feedback"</strong> after writing or submitting your code to get structured evaluation of time/space complexity and optimization options.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
