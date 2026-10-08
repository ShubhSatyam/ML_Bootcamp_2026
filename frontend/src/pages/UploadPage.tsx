import { useRef, useState } from "react";
import { ArrowRight, FileAudio2, FileUp, ShieldCheck, Sparkles, X } from "lucide-react";
import { formatBytes, validateAudio } from "../utils/files";
import type { Meeting } from "../types/meeting";

interface Props {
  meeting: Meeting | null;
  busy: boolean;
  error: string | null;
  onUpload: (file: File) => void;
  onProcess: () => void;
  onReset: () => void;
  onClearError: () => void;
}

const maxSizeMb = Number(import.meta.env.VITE_MAX_FILE_SIZE_MB || 100);

export default function UploadPage({ meeting, busy, error, onUpload, onProcess, onReset, onClearError }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const chooseFile = (selected: File | undefined) => {
    if (!selected) return;
    onClearError();
    const validation = validateAudio(selected, maxSizeMb);
    setFileError(validation);
    setFile(validation ? null : selected);
  };

  const uploadSelected = async () => {
    if (!file) return;
    try {
      await file.slice(0, 1).arrayBuffer();
      onUpload(file);
    } catch {
      setFileError("The selected file could not be read. Choose a different recording.");
    }
  };

  return (
    <main className="hero-layout">
      <section className="hero-copy">
        <div className="eyebrow"><span className="eyebrow-dot" /> YOUR MEETINGS, MADE CLEAR</div>
        <h1>Be present.<br /><span>We’ll take notes.</span></h1>
        <p className="hero-description">Turn a meeting recording into a clear transcript, thoughtful summary, and the next steps that matter.</p>
        <div className="trust-points">
          <span><ShieldCheck size={16} /> Your recordings stay private</span>
          <span><Sparkles size={16} /> Notes grounded in what was said</span>
        </div>
        <div className="how-it-works">
          <span className="how-label">HOW IT WORKS</span>
          <div className="steps-row">
            <Step number="01" title="Upload" detail="Share your audio" />
            <span className="step-line" />
            <Step number="02" title="Transcribe" detail="Words, carefully refined" />
            <span className="step-line" />
            <Step number="03" title="Take it forward" detail="Decisions & action items" />
          </div>
        </div>
      </section>
      <section className="upload-card" aria-label="Upload meeting audio">
        <div className="card-heading">
          <div><h2>Start with a recording</h2><p>English audio · Up to {maxSizeMb} MB</p></div>
          <span className="card-icon"><FileAudio2 size={19} /></span>
        </div>
        {meeting ? (
          <div className="uploaded-state">
            <div className="success-orb"><FileAudio2 size={23} /></div>
            <h3>Your recording is ready</h3>
            <p className="uploaded-name">{meeting.filename}</p>
            <p className="subtle">The audio is uploaded and ready to process.</p>
            {error && <ErrorMessage message={error} />}
            <button className="button-primary full-button" onClick={onProcess} disabled={busy}>
              {busy ? "Starting…" : "Start processing"} <ArrowRight size={17} />
            </button>
            <button className="button-quiet" onClick={onReset}>Choose another recording</button>
          </div>
        ) : (
          <>
            <div
              className={`drop-zone ${dragging ? "is-dragging" : ""} ${file ? "has-file" : ""}`}
              onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                chooseFile(event.dataTransfer.files[0]);
              }}
              onClick={() => input.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") input.current?.click(); }}
            >
              <input
                ref={input}
                type="file"
                accept=".wav,.mp3,.m4a,.mp4,.ogg,.flac,.webm,audio/*"
                hidden
                onChange={(event) => chooseFile(event.target.files?.[0])}
              />
              {file ? (
                <div className="file-selected">
                  <span className="file-icon"><FileAudio2 size={20} /></span>
                  <span className="file-details"><strong>{file.name}</strong><small>{formatBytes(file.size)}</small></span>
                  <button
                    type="button"
                    className="remove-file"
                    aria-label="Remove selected file"
                    onClick={(event) => { event.stopPropagation(); setFile(null); setFileError(null); }}
                  ><X size={17} /></button>
                </div>
              ) : (
                <>
                  <span className="upload-orb"><FileUp size={21} /></span>
                  <strong>Drop your audio here</strong>
                  <span className="drop-support">or <span className="browse-link">browse files</span></span>
                </>
              )}
            </div>
            <p className="format-note">WAV, MP3, M4A, MP4, OGG, FLAC or WebM</p>
            {(fileError || error) && <ErrorMessage message={fileError || error || ""} />}
            <button className="button-primary full-button" onClick={uploadSelected} disabled={!file || busy}>
              {busy ? "Uploading…" : "Upload recording"} <ArrowRight size={17} />
            </button>
            <p className="privacy-note"><ShieldCheck size={14} /> Only used to create your meeting notes</p>
          </>
        )}
      </section>
    </main>
  );
}

function Step({ number, title, detail }: { number: string; title: string; detail: string }) {
  return <div className="step"><span>{number}</span><strong>{title}</strong><small>{detail}</small></div>;
}

function ErrorMessage({ message }: { message: string }) {
  return <div className="error-message" role="alert">{message}</div>;
}
