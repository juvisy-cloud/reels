import type { Avatar, Background, Job, Scene, Script, ScriptBrief } from "../api/types";

export interface UploadedImage {
  fileId: string;
  previewUrl: string;
}

export type Tool = "avatar" | "script" | "background" | "brand";
export type SceneSelection = "hook" | "outro" | number;

export interface EditorState {
  avatar: Avatar | null;
  logo: UploadedImage | null;
  overlay: UploadedImage | null;
  brief: ScriptBrief;
  script: Script | null;
  background: Background | null;
  voice: string;
  tool: Tool;
  selection: SceneSelection;
  job: Job | null;
}

export type EditorAction =
  | { type: "setImage"; slot: "logo" | "overlay"; image: UploadedImage | null }
  | { type: "setAvatar"; avatar: Avatar | null }
  | { type: "updateBrief"; patch: Partial<ScriptBrief> }
  | { type: "setScript"; script: Script }
  | { type: "updateScene"; index: number; patch: Partial<Scene> }
  | { type: "updateScript"; patch: Partial<Omit<Script, "scenes">> }
  | { type: "addScene" }
  | { type: "removeScene"; index: number }
  | { type: "setBackground"; background: Background }
  | { type: "setVoice"; voice: string }
  | { type: "setTool"; tool: Tool }
  | { type: "select"; selection: SceneSelection }
  | { type: "setJob"; job: Job | null };

export const MAX_SCENES = 4;

export const initialState: EditorState = {
  avatar: null,
  logo: null,
  overlay: null,
  brief: { context: "", tone: "cercano y profesional", target_seconds: 15, handle: "" },
  script: null,
  background: null,
  voice: "em_alex",
  tool: "avatar",
  selection: "hook",
  job: null,
};

const emptyScene: Scene = { narration: "", on_screen_text: "", seconds: 4 };

function withScenes(state: EditorState, scenes: Scene[]): EditorState {
  return state.script ? { ...state, script: { ...state.script, scenes } } : state;
}

type Handlers = {
  [K in EditorAction["type"]]: (state: EditorState, action: Extract<EditorAction, { type: K }>) => EditorState;
};

const scenesOf = (state: EditorState): Scene[] => state.script?.scenes ?? [];

// Mapa de manejadores (en lugar de un switch gigante): cada acción es una función pequeña.
const handlers: Handlers = {
  setImage: (state, action) => ({ ...state, [action.slot]: action.image }),
  setAvatar: (state, action) => ({ ...state, avatar: action.avatar }),
  updateBrief: (state, action) => ({ ...state, brief: { ...state.brief, ...action.patch } }),
  setScript: (state, action) => ({ ...state, script: action.script, selection: "hook" }),
  updateScript: (state, action) => (state.script ? { ...state, script: { ...state.script, ...action.patch } } : state),
  updateScene: (state, action) =>
    withScenes(state, scenesOf(state).map((s, i) => (i === action.index ? { ...s, ...action.patch } : s))),
  addScene: (state) => (scenesOf(state).length >= MAX_SCENES ? state : withScenes(state, [...scenesOf(state), emptyScene])),
  removeScene: (state, action) =>
    scenesOf(state).length <= 1
      ? state
      : { ...withScenes(state, scenesOf(state).filter((_, i) => i !== action.index)), selection: "hook" },
  setBackground: (state, action) => ({ ...state, background: action.background }),
  setVoice: (state, action) => ({ ...state, voice: action.voice }),
  setTool: (state, action) => ({ ...state, tool: action.tool }),
  select: (state, action) => ({ ...state, selection: action.selection }),
  setJob: (state, action) => ({ ...state, job: action.job }),
};

export function editorReducer(state: EditorState, action: EditorAction): EditorState {
  const handler = handlers[action.type] as (s: EditorState, a: EditorAction) => EditorState;
  return handler(state, action);
}

export function missingRequirements(state: EditorState): string[] {
  const missing: string[] = [];
  if (!state.avatar) missing.push("elige o crea un avatar");
  if (!state.script) missing.push("genera o escribe el guion");
  if (!state.background) missing.push("elige un fondo de Pexels");
  return missing;
}
