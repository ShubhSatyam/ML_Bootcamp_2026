import Brand from "./components/Brand";
import ProcessingPage from "./pages/ProcessingPage";
import ResultsPage from "./pages/ResultsPage";
import UploadPage from "./pages/UploadPage";
import { useMeeting } from "./hooks/useMeeting";

export default function App() {
  const meetingState = useMeeting();
  const { meeting } = meetingState;
  return (
    <div className="app-shell">
      <header className="site-header"><Brand /><div className="header-note"><span /> Your thoughtful meeting companion</div></header>
      {meeting?.status === "processing" || meeting?.status === "failed" ? (
        <ProcessingPage
          meeting={meeting}
          error={meetingState.error}
          busy={meetingState.busy}
          onRetry={meetingState.process}
          onNewMeeting={meetingState.reset}
        />
      ) : meeting?.status === "completed" ? (
        <ResultsPage meeting={meeting} onNewMeeting={meetingState.reset} />
      ) : (
        <UploadPage
          meeting={meeting}
          busy={meetingState.busy}
          error={meetingState.error}
          onUpload={meetingState.upload}
          onProcess={meetingState.process}
          onReset={meetingState.reset}
          onClearError={meetingState.clearError}
        />
      )}
      <div className="page-footer"><span>BRIEFLY · MEETING NOTES THAT MOVE YOU FORWARD</span><span>PRIVATE BY DESIGN <i>·</i> BUILT FOR CLARITY</span></div>
    </div>
  );
}
