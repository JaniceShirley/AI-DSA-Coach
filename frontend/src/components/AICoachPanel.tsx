import React, { useState, useEffect, useRef } from 'react';
import { coachingService } from '../services/coachingService';
import type {
  ChatMessage,
  LearningStage,
  CoachingSessionState
} from '../types';
import {
  Sparkles,
  Send,
  Loader2,
  RotateCcw,
  Volume2,
  VolumeX,
  AlertCircle,
  CheckCircle2,
  Bot,
  User,
  Layers,
  ChevronDown,
  ChevronUp,
  Code2,
  Lightbulb,
  Scale
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
  // Session & Chat State
  const [session, setSession] = useState<CoachingSessionState | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [speakingText, setSpeakingText] = useState<string | null>(null);

  // Secondary Tools drawer
  const [showSecondaryTools, setShowSecondaryTools] = useState<boolean>(false);
  const [showApproachesDrawer, setShowApproachesDrawer] = useState<boolean>(false);
  const [hintLevel, setHintLevel] = useState<number>(0);

  // Auto-scroll ref
  const chatEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Load session on mount / problem change
  useEffect(() => {
    loadSession();
    return () => {
      stopSpeaking();
    };
  }, [problemId]);

  // Scroll on message updates
  useEffect(() => {
    scrollToBottom(false);
  }, [messages, loading]);

  const scrollToBottom = (smooth = true) => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
    }
  };

  const loadSession = async () => {
    try {
      setLoading(true);
      setError(null);
      const state = await coachingService.getSessionState(problemId);
      setSession(state);
      setMessages(state.messages || []);
    } catch (err) {
      console.error('Failed to load coaching session:', err);
      // Fallback empty state
      setSession({
        session_id: 0,
        problem_id: problemId,
        stage: 'APPROACH_DISCOVERY',
        current_approach: {},
        explored_approaches: [],
        solution_status: 'IN_PROGRESS',
        complexity_state: {},
        hints_provided: [],
        misconceptions: [],
        messages: [],
        updated_at: new Date().toISOString()
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResetSession = async () => {
    if (!window.confirm('Reset your mentoring session for this problem? Your conversation history will start fresh.')) {
      return;
    }
    try {
      setLoading(true);
      stopSpeaking();
      const resetState = await coachingService.resetSession(problemId);
      setSession(resetState);
      setMessages([]);
      setError(null);
    } catch (err) {
      console.error('Reset failed:', err);
      setError('Could not reset session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (customText?: string, runCode = false) => {
    const textToSend = (customText !== undefined ? customText : inputMessage).trim();
    if (!textToSend || loading) return;

    setInputMessage('');
    setError(null);

    // Optimistically append user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: textToSend,
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      setLoading(true);
      const res = await coachingService.sendChatMessage(
        problemId,
        textToSend,
        studentCode,
        runCode
      );

      // Append AI response
      const aiMsg: ChatMessage = {
        id: `ai-${res.interaction_id || Date.now()}`,
        role: 'assistant',
        content: res.message,
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, aiMsg]);

      // Update session state
      setSession((prev) => ({
        ...(prev || {
          session_id: res.session_id,
          problem_id: problemId,
          messages: [],
          updated_at: new Date().toISOString()
        }),
        stage: res.stage,
        current_approach: res.current_approach,
        explored_approaches: res.explored_approaches,
        solution_status: res.solution_status,
        complexity_state: res.complexity_state,
        hints_provided: prev?.hints_provided || [],
        misconceptions: prev?.misconceptions || [],
        messages: [...(prev?.messages || []), tempUserMsg, aiMsg],
        last_student_code: studentCode,
        last_execution_result: res.execution_result
      }));
    } catch (err: unknown) {
      console.error('Failed to send message:', err);
      setError('Unable to reach your AI Mentor. Check your connection or try again.');
      // Remove optimistic message on failure
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

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

  // Secondary Tools: Request Progressive Hint
  const handleRequestHint = async () => {
    try {
      setLoading(true);
      const nextLevel = hintLevel < 4 ? hintLevel + 1 : 4;
      const res = await coachingService.getHint(problemId, studentCode, latestSubmissionId, nextLevel);
      setHintLevel(res.hint_level);

      const aiMsg: ChatMessage = {
        id: `hint-${Date.now()}`,
        role: 'assistant',
        content: `💡 **Level ${res.hint_level} Clue:**\n\n${res.hint}`,
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error('Failed to get hint:', err);
      setError('Could not retrieve hint at this moment.');
    } finally {
      setLoading(false);
    }
  };

  // Secondary Tools: Request Post-Submission Feedback
  const handleRequestFeedback = async () => {
    try {
      setLoading(true);
      const res = await coachingService.getFeedback(problemId, studentCode, latestSubmissionId);

      const summary = `📊 **Post-Submission Code Review:**\n\n- **Approach:** ${res.feedback.approach}\n- **Correctness:** ${res.feedback.correctness}\n- **Time Complexity:** ${res.feedback.time_complexity}\n- **Space Complexity:** ${res.feedback.space_complexity}\n- **Edge Cases:** ${res.feedback.edge_cases}\n- **Next Step:** ${res.feedback.optimization}`;
      const aiMsg: ChatMessage = {
        id: `feedback-${Date.now()}`,
        role: 'assistant',
        content: summary,
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error('Failed to get feedback:', err);
      setError('Could not retrieve code review at this moment.');
    } finally {
      setLoading(false);
    }
  };

  // Stage formatting helper
  const getStageBadge = (stage?: LearningStage) => {
    switch (stage) {
      case 'UNDERSTANDING_PROBLEM':
        return { label: 'Clarifying Problem', color: 'bg-sky-500/10 text-sky-400 border-sky-500/20' };
      case 'APPROACH_DISCOVERY':
        return { label: 'Exploring Approach', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' };
      case 'GUIDED_IMPLEMENTATION':
        return { label: 'Guided Coding', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' };
      case 'DEBUGGING':
        return { label: 'Debugging Code', color: 'bg-rose-500/10 text-rose-400 border-rose-500/20' };
      case 'CORRECTNESS_VERIFICATION':
        return { label: 'Verifying Tests', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' };
      case 'COMPLEXITY_ANALYSIS':
        return { label: 'Complexity Analysis', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' };
      case 'OPTIMIZATION_DISCOVERY':
        return { label: 'Discovering Optimization', color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' };
      case 'OPTIMIZED_IMPLEMENTATION':
        return { label: 'Implementing Optimized Solution', color: 'bg-teal-500/10 text-teal-400 border-teal-500/20' };
      case 'APPROACH_COMPARISON':
        return { label: 'Comparing Approaches', color: 'bg-fuchsia-500/10 text-fuchsia-400 border-fuchsia-500/20' };
      case 'COMPLETED':
        return { label: 'Mastered & Solved', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' };
      default:
        return { label: 'Mentoring', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' };
    }
  };

  // Helper to render markdown text with bold, inline code, blocks, and tables
  const renderFormattedContent = (content: string) => {
    const lines = content.split('\n');
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeBuffer: string[] = [];
    let tableBuffer: string[] = [];
    let inTable = false;

    const flushTable = () => {
      if (tableBuffer.length === 0) return;
      const rows = tableBuffer.map((r) =>
        r
          .split('|')
          .slice(1, -1)
          .map((c) => c.trim())
      );
      if (rows.length >= 2) {
        const header = rows[0];
        const bodyRows = rows.slice(2); // Skip separator row
        elements.push(
          <div key={`table-${elements.length}`} className="overflow-x-auto my-3">
            <table className="min-w-full text-xs text-left border border-slate-700/60 rounded-lg overflow-hidden bg-slate-950/40">
              <thead className="bg-slate-800/80 text-slate-200">
                <tr>
                  {header.map((th, i) => (
                    <th key={i} className="px-3 py-2 font-semibold border-b border-slate-700/60">
                      {th.replace(/\*\*/g, '')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {bodyRows.map((tr, rIdx) => (
                  <tr key={rIdx} className="hover:bg-slate-800/30">
                    {tr.map((td, cIdx) => (
                      <td key={cIdx} className="px-3 py-2 text-slate-300">
                        {renderInlineFormatting(td)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }
      tableBuffer = [];
      inTable = false;
    };

    lines.forEach((line, idx) => {
      // Code block start / end
      if (line.trim().startsWith('```')) {
        if (inCodeBlock) {
          elements.push(
            <pre
              key={`code-${idx}`}
              className="p-3 my-2 bg-slate-950 border border-slate-800 rounded-lg text-emerald-300 font-mono text-xs overflow-x-auto whitespace-pre-wrap"
            >
              {codeBuffer.join('\n')}
            </pre>
          );
          codeBuffer = [];
          inCodeBlock = false;
        } else {
          flushTable();
          inCodeBlock = true;
        }
        return;
      }

      if (inCodeBlock) {
        codeBuffer.push(line);
        return;
      }

      // Markdown table line
      if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
        inTable = true;
        tableBuffer.push(line.trim());
        return;
      } else if (inTable) {
        flushTable();
      }

      // Blockquote / Callout
      if (line.trim().startsWith('>')) {
        elements.push(
          <blockquote
            key={`quote-${idx}`}
            className="border-l-2 border-indigo-500 pl-3 py-1 my-2 text-slate-300 bg-indigo-950/20 rounded-r text-xs italic"
          >
            {renderInlineFormatting(line.replace(/^>\s*/, ''))}
          </blockquote>
        );
        return;
      }

      // Headers
      if (line.trim().startsWith('###')) {
        elements.push(
          <h4 key={`h3-${idx}`} className="text-sm font-bold text-white mt-3 mb-1">
            {line.replace(/^###\s*/, '')}
          </h4>
        );
        return;
      }
      if (line.trim().startsWith('##')) {
        elements.push(
          <h3 key={`h2-${idx}`} className="text-base font-bold text-white mt-3 mb-1">
            {line.replace(/^##\s*/, '')}
          </h3>
        );
        return;
      }

      // Bullet lists
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        elements.push(
          <li key={`li-${idx}`} className="ml-4 list-disc text-slate-300 text-xs my-0.5">
            {renderInlineFormatting(line.replace(/^[-*]\s+/, ''))}
          </li>
        );
        return;
      }

      // Empty line
      if (!line.trim()) {
        elements.push(<div key={`sp-${idx}`} className="h-1.5" />);
        return;
      }

      // Regular paragraph
      elements.push(
        <p key={`p-${idx}`} className="text-xs text-slate-200 leading-relaxed">
          {renderInlineFormatting(line)}
        </p>
      );
    });

    if (inTable) flushTable();

    return elements;
  };

  const renderInlineFormatting = (text: string): React.ReactNode => {
    // Quick regex inline parser for bold and backticks
    const parts: React.ReactNode[] = [];
    const tokens = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);

    tokens.forEach((token, idx) => {
      if (token.startsWith('`') && token.endsWith('`')) {
        parts.push(
          <code
            key={idx}
            className="px-1.5 py-0.5 bg-slate-800 text-indigo-300 rounded font-mono text-[11px] border border-slate-700/60"
          >
            {token.slice(1, -1)}
          </code>
        );
      } else if (token.startsWith('**') && token.endsWith('**')) {
        parts.push(
          <strong key={idx} className="font-bold text-white">
            {token.slice(2, -2)}
          </strong>
        );
      } else {
        parts.push(token);
      }
    });

    return parts;
  };

  const stageBadge = getStageBadge(session?.stage);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col shadow-lg shadow-black/20">
      {/* HEADER */}
      <div className="p-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-white tracking-wide">AI DSA Mentor</h3>
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${stageBadge.color}`}>
                {stageBadge.label}
              </span>
            </div>
            {session?.current_approach?.name && (
              <p className="text-[11px] text-slate-400 flex items-center space-x-1 mt-0.5">
                <span className="text-slate-500">Current Approach:</span>
                <span className="text-indigo-300 font-medium">{session.current_approach.name}</span>
              </p>
            )}
          </div>
        </div>

        {/* Top Header Actions */}
        <div className="flex items-center space-x-1.5">
          {session?.explored_approaches && session.explored_approaches.length > 0 && (
            <button
              onClick={() => setShowApproachesDrawer(!showApproachesDrawer)}
              className="px-2.5 py-1 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs rounded-lg flex items-center space-x-1 border border-slate-700/60 transition-colors"
              title="View Explored Approaches"
            >
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden sm:inline">Approaches ({session.explored_approaches.length})</span>
            </button>
          )}

          <button
            onClick={() => setShowSecondaryTools(!showSecondaryTools)}
            className="px-2 py-1 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs rounded-lg flex items-center space-x-1 border border-slate-700/60 transition-colors"
            title="Secondary Tools (Hints & Feedback)"
          >
            <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
            <span className="hidden sm:inline">Tools</span>
            {showSecondaryTools ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          <button
            onClick={handleResetSession}
            disabled={loading}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            title="Reset Mentoring Session"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* EXPLORED APPROACHES DRAWER */}
      {showApproachesDrawer && session?.explored_approaches && (
        <div className="p-3 bg-slate-950 border-b border-slate-800 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-300 flex items-center space-x-1.5">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              <span>Explored Approaches</span>
            </span>
            <button
              onClick={() => handleSendMessage('Can we compare the approaches explored so far?')}
              className="text-indigo-400 hover:text-indigo-300 text-[11px] underline flex items-center space-x-1"
            >
              <Scale className="w-3 h-3" />
              <span>Compare Trade-offs</span>
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {session.explored_approaches.map((app, i) => (
              <div key={i} className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">{app.name}</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded font-medium ${
                      app.status === 'VERIFIED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {app.status || 'Explored'}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 font-mono space-x-2">
                  <span>Time: {app.time_complexity || 'O(?)'}</span>
                  <span>Space: {app.space_complexity || 'O(?)'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SECONDARY TOOLS DRAWER */}
      {showSecondaryTools && (
        <div className="p-3 bg-slate-950 border-b border-slate-800 flex flex-wrap gap-2 text-xs">
          <button
            onClick={handleRequestHint}
            disabled={loading}
            className="px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 rounded-lg flex items-center space-x-1.5 transition-colors"
          >
            <Lightbulb className="w-3.5 h-3.5" />
            <span>Progressive Clue (Level {hintLevel < 4 ? hintLevel + 1 : 4})</span>
          </button>

          <button
            onClick={handleRequestFeedback}
            disabled={loading || !latestSubmissionId}
            className="px-3 py-1.5 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 rounded-lg flex items-center space-x-1.5 transition-colors disabled:opacity-40"
            title={latestSubmissionId ? 'Review latest submission' : 'Submit code first to review'}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Post-Submit Feedback</span>
          </button>
        </div>
      )}

      {/* CHAT MESSAGES CONTAINER */}
      <div
        ref={chatContainerRef}
        className="flex-1 p-4 overflow-y-auto space-y-3.5 min-h-[300px] max-h-[460px] bg-slate-900/50"
      >
        {/* Empty state welcome */}
        {messages.length === 0 && (
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-3 text-center">
            <div className="w-10 h-10 rounded-full bg-indigo-600/20 text-indigo-400 flex items-center justify-center mx-auto">
              <Bot className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-white">Welcome! I'm your AI DSA Mentor.</h4>
              <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
                I'm here to help you reason through this problem using <strong>your own ideas</strong>. Even a simple brute-force idea is a great place to start!
              </p>
            </div>

            {/* Quick Starters */}
            <div className="pt-2 flex flex-wrap justify-center gap-2">
              {[
                "I think I can use brute force.",
                "Can I use a hash set or dictionary?",
                "Can I solve this with sorting?",
                "I don't understand the problem."
              ].map((starter, i) => (
                <button
                  key={i}
                  onClick={() => handleSendMessage(starter)}
                  disabled={loading}
                  className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700/70 text-slate-300 hover:text-white rounded-lg text-xs transition-colors"
                >
                  {starter}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message Stream */}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start space-x-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex-shrink-0 flex items-center justify-center text-indigo-400 mt-1">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`relative max-w-[85%] rounded-2xl p-3.5 text-xs shadow-sm ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-sm'
                  : 'bg-slate-950 border border-slate-800/90 text-slate-200 rounded-bl-sm space-y-1.5'
              }`}
            >
              {msg.role === 'user' ? (
                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              ) : (
                <div className="space-y-1.5">
                  {renderFormattedContent(msg.content)}

                  {/* Speech button on AI response */}
                  <div className="pt-1.5 flex justify-end">
                    <button
                      onClick={() => handleSpeak(msg.content)}
                      className="text-slate-400 hover:text-white p-1 rounded transition-colors"
                      title={speakingText === msg.content ? 'Stop Audio' : 'Listen with Speech'}
                    >
                      {speakingText === msg.content ? (
                        <VolumeX className="w-3.5 h-3.5 text-amber-400" />
                      ) : (
                        <Volume2 className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-lg bg-slate-800 border border-slate-700 flex-shrink-0 flex items-center justify-center text-slate-300 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex items-start space-x-2.5">
            <div className="w-7 h-7 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex-shrink-0 flex items-center justify-center text-indigo-400 mt-1">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-2xl rounded-bl-sm p-3.5 text-xs flex items-center space-x-2 text-slate-400">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
              <span>Mentor is analyzing your reasoning...</span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* ERROR BANNER */}
      {error && (
        <div className="px-3 py-2 bg-rose-500/10 border-t border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-1.5">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-slate-400 hover:text-white ml-2">
            ✕
          </button>
        </div>
      )}

      {/* QUICK SUGGESTIONS BAR */}
      <div className="p-2 border-t border-slate-800/80 bg-slate-950/40 flex items-center space-x-1.5 overflow-x-auto text-[11px]">
        <button
          onClick={() => handleSendMessage('Can you review my code in the editor?', false)}
          disabled={loading || !studentCode.trim()}
          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 rounded-md whitespace-nowrap transition-colors flex items-center space-x-1"
        >
          <Code2 className="w-3 h-3 text-indigo-400" />
          <span>Review My Code</span>
        </button>

        <button
          onClick={() => handleSendMessage('Please check and verify my code against test cases.', true)}
          disabled={loading || !studentCode.trim()}
          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 rounded-md whitespace-nowrap transition-colors flex items-center space-x-1"
        >
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          <span>Verify Against Tests</span>
        </button>

        <button
          onClick={() => handleSendMessage('What is the time complexity of this approach?')}
          disabled={loading}
          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md whitespace-nowrap transition-colors"
        >
          Complexity?
        </button>

        <button
          onClick={() => handleSendMessage("I am stuck on this step, can you give me a small clue?")}
          disabled={loading}
          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-amber-300 rounded-md whitespace-nowrap transition-colors"
        >
          I'm Stuck
        </button>
      </div>

      {/* MESSAGE COMPOSER */}
      <div className="p-3 border-t border-slate-800 bg-slate-950">
        <div className="flex items-end space-x-2 bg-slate-900 border border-slate-800 focus-within:border-indigo-500 rounded-xl p-2 transition-colors">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your approach, question, or idea... (Enter to send, Shift+Enter for new line)"
            rows={2}
            className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none resize-none max-h-28 overflow-y-auto"
          />

          <button
            onClick={() => handleSendMessage()}
            disabled={loading || !inputMessage.trim()}
            className="p-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white rounded-lg transition-colors flex-shrink-0"
            title="Send Message (Enter)"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
};
