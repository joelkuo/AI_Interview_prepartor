import * as React from "react";
import { useState, useCallback } from "react";
import {
  makeStyles,
  tokens,
  Text,
  Tab,
  TabList,
  SelectTabData,
} from "@fluentui/react-components";
import {
  SlideTextRegular,
  MicRegular,
  StarRegular,
  HistoryRegular,
} from "@fluentui/react-icons";
import DeckSync from "./DeckSync";
import RecordingPanel from "./RecordingPanel";
import FeedbackDashboard from "./FeedbackDashboard";
import SessionHistory from "./SessionHistory";
import { ActiveTab, AnalysisResult, RehearsalResponse } from "../types";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    overflow: "hidden",
    backgroundColor: tokens.colorNeutralBackground1,
  },
  header: {
    padding: "12px 16px 0",
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
  },
  headerTitle: {
    display: "block",
    fontSize: "16px",
    fontWeight: "600",
    paddingBottom: "8px",
  },
  tabList: {
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    padding: "0 8px",
  },
  content: {
    flex: 1,
    overflow: "auto",
    padding: "12px 16px",
  },
});

export default function App() {
  const styles = useStyles();
  const [activeTab, setActiveTab] = useState<ActiveTab>("sync");
  const [currentRehearsal, setCurrentRehearsal] = useState<RehearsalResponse | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  const handleRehearsalCreated = useCallback((rehearsal: RehearsalResponse) => {
    setCurrentRehearsal(rehearsal);
    setActiveTab("record");
  }, []);

  const handleAnalysisComplete = useCallback((result: AnalysisResult) => {
    setAnalysisResult(result);
    setActiveTab("results");
  }, []);

  const handleSelectHistory = useCallback((rehearsal: RehearsalResponse, result: AnalysisResult) => {
    setCurrentRehearsal(rehearsal);
    setAnalysisResult(result);
    setActiveTab("results");
  }, []);

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <Text className={styles.headerTitle}>🎤 Presentation Coach</Text>
      </div>

      <TabList
        className={styles.tabList}
        selectedValue={activeTab}
        onTabSelect={(_e, data: SelectTabData) => setActiveTab(data.value as ActiveTab)}
        size="small"
      >
        <Tab value="sync" icon={<SlideTextRegular />}>Slides</Tab>
        <Tab value="record" icon={<MicRegular />} disabled={!currentRehearsal}>Record</Tab>
        <Tab value="results" icon={<StarRegular />} disabled={!analysisResult}>Results</Tab>
        <Tab value="history" icon={<HistoryRegular />}>History</Tab>
      </TabList>

      <div className={styles.content}>
        {activeTab === "sync" && (
          <DeckSync onRehearsalCreated={handleRehearsalCreated} />
        )}
        {activeTab === "record" && currentRehearsal && (
          <RecordingPanel
            rehearsal={currentRehearsal}
            onAnalysisComplete={handleAnalysisComplete}
          />
        )}
        {activeTab === "results" && analysisResult && (
          <FeedbackDashboard result={analysisResult} />
        )}
        {activeTab === "history" && (
          <SessionHistory onSelect={handleSelectHistory} />
        )}
      </div>
    </div>
  );
}
