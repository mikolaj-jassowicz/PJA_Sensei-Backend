export type TutorAction = "hint" | "next" | "solution";

export type HintLevel = 1 | 2 | 3 | 4 | 5 | 6;

export type TutorRole = "student" | "assistant" | "system";

export interface TutorMessage {
  id: string;
  role: TutorRole;
  content: string;
  hintLevel?: HintLevel;
  createdAt: string;
  isSolution?: boolean;
  followUpQuestion?: string;
}

export interface TutorSessionSnapshot {
  sessionId: string;
  problemStatement: string;
  studentWork: string;
  studentQuestion: string;
  messages: TutorMessage[];
  currentHintLevel: HintLevel | 0;
  hintCount: number;
  canRequestHint: boolean;
  solutionRevealed: boolean;
  nextRecommendedAction: "continue_independently" | "request_next_hint" | "show_solution";
}

export interface TutorRequestPayload {
  sessionId?: string;
  problemStatement: string;
  studentWork: string;
  studentQuestion: string;
  action: TutorAction;
}

export interface TutorResponsePayload {
  session: TutorSessionSnapshot;
  latestMessage: TutorMessage;
}
