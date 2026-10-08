import { AlertCircle, AudioLines, Check, LoaderCircle, RotateCcw } from "lucide-react";
import type { Meeting } from "../types/meeting";

interface Props {
  meeting: Meeting;
  error: string | null;
  busy: boolean;
  onRetry: () => void;
}

const stages = ["Audio uploaded", "Transcription", "Transcript refinement", "Meeting documentation", "Finalizing"];

export default function ProcessingPage({ meeting, error, busy, onRetry }: Props) {
  if (meeting.status === "failed") {
    return (
      <main className="processing-shell">
        <div className="processing-card failed-card">
          <span className="failure-icon"><AlertCircle size={25} /></span>
          <p className="eyebrow centered-eyebrow">PROCESSING STOPPED</p>
          <h1>We couldn’t finish this recording.</h1>
          <p className="processing-description">{meeting.error || "An unexpected issue stopped processing. Please try again."}</p>
          {error && <p className="error-message">{error}</p>}
          <button className="button-primary" onClick={onRetry} disabled={busy}>
            <RotateCcw size={16} /> {busy ? "Retrying…" : "Try again"}
          </button>
        </div>
      </main>
    );
  }

  const activeIndex = stages.findIndex((stage) => stage === meeting.current_stage);
  const currentIndex = Math.max(1, activeIndex);
  return (
    <main className="processing-shell">
      <section className="processing-card">
        <div className="processing-animation"><AudioLines size={29} /></div>
        <p className="eyebrow centered-eyebrow">A LITTLE CLARITY IS ON ITS WAY</p>
        <h1>Making sense of your meeting.</h1>
        <p className="processing-description">We’re carefully working through your recording. You can keep this page open; the status below updates as each stage completes.</p>
        <div className="progress-heading">
          <span>{meeting.current_stage || "Preparing audio"}</span>
          <strong>{meeting.progress}%</strong>
        </div>
        <div className="progress-track"><div className="progress-value" style={{ width: `${meeting.progress}%` }} /></div>
        <div className="pipeline-list">
          {stages.map((stage, index) => {
            const complete = meeting.progress >= (index === 0 ? 1 : [35, 45, 75, 100][index - 1]);
            const active = index === currentIndex && !complete;
            return (
              <div className={`pipeline-stage ${complete ? "is-complete" : ""} ${active ? "is-active" : ""}`} key={stage}>
                <span className="stage-check">{complete ? <Check size={13} /> : active ? <LoaderCircle className="spin" size={14} /> : <span />}</span>
                <span>{stage}</span>
                {active && <small>IN PROGRESS</small>}
              </div>
            );
          })}
        </div>
        {error && <p className="error-message" role="alert">{error}</p>}
      </section>
    </main>
  );
}
