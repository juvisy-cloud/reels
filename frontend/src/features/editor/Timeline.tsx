import { useEditor } from "../../state/EditorContext";

const OUTRO_SECONDS = 2.5;

export function Timeline() {
  const { state, dispatch } = useEditor();
  const scenes = state.script?.scenes ?? [];
  const total = scenes.reduce((sum, scene) => sum + scene.seconds, 0) + OUTRO_SECONDS;

  if (scenes.length === 0) {
    return <footer className="timeline empty muted">Línea de tiempo · aún no hay escenas</footer>;
  }

  return (
    <footer className="timeline" aria-label="Línea de tiempo">
      <div className="timeline__track">
        {scenes.map((scene, index) => (
          <button
            key={index}
            type="button"
            className={`timeline__block ${state.selection === index ? "active" : ""}`}
            style={{ flexGrow: scene.seconds }}
            onClick={() => dispatch({ type: "select", selection: index })}
          >
            {index + 1} · {scene.seconds}s
          </button>
        ))}
        <button
          type="button"
          className={`timeline__block outro ${state.selection === "outro" ? "active" : ""}`}
          style={{ flexGrow: OUTRO_SECONDS }}
          onClick={() => dispatch({ type: "select", selection: "outro" })}
        >
          Cierre
        </button>
      </div>
      <div className="timeline__audio" title="Voz del avatar">
        🔊 Voz · ~{Math.round(total)}s en total (la duración final depende de la voz)
      </div>
    </footer>
  );
}
