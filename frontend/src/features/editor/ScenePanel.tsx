import { useEditor } from "../../state/EditorContext";
import { MAX_SCENES, type SceneSelection } from "../../state/editorState";

function SceneCard({ selection, title, text }: { selection: SceneSelection; title: string; text: string }) {
  const { state, dispatch } = useEditor();
  const active = state.selection === selection;
  return (
    <button
      type="button"
      className={`scene-card ${active ? "active" : ""}`}
      onClick={() => dispatch({ type: "select", selection })}
    >
      <span className="scene-card__title">{title}</span>
      <span className="scene-card__text">{text || "Sin texto"}</span>
    </button>
  );
}

export function ScenePanel() {
  const { state, dispatch } = useEditor();
  const script = state.script;

  if (!script) {
    return (
      <aside className="scenes empty">
        <p className="muted">Las escenas aparecerán aquí cuando generes el guion.</p>
        <button type="button" className="secondary" onClick={() => dispatch({ type: "setTool", tool: "script" })}>
          Escribir contexto
        </button>
      </aside>
    );
  }

  return (
    <aside className="scenes" aria-label="Escenas">
      <SceneCard selection="hook" title="Gancho" text={script.hook} />
      {script.scenes.map((scene, index) => (
        <SceneCard key={index} selection={index} title={`Escena ${index + 1}`} text={scene.narration} />
      ))}
      <SceneCard selection="outro" title="Cierre" text={script.cta} />
      {script.scenes.length < MAX_SCENES && (
        <button type="button" className="secondary" onClick={() => dispatch({ type: "addScene" })}>
          ＋ Escena
        </button>
      )}
    </aside>
  );
}
