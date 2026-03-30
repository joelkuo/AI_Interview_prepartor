import * as React from "react";
import {
  makeStyles,
  tokens,
  Text,
  ProgressBar,
  Badge,
} from "@fluentui/react-components";
import { AnalysisStatus } from "../types";

const STEPS: { status: AnalysisStatus; label: string }[] = [
  { status: "transcribing", label: "Transcribing audio…" },
  { status: "analyzing_slides", label: "Analyzing slides…" },
  { status: "analyzing_speech", label: "Analyzing speech…" },
  { status: "analyzing_alignment", label: "Checking alignment…" },
  { status: "generating_summary", label: "Generating summary…" },
  { status: "complete", label: "Complete!" },
];

const STATUS_ORDER = STEPS.map((s) => s.status);

const useStyles = makeStyles({
  root: { display: "flex", flexDirection: "column", gap: "12px" },
  step: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    opacity: 0.4,
    transition: "opacity 0.2s",
  },
  activeStep: { opacity: 1 },
  doneStep: { opacity: 0.7 },
});

interface Props {
  status: AnalysisStatus;
}

export default function AnalysisProgress({ status }: Props) {
  const styles = useStyles();
  const currentIdx = STATUS_ORDER.indexOf(status);
  const progress = currentIdx >= 0 ? (currentIdx + 1) / STEPS.length : 0;

  const currentLabel = STEPS.find((s) => s.status === status)?.label || status;

  return (
    <div className={styles.root}>
      <Text weight="semibold">{currentLabel}</Text>
      <ProgressBar value={status === "complete" ? 1 : progress} />
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {STEPS.map((step, idx) => {
          const isDone = currentIdx > idx || status === "complete";
          const isActive = STATUS_ORDER[currentIdx] === step.status;
          return (
            <div
              key={step.status}
              className={`${styles.step} ${isActive ? styles.activeStep : ""} ${isDone ? styles.doneStep : ""}`}
            >
              <Badge
                size="small"
                color={isDone ? "success" : isActive ? "brand" : "informative"}
              >
                {idx + 1}
              </Badge>
              <Text size={200}>{step.label}</Text>
            </div>
          );
        })}
      </div>
    </div>
  );
}
