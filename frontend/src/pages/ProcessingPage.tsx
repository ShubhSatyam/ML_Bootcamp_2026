import { AlertCircle, AudioLines, Check, Clipboard, FileText, LoaderCircle, RotateCcw, Scale } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";
import type { Meeting } from "../types/meeting";

interface Props {
  meeting: Meeting;
  error: string | null;
  busy: boolean;
  onRetry: () => void;
  onNewMeeting: () => void;
}

const stages = ["Audio uploaded", "Transcription", "Transcript refinement", "Meeting documentation", "Finalizing"];

export default function ProcessingPage({ meeting, error, busy, onRetry, onNewMeeting }: Props) {
  if (meeting.status === "failed") {
    return (
      <main className="processing-shell">
        <div className="processing-card failed-card">
          <span className="failure-icon"><AlertCircle size={25} /></span>
          <p className="eyebrow centered-eyebrow">PROCESSING STOPPED</p>
          <h1>We couldn’t finish this recording.</h1>
          <p className="processing-description">{meeting.error || "An unexpected issue stopped processing. Please try again."}</p>
          {error && <p className="error-message">{error}</p>}
          <TranscriptSections meeting={meeting} />
          <DocumentationSections meeting={meeting} />
          <button className="button-primary" onClick={onRetry} disabled={busy}>
            <RotateCcw size={16} /> {busy ? "Retrying…" : "Try again"}
          </button>
          <button className="button-quiet" onClick={onNewMeeting}>Upload another recording</button>
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
        <TranscriptSections meeting={meeting} />
        <DocumentationSections meeting={meeting} />
      </section>
    </main>
  );
}

function TranscriptSections({ meeting }: { meeting: Meeting }) {
  return (
    <section className="live-transcripts" aria-labelledby="transcripts-heading">
      <div className="live-transcripts-heading">
        <FileText size={15} />
        <span id="transcripts-heading">TRANSCRIPTS</span>
        <span className="transcripts-note">Raw and refined versions are kept separate.</span>
      </div>
      <div className="live-transcript-grid">
        <TranscriptPanel
          title="Raw transcript"
          description="Original text produced from the audio."
          text={meeting.raw_transcript}
          emptyMessage={meeting.status === "failed" ? "Raw transcript unavailable." : "The raw transcript will appear after transcription."}
          pending={meeting.status === "processing" && !meeting.raw_transcript}
        />
        <TranscriptPanel
          title="Refined transcript"
          description="Corrected for clarity while preserving what was said."
          text={meeting.refined_transcript}
          emptyMessage={meeting.status === "failed" ? "Refined transcript could not be generated." : "The refined transcript will appear after refinement."}
          pending={meeting.status === "processing" && !meeting.refined_transcript}
        />
      </div>
    </section>
  );
}

function DocumentationSections({ meeting }: { meeting: Meeting }) {
  const summary = meeting.summary?.trim() || null;
  const documentationAvailable = summary !== null;
  const documentationPending = meeting.status === "processing" && meeting.progress >= 70 && !documentationAvailable;
  const documentationFailed = meeting.status === "failed" && !documentationAvailable;
  const unavailableMessage = documentationFailed
    ? meeting.progress >= 70
      ? "Meeting documentation could not be generated."
      : "Unavailable because processing stopped before documentation."
    : null;
  const status = documentationAvailable
    ? "AVAILABLE"
    : documentationPending
      ? "IN PROGRESS"
      : documentationFailed
        ? "UNAVAILABLE"
        : "WAITING";

  return (
    <section className="meeting-documentation" aria-labelledby="documentation-heading">
      <div className="live-transcripts-heading">
        <FileText size={15} />
        <span id="documentation-heading">MEETING DOCUMENTATION</span>
        <span className="transcripts-note">Summary, discussion points, and agreed decisions.</span>
      </div>
      <div className="documentation-grid">
        <DocumentationPanel
          className="summary-document"
          title="Meeting summary"
          description="A concise overview of the conversation."
          status={status}
          content={summary}
          emptyMessage={unavailableMessage || "The summary will appear after meeting documentation."}
        >
          {summary && <p className="documentation-summary">{summary}</p>}
        </DocumentationPanel>
        <DocumentationPanel
          title="Meeting minutes"
          description="Organized points discussed in the meeting."
          status={status}
          content={documentationAvailable ? meeting.minutes.join("\n") : null}
          emptyMessage={unavailableMessage || "Minutes will appear after meeting documentation."}
        >
          {documentationAvailable && (
            meeting.minutes.length ? (
              <ol className="live-minutes-list">
                {meeting.minutes.map((minute, index) => <li key={`${index}-${minute}`}>{minute}</li>)}
              </ol>
            ) : <p className="documentation-empty">No meeting minutes were identified.</p>
          )}
        </DocumentationPanel>
        <DocumentationPanel
          title="Key decisions"
          description="Decisions explicitly supported by the conversation."
          status={status}
          content={documentationAvailable ? meeting.decisions.map(({ decision, evidence }, index) => `${index + 1}. ${decision}\nEvidence: ${evidence}`).join("\n\n") : null}
          emptyMessage={unavailableMessage || "Decisions will appear after meeting documentation."}
        >
          {documentationAvailable && (
            meeting.decisions.length ? (
              <ol className="live-decisions-list">
                {meeting.decisions.map((item, index) => (
                  <li key={`${index}-${item.decision}`}>
                    <strong><Scale size={14} /> {item.decision}</strong>
                    <p>{item.evidence}</p>
                  </li>
                ))}
              </ol>
            ) : <p className="documentation-empty">No explicit decisions were identified.</p>
          )}
        </DocumentationPanel>
      </div>
    </section>
  );
}

function DocumentationPanel({
  className = "",
  title,
  description,
  status,
  content,
  emptyMessage,
  children,
}: {
  className?: string;
  title: string;
  description: string;
  status: string;
  content: string | null;
  emptyMessage: string;
  children: ReactNode;
}) {
  const [copyMessage, setCopyMessage] = useState("");
  const hasContent = content !== null;
  const copyContent = async () => {
    if (!content) return;
    try {
      await navigator.clipboard.writeText(content);
      setCopyMessage("Copied");
    } catch {
      setCopyMessage("Copy unavailable in this browser.");
    }
  };

  return (
    <article className={`documentation-panel ${className}`}>
      <div className="transcript-panel-heading">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
        <span className={`transcript-status ${hasContent ? "is-available" : status === "IN PROGRESS" ? "is-pending" : ""}`}>
          {status}
        </span>
      </div>
      <div className={`documentation-panel-content ${hasContent ? "" : "is-empty"}`} aria-live={status === "IN PROGRESS" ? "polite" : undefined}>
        {hasContent ? children : <p className="documentation-empty">{emptyMessage}</p>}
      </div>
      <div className="transcript-panel-footer">
        <span role="status" aria-live="polite">{copyMessage}</span>
        <button type="button" className="copy-transcript-button" onClick={copyContent} disabled={!content}>
          <Clipboard size={14} /> Copy {title.toLowerCase()}
        </button>
      </div>
    </article>
  );
}

function TranscriptPanel({
  title,
  description,
  text,
  emptyMessage,
  pending,
}: {
  title: string;
  description: string;
  text: string | null;
  emptyMessage: string;
  pending: boolean;
}) {
  const [copyMessage, setCopyMessage] = useState("");

  const copyTranscript = async () => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopyMessage("Copied");
    } catch {
      setCopyMessage("Copy unavailable in this browser.");
    }
  };

  return (
    <article className={`live-transcript ${text ? "has-transcript" : ""}`}>
      <div className="transcript-panel-heading">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
        <span className={`transcript-status ${text ? "is-available" : pending ? "is-pending" : ""}`}>
          {text ? "AVAILABLE" : pending ? "IN PROGRESS" : "UNAVAILABLE"}
        </span>
      </div>
      <div className={`transcript-panel-content ${text ? "" : "is-empty"}`} aria-live={pending ? "polite" : undefined}>
        {text || emptyMessage}
      </div>
      <div className="transcript-panel-footer">
        <span role="status" aria-live="polite">{copyMessage}</span>
        <button type="button" className="copy-transcript-button" onClick={copyTranscript} disabled={!text}>
          <Clipboard size={14} /> Copy transcript
        </button>
      </div>
    </article>
  );
}
