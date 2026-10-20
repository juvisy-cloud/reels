import { api } from "../../api/client";
import { useEditor } from "../../state/EditorContext";
import type { EditorState } from "../../state/editorState";

function captionFor(state: EditorState): string {
  const { script, selection } = state;
  if (!script) return "Tu reel aparecerá aquí";
  if (selection === "hook") return script.hook;
  if (selection === "outro") return script.cta;
  return script.scenes[selection]?.on_screen_text ?? "";
}

function OutroPreview({ state }: { state: EditorState }) {
  return (
    <div className="canvas__outro">
      {state.logo && <img src={state.logo.previewUrl} alt="Logo" />}
      <strong>{state.script?.cta}</strong>
      {state.brief.handle && <span>Instagram: {state.brief.handle}</span>}
    </div>
  );
}

function ScenePreview({ state }: { state: EditorState }) {
  const overlay = state.selection === 1 ? state.overlay : null;
  return (
    <>
      {state.background && <img className="canvas__bg" src={state.background.preview_url} alt="" />}
      <div className="canvas__caption">{captionFor(state)}</div>
      {overlay && <img className="canvas__phone" src={overlay.previewUrl} alt="Captura" />}
      {state.avatar && (
        <img className="canvas__avatar" src={api.fileUrl(state.avatar.cutout_file_id)} alt={state.avatar.name} />
      )}
    </>
  );
}

export function Canvas() {
  const { state } = useEditor();
  const outputId = state.job?.status === "done" ? state.job.output_file_id : null;

  return (
    <div className="canvas" aria-label="Vista previa 9:16">
      {outputId ? (
        <video className="canvas__video" src={api.fileUrl(outputId)} controls autoPlay playsInline />
      ) : state.selection === "outro" ? (
        <OutroPreview state={state} />
      ) : (
        <ScenePreview state={state} />
      )}
    </div>
  );
}
