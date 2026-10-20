import { createContext, useContext, useReducer, type Dispatch, type ReactNode } from "react";
import { editorReducer, initialState, type EditorAction, type EditorState } from "./editorState";

interface EditorContextValue {
  state: EditorState;
  dispatch: Dispatch<EditorAction>;
}

const EditorContext = createContext<EditorContextValue | null>(null);

export function EditorProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(editorReducer, initialState);
  return <EditorContext.Provider value={{ state, dispatch }}>{children}</EditorContext.Provider>;
}

export function useEditor(): EditorContextValue {
  const value = useContext(EditorContext);
  if (!value) throw new Error("useEditor debe usarse dentro de EditorProvider");
  return value;
}
