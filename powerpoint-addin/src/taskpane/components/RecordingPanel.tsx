import * as React from "react";
import { useState, useRef, useCallback } from "react";
import {
  Button,
  Text,
  makeStyles,
  tokens,
  Spinner,
  MessageBar,
  MessageBarBody,
  Badge,
} from "@fluentui/react-components";
import {
  MicRegular,
  StopRegular,
  PauseRegular,
  PlayRegular,
  ArrowUploadRegular,
} from "@fluentui/react-icons";
import { AudioRecorder } from "../services/audioRecorder";
import { apiClient } from "../services/apiClient";
import AnalysisProgress from "./AnalysisProgress";
import { usePolling } from "../hooks/usePolling";
import { AnalysisResult, AnalysisStatus, RehearsalResponse } from "../types";

const useStyles = makeStyles({
  root: { display: "flex", flexDirection: "column", gap: "12px" },
  controls: { display: "flex", gap: "8px", flexWrap: "wrap" },
  timer: {
    fontFamily: "monospace",
    fontSize: "24px",
    fontWeight: "600",
    color: tokens.colorBrandForeground1,
    textAlign: "center",
    padding: "8px 0",
  },
  section: {
    padding: "12px",
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: tokens.borderRadiusMedium,
    backgroundColor: tokens.colorNeutralBackground2,
  },
  uploadRow: { display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" },
});

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

interface Props {
  rehearsal: RehearsalResponse;
  onAnalysisComplete: (result: AnalysisResult) => void;
}

export default function RecordingPanel({ rehearsal, onAnalysisComplete }: Props) {
  const styles = useStyles();
  const recorderRef = useRef(new AudioRecorder());
  const [recState, setRecState] = useState<"idle" | "recording" | "paused" | "stopped">("idle");
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [uploading, setUploading] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startTimer = () => {
    timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);
  };
  const stopTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const handleStart = async () => {
    setError(null);
    setElapsed(0);
    try {
      await recorderRef.current.start(setRecState);
      startTimer();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Microphone access denied");
    }
  };

  const handlePause = () => {
    recorderRef.current.pause();
    stopTimer();
  };

  const handleResume = () => {
    recorderRef.current.resume();
    startTimer();
  };

  const handleStop = async () => {
    stopTimer();
    const blob = await recorderRef.current.stop();
    setAudioBlob(blob);
  };

  const handleUploadAndAnalyze = async (blob: Blob) => {
    setUploading(true);
    setError(null);
    try {
      const ext = AudioRecorder.getExtension(blob);
      await apiClient.uploadAudio(rehearsal.id, blob, `recording${ext}`);
      await apiClient.startAnalysis(rehearsal.id);
      setAnalysisStatus("transcribing");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      await apiClient.uploadAudio(rehearsal.id, file, file.name);
      await apiClient.startAnalysis(rehearsal.id);
      setAnalysisStatus("transcribing");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const pollResults = useCallback(async (id: number) => {
    const result = await apiClient.getResults(id);
    setAnalysisStatus(result.status);
    if (result.status === "complete") {
      onAnalysisComplete(result);
    }
  }, [onAnalysisComplete]);

  usePolling(
    analysisStatus && !["complete", "failed", null].includes(analysisStatus) ? rehearsal.id : null,
    analysisStatus,
    pollResults,
  );

  const isRecording = recState === "recording";
  const isPaused = recState === "paused";
  const isStopped = recState === "stopped";
  const isAnalyzing = analysisStatus && !["complete", "failed"].includes(analysisStatus);

  return (
    <div className={styles.root}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Text weight="semibold" size={400}>Record Your Rehearsal</Text>
        <Badge color="informative" size="small">#{rehearsal.id}</Badge>
      </div>

      <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
        {rehearsal.title} · {rehearsal.slide_count} slides
      </Text>

      {!analysisStatus && (
        <>
          {/* Timer */}
          {(isRecording || isPaused || isStopped) && (
            <div className={styles.timer}>{formatTime(elapsed)}</div>
          )}

          {/* Recording controls */}
          <div className={styles.controls}>
            {recState === "idle" && (
              <Button appearance="primary" icon={<MicRegular />} onClick={handleStart}>
                Start Recording
              </Button>
            )}
            {isRecording && (
              <>
                <Button icon={<PauseRegular />} onClick={handlePause}>Pause</Button>
                <Button appearance="subtle" icon={<StopRegular />} onClick={handleStop}>Stop</Button>
              </>
            )}
            {isPaused && (
              <>
                <Button appearance="primary" icon={<PlayRegular />} onClick={handleResume}>Resume</Button>
                <Button icon={<StopRegular />} onClick={handleStop}>Stop</Button>
              </>
            )}
          </div>

          {/* Upload recorded blob */}
          {isStopped && audioBlob && (
            <div className={styles.section}>
              <Text size={200} weight="semibold">Recording ready ({(audioBlob.size / 1024 / 1024).toFixed(1)} MB)</Text>
              <Button
                appearance="primary"
                icon={uploading ? <Spinner size="tiny" /> : <ArrowUploadRegular />}
                disabled={uploading}
                onClick={() => handleUploadAndAnalyze(audioBlob)}
                style={{ marginTop: "8px" }}
              >
                {uploading ? "Uploading…" : "Upload & Analyze"}
              </Button>
            </div>
          )}

          {/* File upload fallback */}
          {recState === "idle" && (
            <div className={styles.section}>
              <Text size={200} weight="semibold">Or upload an audio file</Text>
              <div className={styles.uploadRow} style={{ marginTop: "8px" }}>
                <input
                  type="file"
                  accept="audio/*,.webm,.mp3,.wav,.ogg,.m4a"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  style={{ fontSize: "12px" }}
                />
                {uploading && <Spinner size="tiny" />}
              </div>
              {!AudioRecorder.isSupported() && (
                <Text size={100} style={{ color: tokens.colorPaletteYellowForeground2, marginTop: "4px" }}>
                  In-browser recording not available in this WebView. Use file upload.
                </Text>
              )}
            </div>
          )}
        </>
      )}

      {/* Analysis progress */}
      {isAnalyzing && analysisStatus && (
        <div className={styles.section}>
          <AnalysisProgress status={analysisStatus} />
        </div>
      )}

      {analysisStatus === "failed" && (
        <MessageBar intent="error">
          <MessageBarBody>Analysis failed. Please try again.</MessageBarBody>
        </MessageBar>
      )}

      {error && (
        <MessageBar intent="error">
          <MessageBarBody>{error}</MessageBarBody>
        </MessageBar>
      )}
    </div>
  );
}
