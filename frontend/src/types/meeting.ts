export type MeetingStatus = "uploaded" | "processing" | "completed" | "failed";

export interface Task {
  task: string;
  owner: string;
  deadline: string;
}

export interface Decision {
  decision: string;
  evidence: string;
}

export interface Meeting {
  id: string;
  filename: string;
  status: MeetingStatus;
  created_at: string;
  raw_transcript: string | null;
  refined_transcript: string | null;
  summary: string | null;
  minutes: string[];
  decisions: Decision[];
  tasks: Task[];
  error: string | null;
  current_stage: string | null;
  progress: number;
}

export interface MeetingStatusResponse {
  id: string;
  status: MeetingStatus;
  current_stage: string | null;
  progress: number;
  error: string | null;
}
