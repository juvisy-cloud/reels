import { api } from "../../api/client";
import { useEditor } from "../../state/EditorContext";
import { useAsync } from "../../ui/useAsync";

const MAX_CONTEXT = 1500;
const TONES = ["cercano y profesional", "energético y divertido", "inspirador", "serio y experto"];

export function ScriptPanel() {
  const { state, dispatch } = useEditor();
  const { busy, error, run } = useAsync();
  const { brief } = state;

  const generate = async () => {
    const script = await run(() => api.generateScript(brief));
    if (script) {
      dispatch({ type: "setScript", script });
      dispatch({ type: "setTool", tool: "background" });
    }
  };

  return (
    <section className="panel-section">
      <h2>Contexto del reel</h2>
      <p className="muted">Cuéntale al agente de qué trata el reel. Él escribe el guion y tú lo ajustas.</p>
      <label className="field">
        <span>¿De qué trata?</span>
        <textarea
          rows={7}
          maxLength={MAX_CONTEXT}
          placeholder="Ej: Promociona el agendador de citas de Juvisy: tus clientes agendan por chat, sin llamadas."
          value={brief.context}
          onChange={(e) => dispatch({ type: "updateBrief", patch: { context: e.target.value } })}
        />
        <small className="muted">
          {brief.context.length}/{MAX_CONTEXT}
        </small>
      </label>
      <div className="field-row">
        <label className="field">
          <span>Tono</span>
          <select value={brief.tone} onChange={(e) => dispatch({ type: "updateBrief", patch: { tone: e.target.value } })}>
            {TONES.map((tone) => (
              <option key={tone}>{tone}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Duración (s)</span>
          <input
            type="number"
            min={10}
            max={45}
            value={brief.target_seconds}
            onChange={(e) => dispatch({ type: "updateBrief", patch: { target_seconds: Number(e.target.value) } })}
          />
        </label>
      </div>
      <button type="button" className="primary" disabled={busy || !brief.context.trim()} onClick={generate}>
        {busy ? "Escribiendo guion… (la primera vez tarda ~1 min)" : "✨ Generar guion con IA"}
      </button>
      {error && <p className="error">{error}</p>}
    </section>
  );
}
