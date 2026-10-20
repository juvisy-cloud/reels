import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { EditorLayout } from "./features/editor/EditorLayout";
import { EditorProvider } from "./state/EditorContext";
import "./styles.css";

const root = document.getElementById("root");
if (!root) throw new Error("No se encontró #root");

createRoot(root).render(
  <StrictMode>
    <EditorProvider>
      <EditorLayout />
    </EditorProvider>
  </StrictMode>,
);
