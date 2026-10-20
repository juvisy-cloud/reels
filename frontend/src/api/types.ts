export type MediaKind = "photo" | "video";
export type JobStatus = "queued" | "running" | "done" | "failed";
export type RenderStage = "voice" | "avatar" | "background" | "compose" | "verify";

export interface Scene {
  narration: string;
  on_screen_text: string;
  seconds: number;
}

export interface Script {
  hook: string;
  scenes: Scene[];
  cta: string;
  pexels_queries: string[];
}

export interface Background {
  provider_id: number;
  kind: MediaKind;
  preview_url: string;
  download_url: string;
  width: number;
  height: number;
  author: string;
  author_url: string;
  duration_seconds: number | null;
}

export interface Voice {
  id: string;
  label: string;
}

export interface Job {
  id: string;
  status: JobStatus;
  stage: RenderStage | null;
  progress: number;
  error: string | null;
  output_file_id: string | null;
}

export interface ScriptBrief {
  context: string;
  tone: string;
  target_seconds: number;
  handle: string;
}

export interface Avatar {
  id: string;
  name: string;
  cutout_file_id: string;
  created_at: string;
}

export interface RenderRequest {
  avatar_id: string;
  script: Script;
  background: Background;
  voice: string;
  handle: string;
  logo_file_id: string | null;
  overlay_file_id: string | null;
}
