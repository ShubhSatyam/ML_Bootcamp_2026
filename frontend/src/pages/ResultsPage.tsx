import { useState } from "react";
import { ArrowDownToLine, ArrowLeft, Check, Clipboard, FileJson2, FileText, ListChecks, Quote, Scale, Sparkles } from "lucide-react";
import { downloadUrl } from "../services/api";
import type { Meeting } from "../types/meeting";

interface Props {
  meeting: Meeting;
  onNewMeeting: () => void;
}

const tabs = [
  { id: "raw", label: "Raw transcript", icon: Quote },
  { id: "refined", label: "Refined transcript", icon: Sparkles },
  { id: "summary", label: "Summary", icon: FileText },
  { id: "minutes", label: "Meeting minutes", icon: Clipboard },
  { id: "decisions", label: "Key decisions", icon: Scale },
  { id: "tasks", label: "Action items", icon: ListChecks },
] as const;
type TabId = (typeof tabs)[number]["id"];

export default function ResultsPage({ meeting, onNewMeeting }: Props) {
  const [selected, setSelected] = useState<TabId>("raw");
  const [compare, setCompare] = useState(false);
  return (
    <main className="results-shell">
      <div className="results-topline">
        <button className="back-button" onClick={onNewMeeting}><ArrowLeft size={16} /> New meeting</button>
        <span className="result-ready"><span /> NOTES READY</span>
      </div>
      <div className="results-title-row">
        <div>
          <p className="eyebrow">YOUR MEETING, MADE CLEAR</p>
          <h1>Meeting notes</h1>
          <p className="result-filename">{meeting.filename} <span>·</span> {new Date(meeting.created_at).toLocaleDateString()}</p>
        </div>
        <div className="download-group">
          <a className="download-button" href={downloadUrl(meeting.id, "record")}><ArrowDownToLine size={16} /> Download notes</a>
          <a className="download-json" href={downloadUrl(meeting.id, "json")} title="Download JSON"><FileJson2 size={16} /></a>
        </div>
      </div>
      <div className="results-layout">
        <nav className="results-nav" aria-label="Meeting results" role="tablist">
          <span className="nav-caption">MEETING RECORD</span>
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={`result-tab ${selected === id ? "selected" : ""}`}
              onClick={() => setSelected(id)}
              role="tab"
              aria-selected={selected === id}
              aria-controls="meeting-result-panel"
            >
              <Icon size={17} strokeWidth={1.8} /><span>{label}</span>{selected === id && <span className="tab-indicator" />}
            </button>
          ))}
          <div className="nav-downloads">
            <span className="nav-caption">TRANSCRIPTS</span>
            <a href={downloadUrl(meeting.id, "raw-transcript")}><ArrowDownToLine size={14} /> Raw transcript</a>
            <a href={downloadUrl(meeting.id, "refined-transcript")}><ArrowDownToLine size={14} /> Refined transcript</a>
          </div>
        </nav>
        <section className="result-content" id="meeting-result-panel" role="tabpanel">
          <div className="content-heading">
            <div>
              <span className="content-kicker">{tabs.find((tab) => tab.id === selected)?.label.toUpperCase()}</span>
              <h2>{heading(selected)}</h2>
            </div>
            {(selected === "raw" || selected === "refined") && (
              <button className="compare-button" onClick={() => setCompare((value) => !value)}>
                {compare ? "Show one transcript" : "Compare both"}
              </button>
            )}
          </div>
          {compare && (selected === "raw" || selected === "refined") ? (
            <div className="comparison-grid">
              <TranscriptPanel title="Raw transcript" text={meeting.raw_transcript} tone="muted" />
              <TranscriptPanel title="Refined transcript" text={meeting.refined_transcript} tone="accent" />
            </div>
          ) : <TabContent meeting={meeting} selected={selected} />}
        </section>
      </div>
      <footer className="results-footer">Generated from what was said in the recording. Unstated owners and deadlines are marked <strong>Unspecified</strong>.</footer>
    </main>
  );
}

function heading(id: TabId) {
  return {
    raw: "As transcribed",
    refined: "Polished for clarity",
    summary: "The conversation, at a glance",
    minutes: "What was discussed",
    decisions: "What was agreed",
    tasks: "What happens next",
  }[id];
}

function TabContent({ meeting, selected }: { meeting: Meeting; selected: TabId }) {
  if (selected === "raw") return <TranscriptPanel text={meeting.raw_transcript} />;
  if (selected === "refined") return <TranscriptPanel text={meeting.refined_transcript} tone="accent" />;
  if (selected === "summary") {
    return <article className="summary-card"><span className="summary-sparkle"><Sparkles size={18} /></span><p>{meeting.summary || "No summary was generated."}</p></article>;
  }
  if (selected === "minutes") {
    return meeting.minutes.length ? (
      <div className="minutes-list">{meeting.minutes.map((item, index) => <article className="minute-item" key={`${index}-${item}`}><span>{String(index + 1).padStart(2, "0")}</span><p>{item}</p></article>)}</div>
    ) : <EmptyState text="No meeting minutes were identified." />;
  }
  if (selected === "decisions") {
    return meeting.decisions.length ? (
      <div className="decision-list">{meeting.decisions.map((item, index) => (
        <article className="decision-card" key={`${index}-${item.decision}`}><div className="decision-label"><Check size={14} /> DECISION {String(index + 1).padStart(2, "0")}</div><h3>{item.decision}</h3><blockquote>“{item.evidence}”</blockquote></article>
      ))}</div>
    ) : <EmptyState text="No explicit decisions were identified in this meeting." />;
  }
  return meeting.tasks.length ? (
    <div className="task-list">{meeting.tasks.map((item, index) => (
      <article className="task-card" key={`${index}-${item.task}`}>
        <div className="task-main"><span className="task-number">{String(index + 1).padStart(2, "0")}</span><h3>{item.task}</h3></div>
        <div className="task-metadata"><span><small>OWNER</small><strong>{item.owner}</strong></span><span><small>DEADLINE</small><strong>{item.deadline}</strong></span></div>
      </article>
    ))}</div>
  ) : <EmptyState text="No action items were identified in this meeting." />;
}

function TranscriptPanel({ title, text, tone }: { title?: string; text: string | null; tone?: "muted" | "accent" }) {
  return (
    <article className={`transcript-card ${tone || ""}`}>
      {title && <div className="transcript-label">{title}</div>}
      <p>{text || "Transcript is not available."}</p>
    </article>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="empty-state"><span><ListChecks size={21} /></span><p>{text}</p></div>;
}
