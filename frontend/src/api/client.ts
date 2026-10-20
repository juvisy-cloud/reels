import type { Avatar, Background, Job, MediaKind, RenderRequest, Script, ScriptBrief, Voice } from "./types";

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    const detail = typeof body?.detail === "string" ? body.detail : "Algo salió mal, intenta de nuevo.";
    throw new ApiError(detail);
  }
  return (await response.json()) as T;
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  uploadImage(file: File): Promise<{ file_id: string }> {
    const form = new FormData();
    form.append("file", file);
    return request("/api/uploads", { method: "POST", body: form });
  },
  listAvatars: (): Promise<Avatar[]> => request("/api/avatars"),
  createAvatar: (photoFileId: string, name: string): Promise<Avatar> =>
    request("/api/avatars", json({ photo_file_id: photoFileId, name })),
  async deleteAvatar(avatarId: string): Promise<void> {
    const response = await fetch(`/api/avatars/${encodeURIComponent(avatarId)}`, { method: "DELETE" });
    if (!response.ok) throw new ApiError("No se pudo borrar el avatar.");
  },
  generateScript: (brief: ScriptBrief): Promise<Script> => request("/api/scripts", json(brief)),
  searchBackgrounds(query: string, kind: MediaKind): Promise<Background[]> {
    const params = new URLSearchParams({ query, kind });
    return request(`/api/backgrounds?${params.toString()}`);
  },
  voices: (): Promise<Voice[]> => request("/api/voices"),
  submitRender: (body: RenderRequest): Promise<Job> => request("/api/renders", json(body)),
  fileUrl: (fileId: string, download = false): string =>
    `/api/files/${encodeURIComponent(fileId)}${download ? "?download=true" : ""}`,
  subscribeToJob(jobId: string, onUpdate: (job: Job) => void): () => void {
    const source = new EventSource(`/api/renders/${encodeURIComponent(jobId)}/events`);
    source.onmessage = (event: MessageEvent<string>) => {
      const job = JSON.parse(event.data) as Job;
      onUpdate(job);
      if (job.status === "done" || job.status === "failed") source.close();
    };
    return () => source.close();
  },
};
