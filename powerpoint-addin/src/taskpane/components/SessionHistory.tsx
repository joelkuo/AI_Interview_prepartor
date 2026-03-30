import * as React from "react";
import { useState, useEffect } from "react";
import {
  makeStyles,
  tokens,
  Text,
  Badge,
  Button,
  Spinner,
  MessageBar,
  MessageBarBody,
} from "@fluentui/react-components";
import { DeleteRegular } from "@fluentui/react-icons";
import { apiClient } from "../services/apiClient";
import { AnalysisResult, RehearsalResponse } from "../types";

const useStyles = makeStyles({
  root: { display: "flex", flexDirection: "column", gap: "8px" },
  item: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    padding: "10px 12px",
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: tokens.borderRadiusMedium,
    cursor: "pointer",
    backgroundColor: tokens.colorNeutralBackground1,
    ":hover": { backgroundColor: tokens.colorNeutralBackground2 },
  },
  itemRow: { display: "flex", alignItems: "center", gap: "8px" },
});

function statusColor(status: string): "success" | "warning" | "danger" | "informative" {
  if (status === "complete") return "success";
  if (status === "failed") return "danger";
  if (status === "pending") return "informative";
  return "warning";
}

interface Props {
  onSelect: (rehearsal: RehearsalResponse, result: AnalysisResult) => void;
}

export default function SessionHistory({ onSelect }: Props) {
  const styles = useStyles();
  const [rehearsals, setRehearsals] = useState<RehearsalResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiClient.listRehearsals();
      setRehearsals(data.rehearsals);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    setDeleting(id);
    try {
      await apiClient.deleteRehearsal(id);
      setRehearsals((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeleting(null);
    }
  };

  const handleSelect = async (rehearsal: RehearsalResponse) => {
    if (rehearsal.status !== "complete") return;
    try {
      const result = await apiClient.getResults(rehearsal.id);
      onSelect(rehearsal, result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load results");
    }
  };

  if (loading) return <div style={{ display: "flex", justifyContent: "center", padding: "24px" }}><Spinner /></div>;

  return (
    <div className={styles.root}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Text weight="semibold" size={400}>Session History</Text>
        <Button size="small" appearance="subtle" onClick={load}>Refresh</Button>
      </div>

      {error && (
        <MessageBar intent="error" onDismiss={() => setError(null)}>
          <MessageBarBody>{error}</MessageBarBody>
        </MessageBar>
      )}

      {rehearsals.length === 0 && (
        <Text size={200} style={{ color: tokens.colorNeutralForeground3, textAlign: "center", padding: "24px" }}>
          No rehearsal sessions yet. Sync your deck to get started.
        </Text>
      )}

      {rehearsals.map((r) => (
        <div
          key={r.id}
          className={styles.item}
          onClick={() => handleSelect(r)}
          role="button"
          tabIndex={0}
        >
          <div className={styles.itemRow}>
            <Text size={200} weight="semibold" style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {r.title}
            </Text>
            <Badge color={statusColor(r.status)} size="small">{r.status}</Badge>
            <Button
              size="small"
              appearance="subtle"
              icon={deleting === r.id ? <Spinner size="tiny" /> : <DeleteRegular />}
              onClick={(e) => handleDelete(e, r.id)}
              disabled={deleting === r.id}
            />
          </div>
          <Text size={100} style={{ color: tokens.colorNeutralForeground3 }}>
            {r.slide_count} slides · {new Date(r.created_at).toLocaleString()}
          </Text>
          {r.status === "complete" && (
            <Text size={100} style={{ color: tokens.colorBrandForeground1 }}>Click to view results →</Text>
          )}
        </div>
      ))}
    </div>
  );
}
