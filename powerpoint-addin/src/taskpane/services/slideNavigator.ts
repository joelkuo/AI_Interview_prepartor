/* global Office PowerPoint */

export async function goToSlide(slideNumber: number): Promise<void> {
  if (typeof PowerPoint !== "undefined" && PowerPoint.run) {
    await PowerPoint.run(async (context) => {
      const slides = context.presentation.slides;
      slides.load("items");
      await context.sync();

      const idx = slideNumber - 1;
      if (idx >= 0 && idx < slides.items.length) {
        slides.items[idx].setSelectedSlides();
        await context.sync();
      }
    });
  } else {
    // Fallback: use goToByIdAsync
    Office.context.document.goToByIdAsync(
      slideNumber.toString(),
      Office.GoToType.Slide,
      () => {}
    );
  }
}
