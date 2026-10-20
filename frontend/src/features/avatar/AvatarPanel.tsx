import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Voice } from "../../api/types";
import { useEditor } from "../../state/EditorContext";
import { NewAvatarForm } from "./NewAvatarForm";
import { useAvatarLibrary } from "./useAvatarLibrary";

function VoicePicker() {
  const { state, dispatch } = useEditor();
  const [voices, setVoices] = useState<Voice[]>([]);

  useEffect(() => {
    api.voices().then(setVoices).catch(() => setVoices([]));
  }, []);

  return (
    <label className="field">
      <span>Voz</span>
      <select value={state.voice} onChange={(e) => dispatch({ type: "setVoice", voice: e.target.value })}>
        {voices.map((voice) => (
          <option key={voice.id} value={voice.id}>
            {voice.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function AvatarPanel() {
  const library = useAvatarLibrary();
  const [adding, setAdding] = useState(false);
  const showForm = adding || library.avatars.length === 0;

  return (
    <section className="panel-section">
      <h2>Mis avatares</h2>
      <p className="muted">El fondo se quita una sola vez al crearlo. Después solo lo eliges.</p>
      {library.avatars.length > 0 && (
        <div className="avatar-grid">
          {library.avatars.map((avatar) => (
            <div key={avatar.id} className={`avatar-card ${library.selectedId === avatar.id ? "selected" : ""}`}>
              <button type="button" className="avatar-card__pick" onClick={() => library.select(avatar)}>
                <img src={api.fileUrl(avatar.cutout_file_id)} alt={avatar.name} loading="lazy" />
                <span>{avatar.name}</span>
              </button>
              <button
                type="button"
                className="avatar-card__delete"
                aria-label={`Borrar ${avatar.name}`}
                onClick={() => void library.remove(avatar)}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
      {showForm ? (
        <NewAvatarForm
          creating={library.creating}
          onCreate={async (photoId, name) => {
            const ok = await library.create(photoId, name);
            if (ok) setAdding(false);
            return ok;
          }}
          onCancel={() => setAdding(false)}
        />
      ) : (
        <button type="button" className="secondary" onClick={() => setAdding(true)}>
          ＋ Nuevo avatar
        </button>
      )}
      {library.error && <p className="error">{library.error}</p>}
      <VoicePicker />
    </section>
  );
}
