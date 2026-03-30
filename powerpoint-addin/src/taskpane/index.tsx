import * as React from "react";
import { createRoot } from "react-dom/client";
import { FluentProvider, webLightTheme } from "@fluentui/react-components";
import App from "./components/App";

/* global Office */

const render = () => {
  const container = document.getElementById("root");
  if (!container) return;
  const root = createRoot(container);
  root.render(
    <FluentProvider theme={webLightTheme}>
      <App />
    </FluentProvider>
  );
};

Office.onReady(() => {
  render();
});
