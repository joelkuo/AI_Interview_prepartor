import * as React from "react";
import {
  makeStyles,
  tokens,
  Text,
  Badge,
  Button,
  Accordion,
  AccordionItem,
  AccordionHeader,
  AccordionPanel,
} from "@fluentui/react-components";
import { NavigationRegular } from "@fluentui/react-icons";
import { SlideFeedback } from "../types";
import { goToSlide } from "../services/slideNavigator";

const useStyles = makeStyles({
  card: {
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: tokens.borderRadiusMedium,
    overflow: "hidden",
    backgroundColor: tokens.colorNeutralBackground1,
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "8px 12px",
    backgroundColor: tokens.colorNeutralBackground2,
  },
  score: {
    marginLeft: "auto",
    fontWeight: "600",
    fontSize: "14px",
  },
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    paddingLeft: "0",
    margin: "0",
  },
  listItem: {
    display: "flex",
    gap: "6px",
    fontSize: "12px",
    alignItems: "flex-start",
  },
  bullet: { flexShrink: 0, marginTop: "2px" },
});

function scoreColor(score: number): "success" | "warning" | "danger" {
  if (score >= 75) return "success";
  if (score >= 50) return "warning";
  return "danger";
}

interface Props {
  feedback: SlideFeedback;
}

export default function SlideCard({ feedback }: Props) {
  const styles = useStyles();
  const color = scoreColor(feedback.score);

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <Text size={200} weight="semibold">Slide {feedback.slide_number}</Text>
        <Button
          size="small"
          appearance="subtle"
          icon={<NavigationRegular />}
          onClick={() => goToSlide(feedback.slide_number)}
        >
          Go to slide
        </Button>
        <Badge color={color} size="medium" className={styles.score}>
          {feedback.score}/100
        </Badge>
      </div>

      <Accordion collapsible>
        <AccordionItem value="detail">
          <AccordionHeader size="small">
            <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
              {feedback.summary}
            </Text>
          </AccordionHeader>
          <AccordionPanel>
            <div style={{ padding: "8px 12px", display: "flex", flexDirection: "column", gap: "10px" }}>
              {feedback.issues.length > 0 && (
                <div>
                  <Text size={100} weight="semibold" style={{ color: tokens.colorPaletteRedForeground1 }}>
                    Issues
                  </Text>
                  <ul className={styles.list}>
                    {feedback.issues.map((issue, i) => (
                      <li key={i} className={styles.listItem}>
                        <span className={styles.bullet}>⚠</span>
                        <Text size={200}>{issue}</Text>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {feedback.suggestions.length > 0 && (
                <div>
                  <Text size={100} weight="semibold" style={{ color: tokens.colorBrandForeground1 }}>
                    Suggestions
                  </Text>
                  <ul className={styles.list}>
                    {feedback.suggestions.map((sug, i) => (
                      <li key={i} className={styles.listItem}>
                        <span className={styles.bullet}>→</span>
                        <Text size={200}>{sug}</Text>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {feedback.strengths.length > 0 && (
                <div>
                  <Text size={100} weight="semibold" style={{ color: tokens.colorPaletteGreenForeground1 }}>
                    Strengths
                  </Text>
                  <ul className={styles.list}>
                    {feedback.strengths.map((str, i) => (
                      <li key={i} className={styles.listItem}>
                        <span className={styles.bullet}>✓</span>
                        <Text size={200}>{str}</Text>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </AccordionPanel>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
