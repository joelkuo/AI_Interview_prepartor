import * as React from "react";
import { useState } from "react";
import {
  makeStyles,
  tokens,
  Text,
  Badge,
  ProgressBar,
  Button,
  Accordion,
  AccordionItem,
  AccordionHeader,
  AccordionPanel,
  Tab,
  TabList,
  SelectTabData,
} from "@fluentui/react-components";
import { ArrowDownloadRegular } from "@fluentui/react-icons";
import SlideCard from "./SlideCard";
import { AnalysisResult } from "../types";
import { apiClient } from "../services/apiClient";

const useStyles = makeStyles({
  root: { display: "flex", flexDirection: "column", gap: "12px" },
  scoreCard: {
    padding: "16px",
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: tokens.borderRadiusMedium,
    backgroundColor: tokens.colorNeutralBackground2,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "8px",
  },
  bigScore: {
    fontSize: "48px",
    fontWeight: "700",
    lineHeight: "1",
  },
  statsRow: {
    display: "flex",
    gap: "12px",
    flexWrap: "wrap",
  },
  statBox: {
    flex: "1 1 80px",
    padding: "8px",
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: tokens.borderRadiusMedium,
    textAlign: "center",
    backgroundColor: tokens.colorNeutralBackground1,
  },
  list: { display: "flex", flexDirection: "column", gap: "6px" },
  listItem: { display: "flex", gap: "8px", fontSize: "13px", alignItems: "flex-start" },
});

function scoreToColor(score: number) {
  if (score >= 75) return tokens.colorPaletteGreenForeground1;
  if (score >= 50) return tokens.colorPaletteYellowForeground2;
  return tokens.colorPaletteRedForeground1;
}

type FeedbackTab = "overview" | "slides" | "speech" | "transcript";

interface Props {
  result: AnalysisResult;
}

export default function FeedbackDashboard({ result }: Props) {
  const styles = useStyles();
  const [tab, setTab] = useState<FeedbackTab>("overview");
  const overall = result.overall;
  const speech = result.speech;
  const slides = [...result.slides].sort((a, b) => a.score - b.score);

  const handleExport = () => {
    window.open(apiClient.getExportUrl(result.rehearsal_id), "_blank");
  };

  return (
    <div className={styles.root}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Text weight="semibold" size={400}>Coaching Results</Text>
        <Button size="small" icon={<ArrowDownloadRegular />} appearance="subtle" onClick={handleExport}>
          Export
        </Button>
      </div>

      {overall && (
        <div className={styles.scoreCard}>
          <div className={styles.bigScore} style={{ color: scoreToColor(overall.overall_score) }}>
            {overall.overall_score}
          </div>
          <Text size={200} weight="semibold">Overall Score</Text>
          <ProgressBar value={overall.overall_score / 100} style={{ width: "100%" }} />
          <Text size={200} style={{ textAlign: "center", color: tokens.colorNeutralForeground2 }}>
            {overall.headline}
          </Text>
        </div>
      )}

      <div className={styles.statsRow}>
        {speech && (
          <div className={styles.statBox}>
            <Text size={300} weight="semibold" style={{ color: scoreToColor(speech.score) }}>
              {Math.round(speech.wpm)}
            </Text>
            <Text size={100} block>WPM</Text>
          </div>
        )}
        {speech && (
          <div className={styles.statBox}>
            <Text size={300} weight="semibold">{speech.filler_word_count}</Text>
            <Text size={100} block>Fillers</Text>
          </div>
        )}
        {result.alignment && (
          <div className={styles.statBox}>
            <Text size={300} weight="semibold">{result.alignment.coverage_percentage}%</Text>
            <Text size={100} block>Coverage</Text>
          </div>
        )}
        <div className={styles.statBox}>
          <Text size={300} weight="semibold">{slides.length}</Text>
          <Text size={100} block>Slides</Text>
        </div>
      </div>

      <TabList
        selectedValue={tab}
        onTabSelect={(_e, data: SelectTabData) => setTab(data.value as FeedbackTab)}
        size="small"
      >
        <Tab value="overview">Overview</Tab>
        <Tab value="slides">Slides</Tab>
        <Tab value="speech">Speech</Tab>
        {result.transcript && <Tab value="transcript">Transcript</Tab>}
      </TabList>

      {tab === "overview" && overall && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <Accordion collapsible defaultOpenItems="strengths">
            <AccordionItem value="strengths">
              <AccordionHeader>Top Strengths</AccordionHeader>
              <AccordionPanel>
                <div className={styles.list}>
                  {overall.top_strengths.map((s, i) => (
                    <div key={i} className={styles.listItem}>
                      <span>✅</span><Text size={200}>{s}</Text>
                    </div>
                  ))}
                </div>
              </AccordionPanel>
            </AccordionItem>
            <AccordionItem value="improve">
              <AccordionHeader>Top Improvements</AccordionHeader>
              <AccordionPanel>
                <div className={styles.list}>
                  {overall.top_improvements.map((s, i) => (
                    <div key={i} className={styles.listItem}>
                      <span>🎯</span><Text size={200}>{s}</Text>
                    </div>
                  ))}
                </div>
              </AccordionPanel>
            </AccordionItem>
            <AccordionItem value="next">
              <AccordionHeader>Next Steps</AccordionHeader>
              <AccordionPanel>
                <div className={styles.list}>
                  {overall.next_steps.map((s, i) => (
                    <div key={i} className={styles.listItem}>
                      <span>→</span><Text size={200}>{s}</Text>
                    </div>
                  ))}
                </div>
              </AccordionPanel>
            </AccordionItem>
          </Accordion>
        </div>
      )}

      {tab === "slides" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
            Sorted by score (worst first)
          </Text>
          {slides.map((sf) => (
            <SlideCard key={sf.slide_number} feedback={sf} />
          ))}
        </div>
      )}

      {tab === "speech" && speech && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div className={styles.scoreCard}>
            <Badge color={speech.score >= 75 ? "success" : speech.score >= 50 ? "warning" : "danger"} size="large">
              Speech Score: {speech.score}/100
            </Badge>
            <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>{speech.summary}</Text>
          </div>
          <Text size={200} weight="semibold">Filler Words Detected:</Text>
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {Object.entries(speech.filler_words_detail).map(([word, count]) => (
              <Badge key={word} color="warning" size="medium">"{word}" ×{count}</Badge>
            ))}
            {Object.keys(speech.filler_words_detail).length === 0 && (
              <Badge color="success">No filler words detected!</Badge>
            )}
          </div>
          {speech.issues.length > 0 && (
            <>
              <Text size={200} weight="semibold">Issues:</Text>
              <div className={styles.list}>
                {speech.issues.map((i, idx) => (
                  <div key={idx} className={styles.listItem}><span>⚠</span><Text size={200}>{i}</Text></div>
                ))}
              </div>
            </>
          )}
          {speech.suggestions.length > 0 && (
            <>
              <Text size={200} weight="semibold">Suggestions:</Text>
              <div className={styles.list}>
                {speech.suggestions.map((s, idx) => (
                  <div key={idx} className={styles.listItem}><span>→</span><Text size={200}>{s}</Text></div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {tab === "transcript" && result.transcript && (
        <div style={{ padding: "8px", backgroundColor: tokens.colorNeutralBackground2, borderRadius: tokens.borderRadiusMedium }}>
          <Text size={200} style={{ whiteSpace: "pre-wrap", lineHeight: "1.6" }}>{result.transcript}</Text>
        </div>
      )}
    </div>
  );
}
