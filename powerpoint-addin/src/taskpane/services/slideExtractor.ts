import { SlideData } from "../types";

/* global Office */

export async function extractSlides(): Promise<SlideData[]> {
  return new Promise((resolve, reject) => {
    Office.context.document.getActiveViewAsync((_result) => {
      // Use PowerPoint API for slide extraction
      Office.context.document.getSelectedDataAsync(
        Office.CoercionType.SlideRange,
        {},
        () => {
          // Fall through to PowerPoint-specific API
        }
      );
    });

    // Use PowerPoint-specific API
    if (typeof PowerPoint !== "undefined" && PowerPoint.run) {
      PowerPoint.run(async (context) => {
        const slides = context.presentation.slides;
        slides.load("items");
        await context.sync();

        const results: SlideData[] = [];

        for (let i = 0; i < slides.items.length; i++) {
          const slide = slides.items[i];
          slide.shapes.load("items");
          await context.sync();

          let title = "";
          const contentParts: string[] = [];
          let notes = "";

          for (const shape of slide.shapes.items) {
            try {
              shape.textFrame.load("text");
              shape.load("name,placeholderType");
            } catch {
              // ignore shapes without text
            }
          }
          await context.sync();

          for (const shape of slide.shapes.items) {
            try {
              const text = shape.textFrame?.text?.trim() || "";
              if (!text) continue;

              // Detect title placeholder
              const name = (shape.name || "").toLowerCase();
              if (
                name.includes("title") ||
                shape.placeholderType === PowerPoint.PlaceholderType.title ||
                shape.placeholderType === PowerPoint.PlaceholderType.centeredTitle
              ) {
                title = text;
              } else {
                contentParts.push(text);
              }
            } catch {
              // shape has no text frame
            }
          }

          // Extract notes if API 1.3+ is supported
          try {
            if (Office.context.requirements.isSetSupported("PowerPointApi", "1.3")) {
              const notesSlide = slide.getNotesSlide();
              notesSlide.body.load("text");
              await context.sync();
              notes = notesSlide.body.text?.trim() || "";
            }
          } catch {
            // Notes not available
          }

          results.push({
            slide_number: i + 1,
            title,
            content: contentParts.join("\n"),
            notes,
          });
        }

        resolve(results);
      }).catch(reject);
    } else {
      // Fallback: try to get basic info via common API
      Office.context.document.getSelectedDataAsync(
        Office.CoercionType.Text,
        (result) => {
          if (result.status === Office.AsyncResultStatus.Succeeded) {
            resolve([{
              slide_number: 1,
              title: "Current Slide",
              content: result.value as string,
              notes: "",
            }]);
          } else {
            reject(new Error("Cannot read slides: PowerPoint API not available"));
          }
        }
      );
    }
  });
}

export function getPresentationTitle(): string {
  try {
    return Office.context.document.url?.split("/").pop()?.replace(/\.pptx?$/i, "") || "Untitled Presentation";
  } catch {
    return "Untitled Presentation";
  }
}
