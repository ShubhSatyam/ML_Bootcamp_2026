import { useCallback, useEffect, useState } from "react";
import { getMeeting, getMeetingStatus, startProcessing, uploadAudio } from "../services/api";
import type { Meeting } from "../types/meeting";

export function useMeeting() {
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(async (file: File) => {
    setBusy(true);
    setError(null);
    try {
      const result = await uploadAudio(file);
      setMeeting(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }, []);

  const process = useCallback(async () => {
    if (!meeting) return;
    setBusy(true);
    setError(null);
    try {
      setMeeting(await startProcessing(meeting.id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not start processing.");
    } finally {
      setBusy(false);
    }
  }, [meeting]);

  const reset = useCallback(() => {
    setMeeting(null);
    setError(null);
  }, []);

  useEffect(() => {
    if (!meeting || meeting.status !== "processing") return;
    let active = true;
    let timeout: number;
    const poll = async () => {
      try {
        const status = await getMeetingStatus(meeting.id);
        if (!active) return;
        if (status.status === "completed" || status.status === "failed") {
          setMeeting(await getMeeting(meeting.id));
          return;
        }
        setMeeting((current) =>
          current ? { ...current, progress: status.progress, current_stage: status.current_stage } : current,
        );
      } catch (reason) {
        if (active) setError(reason instanceof Error ? reason.message : "Could not refresh meeting status.");
      }
      if (active) timeout = window.setTimeout(poll, 1500);
    };
    timeout = window.setTimeout(poll, 700);
    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [meeting?.id, meeting?.status]);

  return { meeting, busy, error, upload, process, reset, clearError: () => setError(null) };
}
