import { useEditor } from "../../state/EditorContext";
import type { Tool } from "../../state/editorState";
import { AvatarPanel } from "../avatar/AvatarPanel";
import { BackgroundPanel } from "../background/BackgroundPanel";
import { BrandPanel } from "../brand/BrandPanel";
import { ScriptPanel } from "../context/ScriptPanel";

const TOOLS: { id: Tool; icon: string; label: string }[] = [
  { id: "avatar", icon: "🧑", label: "Avatar" },
  { id: "script", icon: "✍️", label: "Guion" },
  { id: "background", icon: "🖼️", label: "Fondo" },
  { id: "brand", icon: "🏷️", label: "Marca" },
];

const PANELS: Record<Tool, () => JSX.Element> = {
  avatar: AvatarPanel,
  script: ScriptPanel,
  background: BackgroundPanel,
  brand: BrandPanel,
};

export function ToolsPanel() {
  const { state, dispatch } = useEditor();
  const Panel = PANELS[state.tool];
  return (
    <div className="tools">
      <div className="tools__panel">
        <Panel />
      </div>
      <nav className="tools__rail" aria-label="Herramientas">
        {TOOLS.map((tool) => (
          <button
            key={tool.id}
            type="button"
            className={state.tool === tool.id ? "active" : ""}
            aria-pressed={state.tool === tool.id}
            onClick={() => dispatch({ type: "setTool", tool: tool.id })}
          >
            <span aria-hidden>{tool.icon}</span>
            {tool.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
