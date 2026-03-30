import * as React from "react";
import { useState } from "react";
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
import { ArrowSyncRegular, SlideTextRegular } from "@fluentui/react-icons";
import { extractSlides, getPresentationTitle } from "../services/slideExtractor";
import { apiClient } from "../services/apiClient";
import { RehearsalResponse } from "../types";

const useStyles = makeStyles({
  root: { display: "flex", flexDirection: "column", gap: "12px" },
  section: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    padding: "12px",
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: tokens.borderRadiusMedium,
    backgroundColor: tokens.colorNeutralBackground2,
  },
  row: { display: "flex", alignItems: "center", gap: "8px" },
  slideList: { display: "flex", flexDirection: "column", gap: "4px", maxHeight: "200px", overflowY: "auto" },
  slideItem: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "4px 8px",
    borderRadius: tokens.borderRadiusSmall,
    backgroundColor: tokens.colorNeutralBackground1,
    fontSize: "12px",
  },
});

interface Props {
  onRehearsalCreated: (rehearsal: RehearsalResponse) => void;
}

export default function DeckSync({ onRehearsalCreated }: Props) {
  const styles = useStyles();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [slideCount, setSlideCount] = useState<number | null>(null);
  const [health, setHealth] = useState<"unknown" | "ok" | "error">("unknown");

  const checkHealth = async () => {
    try {
      await apiClient.health();
      setHealth("ok");
    } catch {
      setHealth("error");
    }
  };

  const handleSync = async () => {
    setLoading(true);
    setError(null);
    try {
      // Check backend first
      await apiClient.health();
      setHealth("ok");

      const slides = await extractSlides();
      setSlideCount(slides.length);

      const title = getPresentationTitle();
      const rehearsal = await apiClient.createRehearsal(title, slides);
      onRehearsalCreated(rehearsal);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.root}>
      <Text weight="semibold" size={400}>Sync Your Deck</Text>
      <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
        Read your presentation slides and send them to the coaching backend.
      </Text>

      <div className={styles.section}>
        <div className={styles.row}>
          <Text size={200} weight="semibold">Backend Status:</Text>
          {health === "ok" && <Badge color="success" size="small">Connected</Badge>}
          {health === "error" && <Badge color="danger" size="small">Offline</Badge>}
          {health === "unknown" && <Badge color="informative" size="small">Unknown</Badge>}
          <Button size="small" appearance="subtle" onClick={checkHealth}>Check</Button>
        </div>
      </div>

      {slideCount !== null && (
        <div className={styles.section}>
          <div className={styles.row}>
            <SlideTextRegular />
            <Text size={300} weight="semibold">{slideCount} slides read</Text>
          </div>
          <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
            Slides synced successfully. Click "Record" tab to start your rehearsal.
          </Text>
        </div>
      )}

      {error && (
        <MessageBar intent="error">
          <MessageBarBody>{error}</MessageBarBody>
        </MessageBar>
      )}

      <Button
        appearance="primary"
        icon={loading ? <Spinner size="tiny" /> : <ArrowSyncRegular />}
        onClick={handleSync}
        disabled={loading}
      >
        {loading ? "Syncing…" : "Sync Deck & Start Session"}
      </Button>

      <Text size={100} style={{ color: tokens.colorNeutralForeground3 }}>
        Make sure the backend is running: <code>uvicorn app.main:app --reload</code>
      </Text>
    </div>
  );
}
