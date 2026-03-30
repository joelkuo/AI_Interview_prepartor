import { useEffect, useRef, useCallback } from "react";
import { AnalysisStatus } from "../types";

const TERMINAL_STATES: AnalysisStatus[] = ["complete", "failed"];

export function usePolling(
  rehearsalId: number | null,
  currentStatus: AnalysisStatus | null,
  onPoll: (id: number) => Promise<void>,
  intervalMs = 3000
) {
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isPolling = rehearsalId !== null && currentStatus !== null && !TERMINAL_STATES.includes(currentStatus);

  const poll = useCallback(async () => {
    if (rehearsalId !== null) {
      await onPoll(rehearsalId);
    }
  }, [rehearsalId, onPoll]);

  useEffect(() => {
    if (!isPolling) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    timerRef.current = setInterval(poll, intervalMs);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPolling, poll, intervalMs]);
}
