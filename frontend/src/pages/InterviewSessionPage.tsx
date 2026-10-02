import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { interviewService } from '../services/interviewService';
import { submissionService } from '../services/submissionService';
import type {
  InterviewSessionDetail,
  InterviewMessage,
  InterviewEvaluation,
  InterviewStage,
  RunCodeResponse,
  Difficulty
} from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { CodeEditor } from '../components/CodeEditor';
import { getDifficultyBadgeClass } from '../utils/difficultyColors';
import {
  speak,
  stopSpeaking,
  createSpeechRecognizer,
  type SpeechRecognizerController,
} from '../utils/speech';
import {
  Send,
  Code2,
  BrainCircuit,
  Award,
  CheckCircle2,
  Play,
  RotateCcw,
  Sparkles,
  ArrowRight,
  HelpCircle,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
} from 'lucide-react';

export const InterviewSessionPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<InterviewSessionDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [sending, setSending] = useState<boolean>(false);
  const [studentInput, setStudentInput] = useState<string>('');
  const [messages, setMessages] = useState<InterviewMessage[]>([]);
  const [evaluation, setEvaluation] = useState<InterviewEvaluation | null>(null);

  // Speech (Voice Mode & Speech-to-Text) State
  const [autoSpeak, setAutoSpeak] = useState<boolean>(true);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [speakingMsgId, setSpeakingMsgId] = useState<number | null>(null);
  const [isListening, setIsListening] = useState<boolean>(false);
  const recognizerRef = useRef<SpeechRecognizerController | null>(null);

  // Split View & Code Execution State
  const [showEditor, setShowEditor] = useState<boolean>(false);
  const [code, setCode] = useState<string>('');
  const [language, setLanguage] = useState<string>('python');
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [execResult, setExecResult] = useState<RunCodeResponse | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sessionId) {
      loadSessionData(Number(sessionId));
    }
    return () => {
      stopSpeaking();
      recognizerRef.current?.abort();
    };
  }, [sessionId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const loadSessionData = async (id: number) => {
    try {
      setLoading(true);
      const data = await interviewService.getInterviewById(id);
      setSession(data);
      setMessages(data.messages || []);
      if (data.evaluation) {
        setEvaluation(data.evaluation);
      }
      if (data.problem?.starter_code?.python) {
        setCode(data.problem.starter_code.python);
      }
      if (data.current_stage === 'CODING') {
        setShowEditor(true);
      }
    } catch (err) {
      console.error('Failed to load interview session:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSpeakMessage = (text: string, msgId: number) => {
    if (isSpeaking && speakingMsgId === msgId) {
      handleStopSpeaking();
      return;
    }

    speak(
      text,
      () => {
        setIsSpeaking(true);
        setSpeakingMsgId(msgId);
      },
      () => {
        setIsSpeaking(false);
        setSpeakingMsgId(null);
      },
      (err) => {
        console.warn('Speech synthesis error:', err);
        setIsSpeaking(false);
        setSpeakingMsgId(null);
      }
    );
  };

  const handleStopSpeaking = () => {
    stopSpeaking();
    setIsSpeaking(false);
    setSpeakingMsgId(null);
  };

  const toggleListening = () => {
    if (isListening) {
      recognizerRef.current?.stop();
      setIsListening(false);
      return;
    }

    // Stop interviewer voice playback if currently speaking
    handleStopSpeaking();

    const recognizer = createSpeechRecognizer(
      (transcript) => {
        setStudentInput(transcript);
      },
      () => {
        setIsListening(false);
      },
      (err) => {
        console.warn('Speech recognizer error:', err);
        setIsListening(false);
      }
    );

    if (recognizer) {
      recognizerRef.current = recognizer;
      recognizer.start();
      setIsListening(true);
    } else {
      alert('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
    }
  };

  const handleSendMessage = async () => {
    if (!studentInput.trim() || !session || sending) return;

    if (isListening) {
      recognizerRef.current?.stop();
      setIsListening(false);
    }
    handleStopSpeaking();

    const userText = studentInput.trim();
    setStudentInput('');
    setSending(true);

    // Optimistically add student message
    const tempUserMsg: InterviewMessage = {
      id: Date.now(),
      role: 'STUDENT',
      message: userText,
      stage: session.current_stage,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await interviewService.respond(session.id, userText);
      setSession((prev) => (prev ? { ...prev, current_stage: res.stage, status: res.status } : null));

      const aiMsg: InterviewMessage = {
        id: Date.now() + 1,
        role: 'AI_INTERVIEWER',
        message: res.message,
        stage: res.stage,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);

      if (autoSpeak) {
        handleSpeakMessage(res.message, aiMsg.id);
      }

      if (res.stage === 'CODING') {
        setShowEditor(true);
      }

      if (res.should_end) {
        const evalData = await interviewService.getFeedback(session.id);
        setEvaluation(evalData);
      }
    } catch (err) {
      console.error('Failed to send interview response:', err);
    } finally {
      setSending(false);
    }
  };

  const handleRunCode = async () => {
    if (!session) return;
    try {
      setIsExecuting(true);
      setExecResult(null);
      const res = await submissionService.runCode(session.problem.id, code, language);
      setExecResult(res);
    } catch {
      setExecResult({
        status: 'INTERNAL_ERROR',
        test_cases_passed: 0,
        total_test_cases: 0,
        runtime: 0,
        memory: 0,
        error_message: 'Execution error while contacting runner sandbox.',
        results: [],
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleSubmitCode = async () => {
    if (!session) return;
    try {
      setIsExecuting(true);
      setExecResult(null);
      const sub = await submissionService.submitCode(session.problem.id, code, language);

      setExecResult({
        status: sub.status,
        test_cases_passed: sub.test_cases_passed,
        total_test_cases: sub.total_test_cases,
        runtime: sub.runtime,
        memory: sub.memory,
        error_message: sub.error_message,
        results: [],
      });

      // Associate submission with interview session
      const codeTurn = await interviewService.associateCode(session.id, sub.id);
      const aiMsg: InterviewMessage = {
        id: Date.now() + 2,
        role: 'AI_INTERVIEWER',
        message: codeTurn.message,
        stage: 'CODING',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
      if (autoSpeak) {
        handleSpeakMessage(codeTurn.message, aiMsg.id);
      }
    } catch (err) {
      console.error('Submit code error:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleEndInterview = async () => {
    if (!session) return;
    try {
      setLoading(true);
      const evalData = await interviewService.endInterview(session.id);
      setEvaluation(evalData);
      setSession((prev) => (prev ? { ...prev, status: 'COMPLETED', current_stage: 'FINAL_EVALUATION' } : null));
    } catch (err) {
      console.error('Failed to end interview:', err);
    } finally {
      setLoading(false);
    }
  };

  const stages: { key: InterviewStage; label: string }[] = [
    { key: 'PROBLEM_INTRO', label: '1. Problem' },
    { key: 'APPROACH', label: '2. Approach' },
    { key: 'COMPLEXITY', label: '3. Complexity' },
    { key: 'EDGE_CASES', label: '4. Edge Cases' },
    { key: 'OPTIMIZATION', label: '5. Optimization' },
    { key: 'CODING', label: '6. Coding' },
    { key: 'FINAL_EVALUATION', label: '7. Report' },
  ];

  if (loading) {
    return <LoadingSpinner message="Preparing your technical interview room..." />;
  }

  if (!session) {
    return (
      <div className="p-8 bg-slate-900 border border-slate-800 rounded-xl text-center space-y-4">
        <h3 className="text-lg font-bold text-white">Interview Session Not Found</h3>
        <p className="text-slate-400 text-sm">The requested mock interview session does not exist or you do not have permission.</p>
        <Link to="/interview" className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold">
          <span>Back to Setup</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4 pb-10">
      {/* Top Header Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 border border-indigo-500/40 rounded-xl text-indigo-400">
            <BrainCircuit className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <h2 className="text-lg font-bold text-white tracking-tight">
                {session.problem.id}. {session.problem.title}
              </h2>
              <span className={`text-[11px] px-2.5 py-0.5 rounded font-bold ${getDifficultyBadgeClass(session.problem.difficulty)}`}>
                {session.problem.difficulty}
              </span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${session.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-indigo-500/20 text-indigo-300'}`}>
                {session.status}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Live Mock Technical Interview • Interactive Stage Progression
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowEditor(!showEditor)}
            className={`px-3.5 py-2 rounded-xl border text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              showEditor
                ? 'bg-indigo-600 text-white border-indigo-500 shadow-md'
                : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
            }`}
          >
            <Code2 className="w-4 h-4 text-emerald-400" />
            <span>{showEditor ? 'Hide Code Editor' : 'Open Code Editor'}</span>
          </button>

          {session.status !== 'COMPLETED' ? (
            <button
              onClick={handleEndInterview}
              className="px-4 py-2 bg-rose-600/20 hover:bg-rose-600 border border-rose-500/40 text-rose-300 hover:text-white rounded-xl text-xs font-semibold transition-all"
            >
              End Interview
            </button>
          ) : (
            <button
              onClick={() => navigate('/interview/history')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700"
            >
              All History
            </button>
          )}
        </div>
      </div>

      {/* Stage Progression Breadcrumb Bar */}
      <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[650px] gap-2">
          {stages.map((st) => {
            const isCurrent = session.current_stage === st.key;
            return (
              <div
                key={st.key}
                className={`flex-1 py-1.5 px-2.5 rounded-lg text-xs font-semibold text-center border transition-all ${
                  isCurrent
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-sm'
                    : 'bg-slate-900 text-slate-400 border-slate-800'
                }`}
              >
                {st.label}
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Two-Panel Layout */}
      <div className={`grid grid-cols-1 ${showEditor ? 'lg:grid-cols-12' : 'max-w-4xl mx-auto'} gap-6`}>
        {/* LEFT / CHAT PANEL: Technical Interview Dialogue */}
        <div className={`${showEditor ? 'lg:col-span-6' : 'w-full'} flex flex-col bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl min-h-[550px]`}>
          <div className="bg-slate-950 border-b border-slate-800 p-3.5 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              <span>Interview Dialogue</span>
            </div>

            <div className="flex items-center space-x-2">
              {isSpeaking && (
                <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs animate-pulse">
                  <Volume2 className="w-3.5 h-3.5 text-indigo-400" />
                  <span className="flex space-x-0.5">
                    <span className="w-1 h-2 bg-indigo-400 rounded-full animate-bounce" />
                    <span className="w-1 h-3.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.15s]" />
                    <span className="w-1 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.3s]" />
                  </span>
                  <span className="text-[11px] font-medium hidden sm:inline">Speaking</span>
                  <button
                    type="button"
                    onClick={handleStopSpeaking}
                    className="ml-1 text-slate-400 hover:text-white"
                    title="Stop audio playback"
                  >
                    <VolumeX className="w-3.5 h-3.5 text-rose-400" />
                  </button>
                </div>
              )}

              <button
                type="button"
                onClick={() => {
                  if (autoSpeak && isSpeaking) {
                    handleStopSpeaking();
                  }
                  setAutoSpeak(!autoSpeak);
                }}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all border ${
                  autoSpeak
                    ? 'bg-indigo-600/25 border-indigo-500/40 text-indigo-200 hover:bg-indigo-600/35'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
                title={autoSpeak ? "Voice mode enabled: Interviewer speaks questions aloud automatically" : "Voice mode muted: Click to enable speech"}
              >
                {autoSpeak ? <Volume2 className="w-3.5 h-3.5 text-indigo-400" /> : <VolumeX className="w-3.5 h-3.5 text-slate-500" />}
                <span>Voice: {autoSpeak ? 'ON' : 'OFF'}</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  const latestAI = [...messages].reverse().find((m) => m.role === 'AI_INTERVIEWER');
                  if (latestAI) handleSpeakMessage(latestAI.message, latestAI.id);
                }}
                className="px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-300 hover:text-white"
                title="Play current interviewer question aloud"
              >
                <Play className="w-3 h-3 fill-indigo-400 text-indigo-400" />
                <span>Play Question</span>
              </button>

              <span className="text-[11px] text-slate-400 font-mono bg-slate-900 px-2 py-1 rounded border border-slate-800">
                Stage: {session.current_stage}
              </span>
            </div>
          </div>

          {/* Messages Stream */}
          <div className="flex-grow p-4 space-y-4 max-h-[520px] overflow-y-auto">
            {messages.map((msg, index) => {
              const isAI = msg.role === 'AI_INTERVIEWER';
              return (
                <div
                  key={msg.id || index}
                  className={`flex items-start space-x-3 ${isAI ? 'justify-start' : 'justify-end'}`}
                >
                  {isAI && (
                    <div className="w-8 h-8 rounded-full bg-indigo-600/30 border border-indigo-500/50 flex items-center justify-center text-indigo-400 shrink-0 mt-1">
                      <BrainCircuit className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] p-4 rounded-2xl text-xs sm:text-sm leading-relaxed whitespace-pre-line shadow-sm ${
                      isAI
                        ? 'bg-slate-950 border border-indigo-500/30 text-slate-100'
                        : 'bg-indigo-600 text-white rounded-br-none'
                    }`}
                  >
                    <div className="flex items-center justify-between text-[10px] opacity-80 mb-1 border-b border-white/10 pb-1">
                      <span className="font-bold uppercase tracking-wider text-indigo-300">
                        {isAI ? 'Senior Interviewer' : 'You (Candidate)'}
                      </span>
                      {isAI && (
                        <button
                          type="button"
                          onClick={() => handleSpeakMessage(msg.message, msg.id || index)}
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center space-x-1 transition-all ${
                            speakingMsgId === (msg.id || index)
                              ? 'bg-rose-500/30 text-rose-200 border border-rose-500/40'
                              : 'bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/30'
                          }`}
                          title={speakingMsgId === (msg.id || index) ? "Stop speech" : "Read aloud"}
                        >
                          {speakingMsgId === (msg.id || index) ? (
                            <>
                              <VolumeX className="w-3 h-3 text-rose-400" />
                              <span>Stop</span>
                            </>
                          ) : (
                            <>
                              <Volume2 className="w-3 h-3" />
                              <span>Speak</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>
                    <div>{msg.message}</div>
                  </div>

                  {!isAI && (
                    <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white shrink-0 mt-1 font-bold text-xs">
                      U
                    </div>
                  )}
                </div>
              );
            })}

            {sending && (
              <div className="flex items-center space-x-2 text-xs text-indigo-400 italic p-3 bg-slate-950/60 rounded-xl border border-indigo-500/20 w-max">
                <BrainCircuit className="w-4 h-4 animate-spin" />
                <span>Interviewer is evaluating response & formulating next question...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Chat Input Box */}
          {session.status === 'IN_PROGRESS' ? (
            <div className="p-3.5 bg-slate-950 border-t border-slate-800 space-y-2">
              {isListening && (
                <div className="flex items-center justify-between px-3 py-2 bg-rose-500/15 border border-rose-500/40 rounded-xl text-rose-300 text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
                    <span className="font-bold">Live Voice Dictation:</span>
                    <span>Speak clearly into your microphone — speech will transcribe into the box...</span>
                  </div>
                  <button
                    type="button"
                    onClick={toggleListening}
                    className="text-[11px] font-bold text-rose-200 hover:text-white underline ml-2"
                  >
                    Done Speaking
                  </button>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={toggleListening}
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all border ${
                    isListening
                      ? 'bg-rose-600 text-white border-rose-500 shadow-lg shadow-rose-600/30 animate-pulse'
                      : 'bg-slate-900 hover:bg-slate-800 text-slate-200 border-slate-800 hover:border-slate-700'
                  }`}
                  title={isListening ? "Click to stop microphone" : "Speak your response into microphone"}
                >
                  {isListening ? (
                    <>
                      <MicOff className="w-4 h-4 text-white" />
                      <span className="hidden sm:inline">Listening...</span>
                    </>
                  ) : (
                    <>
                      <Mic className="w-4 h-4 text-indigo-400" />
                      <span className="hidden sm:inline">Speak</span>
                    </>
                  )}
                </button>

                <textarea
                  value={studentInput}
                  onChange={(e) => setStudentInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey && studentInput.trim()) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  rows={2}
                  placeholder={
                    isListening
                      ? 'Listening... speak your response now...'
                      : 'Explain your approach, derive Big-O complexity, or speak your answer (Click Speak or Press Enter)...'
                  }
                  className="flex-grow bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs sm:text-sm text-white focus:outline-none focus:border-indigo-500 resize-none font-sans"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!studentInput.trim() || sending}
                  className="px-5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl font-bold flex items-center justify-center transition-all shadow-md shadow-indigo-600/20"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-slate-950 border-t border-slate-800 text-center text-xs text-slate-400">
              This interview has finished. View your comprehensive evaluation report below.
            </div>
          )}
        </div>

        {/* RIGHT / CODE PANEL (When active) */}
        {showEditor && (
          <div className="lg:col-span-6 flex flex-col space-y-4">
            <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs text-slate-300">
                <Code2 className="w-4 h-4 text-indigo-400" />
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-white focus:outline-none"
                >
                  <option value="python">Python 3</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCode(session.problem.starter_code?.python || '')}
                  className="p-1.5 text-slate-400 hover:text-white rounded text-xs flex items-center space-x-1"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Reset</span>
                </button>

                <button
                  onClick={handleRunCode}
                  disabled={isExecuting}
                  className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors"
                >
                  <Play className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{isExecuting ? 'Running...' : 'Run'}</span>
                </button>

                <button
                  onClick={handleSubmitCode}
                  disabled={isExecuting}
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors shadow-md"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Code</span>
                </button>
              </div>
            </div>

            {/* Monaco Editor */}
            <div className="min-h-[380px] flex-grow rounded-xl overflow-hidden border border-slate-800">
              <CodeEditor code={code} onChange={setCode} language={language} />
            </div>

            {/* Test Results Output */}
            {execResult && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2 text-xs font-mono">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className={`px-2 py-0.5 rounded font-bold ${execResult.status === 'ACCEPTED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
                    {execResult.status}
                  </span>
                  <span className="text-slate-400">
                    Passed: {execResult.test_cases_passed} / {execResult.total_test_cases} • {execResult.runtime} ms
                  </span>
                </div>
                {execResult.error_message && (
                  <div className="text-rose-400 whitespace-pre-wrap">{execResult.error_message}</div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* FINAL EVALUATION REPORT MODAL / SECTION */}
      {evaluation && (
        <div className="mt-8 bg-slate-900 border border-indigo-500/40 rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-indigo-600/20 border border-indigo-500/40 rounded-2xl text-indigo-400">
                <Award className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                  Final Interview Performance Report
                </h3>
                <p className="text-xs text-slate-400">
                  Comprehensive rubric score & constructive feedback generated by the AI Technical Interviewer.
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4 bg-slate-950 p-3.5 rounded-2xl border border-slate-800">
              <div className="text-right">
                <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                  Overall Score
                </span>
                <span className="text-2xl font-extrabold text-indigo-400 font-mono">
                  {evaluation.overall_score} / 100
                </span>
              </div>
            </div>
          </div>

          {/* Rubric Category Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            {[
              { label: 'Problem Understanding', item: evaluation.problem_understanding },
              { label: 'Approach Quality', item: evaluation.approach_quality },
              { label: 'Technical Reasoning', item: evaluation.technical_reasoning },
              { label: 'Complexity Analysis', item: evaluation.complexity_analysis },
              { label: 'Edge Case Awareness', item: evaluation.edge_case_awareness },
              { label: 'Optimization & Trade-offs', item: evaluation.optimization },
              { label: 'Communication', item: evaluation.communication },
              { label: 'Code Execution', item: evaluation.coding_correctness },
            ].map((cat, idx) => (
              <div key={idx} className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-300 text-[11px]">{cat.label}</span>
                  <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${cat.item?.rating === 'Strong' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-blue-500/20 text-blue-300'}`}>
                    {cat.item?.rating || 'Good'}
                  </span>
                </div>
                <p className="text-slate-400 leading-snug">{cat.item?.notes || 'Solid demonstration.'}</p>
              </div>
            ))}
          </div>

          {/* Strengths & Areas for Improvement */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl space-y-2">
              <h4 className="font-bold text-emerald-300 flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>Key Strengths</span>
              </h4>
              <ul className="list-disc list-inside space-y-1 text-slate-300">
                {evaluation.strengths.map((str, i) => (
                  <li key={i}>{str}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl space-y-2">
              <h4 className="font-bold text-amber-300 flex items-center space-x-2">
                <HelpCircle className="w-4 h-4" />
                <span>Areas for Improvement</span>
              </h4>
              <ul className="list-disc list-inside space-y-1 text-slate-300">
                {evaluation.areas_for_improvement.map((area, i) => (
                  <li key={i}>{area}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Final Feedback Summary */}
          <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">
              Interviewer Summary Feedback
            </span>
            <p className="text-slate-200 leading-relaxed font-sans">{evaluation.final_feedback}</p>
          </div>

          {/* Recommended Practice Problems */}
          {evaluation.recommended_problems && evaluation.recommended_problems.length > 0 && (
            <div className="space-y-3 pt-2 border-t border-slate-800">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Recommended Next Practice Problems
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {evaluation.recommended_problems.map((prob) => (
                  <Link
                    key={prob.id}
                    to={`/problems/${prob.slug}`}
                    className="p-3 bg-slate-950 border border-slate-800 hover:border-indigo-500/50 rounded-xl flex items-center justify-between text-xs transition-colors"
                  >
                    <div>
                      <p className="font-bold text-white">{prob.title}</p>
                      <span className={`text-[10px] font-semibold ${getDifficultyBadgeClass(prob.difficulty as Difficulty)}`}>
                        {prob.difficulty}
                      </span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-indigo-400" />
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
