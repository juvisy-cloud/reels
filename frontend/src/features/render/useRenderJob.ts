import { useEffect } from "react";
import { api } from "../../api/client";
import type { RenderRequest } from "../../api/types";
import { useEditor } from "../../state/EditorContext";
import type { EditorState } from "../../state/editorState";
import { useAsync } from "../../ui/useAsync";

export function buildRequest(state: EditorState): RenderRequest | null {
  if (!state.avatar || !state.script || !state.background) return null;
  return {
    avatar_id: state.avatar.id,
    script: state.script,
    background: state.background,
    voice: state.voice,
    handle: state.brief.handle,
    logo_file_id: state.logo?.fileId ?? null,
    overlay_file_id: state.overlay?.fileId ?? null,
  };
}

/** Envía el render y escucha su progreso por SSE hasta que termine. */
export function useRenderJob() {
  const { state, dispatch } = useEditor();
  const { busy, error, run } = useAsync();
  const job = state.job;
  const running = job?.status === "queued" || job?.status === "running";
  const jobId = running ? job.id : null;

  useEffect(() => {
    if (!jobId) return;
    return api.subscribeToJob(jobId, (update) => dispatch({ type: "setJob", job: update }));
  }, [jobId, dispatch]);

  const start = async () => {
    const body = buildRequest(state);
    if (!body) return;
    const created = await run(() => api.submitRender(body));
    if (created) dispatch({ type: "setJob", job: created });
  };

  return { job, running, busy, error, start };
}
