import { RenderControls } from "../render/RenderControls";
import { Canvas } from "./Canvas";
import { SceneEditor } from "./SceneEditor";
import { ScenePanel } from "./ScenePanel";
import { Timeline } from "./Timeline";
import { ToolsPanel } from "./ToolsPanel";

export function EditorLayout() {
  return (
    <div className="editor">
      <header className="topbar">
        <div className="brand">
          <span className="brand__logo" aria-hidden>
            ▶
          </span>
          <strong>Reels Studio</strong>
          <span className="muted">· reel vertical 9:16</span>
        </div>
        <RenderControls />
      </header>
      <ScenePanel />
      <main className="stage">
        <Canvas />
        <SceneEditor />
      </main>
      <ToolsPanel />
      <Timeline />
    </div>
  );
}
