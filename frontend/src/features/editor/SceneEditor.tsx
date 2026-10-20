import type { Scene, Script } from "../../api/types";
import { useEditor } from "../../state/EditorContext";

function TextOnlyEditor({ field, script }: { field: "hook" | "cta"; script: Script }) {
  const { dispatch } = useEditor();
  return (
    <label className="field">
      <span>{field === "hook" ? "Texto gancho (pantalla)" : "Llamada a la acción del cierre"}</span>
      <input
        maxLength={field === "hook" ? 80 : 120}
        value={script[field]}
        onChange={(e) => dispatch({ type: "updateScript", patch: { [field]: e.target.value } })}
      />
    </label>
  );
}

function SceneFields({ index, scene, removable }: { index: number; scene: Scene; removable: boolean }) {
  const { dispatch } = useEditor();
  const update = (patch: Partial<Scene>) => dispatch({ type: "updateScene", index, patch });
  return (
    <>
      <label className="field">
        <span>Lo que dice el avatar</span>
        <textarea rows={3} maxLength={400} value={scene.narration} onChange={(e) => update({ narration: e.target.value })} />
      </label>
      <div className="field-row">
        <label className="field">
          <span>Texto en pantalla</span>
          <input maxLength={60} value={scene.on_screen_text} onChange={(e) => update({ on_screen_text: e.target.value })} />
        </label>
        <label className="field narrow">
          <span>Segundos</span>
          <input type="number" min={1} max={20} value={scene.seconds} onChange={(e) => update({ seconds: Number(e.target.value) })} />
        </label>
        {removable && (
          <button type="button" className="link-button danger" onClick={() => dispatch({ type: "removeScene", index })}>
            Eliminar escena
          </button>
        )}
      </div>
    </>
  );
}

/** Edición del texto de la escena seleccionada, bajo el lienzo. */
export function SceneEditor() {
  const { state } = useEditor();
  const { script, selection } = state;
  if (!script) return null;
  const scene = typeof selection === "number" ? script.scenes[selection] : undefined;

  return (
    <div className="scene-editor">
      {selection === "hook" && <TextOnlyEditor field="hook" script={script} />}
      {selection === "outro" && <TextOnlyEditor field="cta" script={script} />}
      {typeof selection === "number" && scene && (
        <SceneFields index={selection} scene={scene} removable={script.scenes.length > 1} />
      )}
    </div>
  );
}
