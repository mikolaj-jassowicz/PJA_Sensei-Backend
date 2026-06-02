import {
  ArrowRight,
  BrainCircuit,
  HelpCircle,
  Lightbulb,
  RefreshCcw,
  Sparkles,
  Trophy
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type {
  HintLevel,
  TutorAction,
  TutorMessage,
  TutorResponsePayload,
  TutorSessionSnapshot
} from "../shared/types";

const STORAGE_KEY = "pjasensei.socratic-tutor.session";

interface ClientSessionState {
  sessionId: string;
  problemStatement: string;
  studentWork: string;
  studentQuestion: string;
  messages: TutorMessage[];
  currentHintLevel: HintLevel | 0;
  hintCount: number;
  solutionRevealed: boolean;
}

const initialSession = (): ClientSessionState => ({
  sessionId: crypto.randomUUID(),
  problemStatement:
    "A rectangle has a perimeter of 30 cm. Its length is 3 cm more than twice its width. Find the dimensions.",
  studentWork: "I wrote P = 2l + 2w, but I am not sure what to do with the other sentence.",
  studentQuestion: "How do I turn the words about length and width into something useful?",
  messages: [],
  currentHintLevel: 0,
  hintCount: 0,
  solutionRevealed: false
});

function App() {
  const [session, setSession] = useState<ClientSessionState>(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    return saved ? (JSON.parse(saved) as ClientSessionState) : initialSession();
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  }, [session]);

  const latestAssistantMessage = useMemo(
    () => [...session.messages].reverse().find((message) => message.role === "assistant"),
    [session.messages]
  );

  const canAskForHelp =
    Boolean(session.problemStatement.trim()) && Boolean(session.studentQuestion.trim()) && !isLoading;
  const nextHintDisabled = !canAskForHelp || session.solutionRevealed || session.currentHintLevel >= 5;

  async function requestTutorAction(action: TutorAction) {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/tutor/hint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sessionId: session.sessionId,
          problemStatement: session.problemStatement,
          studentWork: session.studentWork,
          studentQuestion: session.studentQuestion,
          action
        })
      });

      const responseText = await response.text();
      const payload = responseText ? JSON.parse(responseText) : null;

      if (!response.ok) {
        throw new Error(payload?.error ?? responseText ?? "The tutor could not generate a response.");
      }

      if (!payload) {
        throw new Error("The tutor API returned an empty response.");
      }

      const result = payload as TutorResponsePayload;
      setSession(fromServerSession(result.session));
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Something went wrong.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  async function resetSession() {
    if (session.sessionId) {
      void fetch(`/api/tutor/session/${session.sessionId}`, { method: "DELETE" });
    }

    window.localStorage.removeItem(STORAGE_KEY);
    setSession(initialSession());
    setError(null);
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="left-panel" aria-label="Student inputs">
          <div className="brand-row">
            <div className="brand-mark">
              <BrainCircuit aria-hidden="true" size={22} />
            </div>
            <div>
              <p className="eyebrow">PJASensei prototype</p>
              <h1>Socratic Tutor</h1>
            </div>
          </div>

          <label className="field">
            <span>Problem statement</span>
            <textarea
              value={session.problemStatement}
              onChange={(event) =>
                setSession((current) => ({ ...current, problemStatement: event.target.value }))
              }
              rows={7}
            />
          </label>

          <label className="field">
            <span>Your current work</span>
            <textarea
              value={session.studentWork}
              onChange={(event) =>
                setSession((current) => ({ ...current, studentWork: event.target.value }))
              }
              rows={6}
            />
          </label>

          <label className="field">
            <span>What are you stuck on?</span>
            <textarea
              value={session.studentQuestion}
              onChange={(event) =>
                setSession((current) => ({ ...current, studentQuestion: event.target.value }))
              }
              rows={4}
            />
          </label>

          {error && <p className="error-message">{error}</p>}

          <div className="controls" aria-label="Tutor controls">
            <button type="button" onClick={() => requestTutorAction("hint")} disabled={!canAskForHelp}>
              <Lightbulb aria-hidden="true" size={18} />
              Get Hint
            </button>
            <button type="button" onClick={() => requestTutorAction("next")} disabled={nextHintDisabled}>
              <ArrowRight aria-hidden="true" size={18} />
              Next Hint
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => requestTutorAction("solution")}
              disabled={!canAskForHelp || session.solutionRevealed}
            >
              <Trophy aria-hidden="true" size={18} />
              Show Solution
            </button>
            <button type="button" className="ghost" onClick={resetSession} disabled={isLoading}>
              <RefreshCcw aria-hidden="true" size={18} />
              Reset
            </button>
          </div>
        </aside>

        <section className="right-panel" aria-label="Tutor conversation">
          <div className="status-strip">
            <HintMeter level={session.currentHintLevel} />
            <div className="stat">
              <span>{session.hintCount}</span>
              hints used
            </div>
            <div className="stat">
              <span>{session.solutionRevealed ? "Shown" : "Hidden"}</span>
              solution
            </div>
          </div>

          <div className="conversation-header">
            <div>
              <p className="eyebrow">Conversation</p>
              <h2>Guided reasoning</h2>
            </div>
            {latestAssistantMessage && (
              <p className="recommendation">{recommendationText(session, latestAssistantMessage)}</p>
            )}
          </div>

          <div className="conversation">
            {session.messages.length === 0 ? (
              <div className="empty-state">
                <Sparkles aria-hidden="true" size={28} />
                <p>Ask for a hint when you want a nudge. The tutor will start gently and only get more explicit as you request more help.</p>
              </div>
            ) : (
              session.messages.map((message) => <MessageBubble key={message.id} message={message} />)
            )}
            {isLoading && (
              <div className="message assistant loading">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

function fromServerSession(serverSession: TutorSessionSnapshot): ClientSessionState {
  return {
    sessionId: serverSession.sessionId,
    problemStatement: serverSession.problemStatement,
    studentWork: serverSession.studentWork,
    studentQuestion: serverSession.studentQuestion,
    messages: serverSession.messages,
    currentHintLevel: serverSession.currentHintLevel,
    hintCount: serverSession.hintCount,
    solutionRevealed: serverSession.solutionRevealed
  };
}

function HintMeter({ level }: { level: HintLevel | 0 }) {
  return (
    <div className="hint-meter" aria-label={`Current hint level ${level || 0}`}>
      <div>
        <p className="eyebrow">Hint level</p>
        <strong>{level === 0 ? "Not started" : level === 6 ? "Final solution" : `Level ${level}`}</strong>
      </div>
      <div className="meter-steps" aria-hidden="true">
        {[1, 2, 3, 4, 5].map((step) => (
          <span key={step} className={step <= level ? "active" : ""} />
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: TutorMessage }) {
  const isAssistant = message.role === "assistant";

  return (
    <article className={`message ${message.role}`}>
      <div className="message-meta">
        <span>{isAssistant ? (message.isSolution ? "Solution" : `Hint level ${message.hintLevel}`) : "Student"}</span>
        {isAssistant && !message.isSolution && <HelpCircle aria-hidden="true" size={15} />}
      </div>
      <p>{message.content}</p>
      {message.followUpQuestion && <p className="follow-up">{message.followUpQuestion}</p>}
    </article>
  );
}

function recommendationText(session: ClientSessionState, latestMessage: TutorMessage) {
  if (session.solutionRevealed || latestMessage.isSolution) {
    return "Review the reasoning, then try a similar problem without the solution visible.";
  }

  if (session.currentHintLevel >= 5) {
    return "You have reached the strongest hint. The solution is available when you are ready.";
  }

  if (session.currentHintLevel <= 2) {
    return "Try one independent step before asking for the next hint.";
  }

  return "Use the strategy, update your work, then request another hint if needed.";
}

export default App;
