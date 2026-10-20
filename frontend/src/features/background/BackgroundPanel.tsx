import { useState, type FormEvent } from "react";
import { api } from "../../api/client";
import type { Background, MediaKind } from "../../api/types";
import { useEditor } from "../../state/EditorContext";
import { useAsync } from "../../ui/useAsync";

export function BackgroundPanel() {
  const { state, dispatch } = useEditor();
  const suggestions = state.script?.pexels_queries ?? [];
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<MediaKind>("video");
  const [results, setResults] = useState<Background[]>([]);
  const { busy, error, run } = useAsync();

  const search = async (text: string, mediaKind: MediaKind = kind) => {
    if (!text.trim()) return;
    setQuery(text);
    const found = await run(() => api.searchBackgrounds(text, mediaKind));
    if (found) setResults(found);
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void search(query);
  };

  return (
    <section className="panel-section">
      <h2>Fondo (Pexels)</h2>
      <div className="segmented" role="radiogroup" aria-label="Tipo de fondo">
        {(["video", "photo"] as const).map((option) => (
          <button
            key={option}
            type="button"
            role="radio"
            aria-checked={kind === option}
            className={kind === option ? "active" : ""}
            onClick={() => {
              setKind(option);
              void search(query, option);
            }}
          >
            {option === "video" ? "Videos" : "Fotos"}
          </button>
        ))}
      </div>
      <form className="search" onSubmit={submit}>
        <input value={query} maxLength={80} placeholder="Buscar en inglés: office, coffee…" onChange={(e) => setQuery(e.target.value)} />
        <button type="submit" disabled={busy}>
          Buscar
        </button>
      </form>
      {suggestions.length > 0 && (
        <div className="chips">
          <span className="muted">Sugeridas:</span>
          {suggestions.map((s) => (
            <button key={s} type="button" className="chip" onClick={() => void search(s)}>
              {s}
            </button>
          ))}
        </div>
      )}
      {error && <p className="error">{error}</p>}
      <div className="gallery">
        {results.map((item) => (
          <button
            key={`${item.kind}-${item.provider_id}`}
            type="button"
            className={`gallery__item ${state.background?.provider_id === item.provider_id ? "selected" : ""}`}
            onClick={() => dispatch({ type: "setBackground", background: item })}
            title={`Por ${item.author} en Pexels`}
          >
            <img src={item.preview_url} alt={`Fondo de ${item.author}`} loading="lazy" />
            {item.kind === "video" && <span className="badge">▶ {Math.round(item.duration_seconds ?? 0)}s</span>}
          </button>
        ))}
      </div>
      {state.background && (
        <p className="muted small">
          Fondo por{" "}
          <a href={state.background.author_url} target="_blank" rel="noreferrer noopener">
            {state.background.author}
          </a>{" "}
          en Pexels
        </p>
      )}
    </section>
  );
}
