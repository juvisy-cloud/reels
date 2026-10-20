import { api } from "../../api/client";
import type { Job, RenderStage } from "../../api/types";
import { useEditor } from "../../state/EditorContext";
import { missingRequirements } from "../../state/editorState";
import { useRenderJob } from "./useRenderJob";

const STAGE_LABELS: Record<RenderStage, string> = {
  voice: "Generando la voz",
  avatar: "Animando el avatar (la parte lenta)",
  background: "Descargando el fondo",
  compose: "Armando el video",
  verify: "Verificando el resultado",
};

function JobStatus({ job }: { job: Job }) {
  if (job.status === "failed") return <span className="error">No se pudo crear: {job.error}</span>;
  if (job.status === "done" && job.output_file_id) {
    return (
      <a className="secondary" href={api.fileUrl(job.output_file_id, true)}>
        ⬇ Descargar MP4
      </a>
    );
  }
  return (
    <div className="render__progress" role="status">
      <span>{job.stage ? STAGE_LABELS[job.stage] : "En cola…"}</span>
      <progress max={1} value={job.progress} />
      <span>{Math.round(job.progress * 100)}%</span>
    </div>
  );
}

export function RenderControls() {
  const { state } = useEditor();
  const { job, running, busy, error, start } = useRenderJob();
  const missing = missingRequirements(state);

  return (
    <div className="render">
      {job && <JobStatus job={job} />}
      {error && <span className="error">{error}</span>}
      <button
        type="button"
        className="primary"
        disabled={busy || running || missing.length > 0}
        title={missing.length ? `Falta: ${missing.join(", ")}` : "Generar el reel"}
        onClick={start}
      >
        {running ? "Generando…" : "🎬 Generar reel"}
      </button>
    </div>
  );
}
