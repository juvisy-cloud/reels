import { useId, type ChangeEvent } from "react";
import { api } from "../api/client";
import type { UploadedImage } from "../state/editorState";
import { useAsync } from "./useAsync";

const ACCEPTED = "image/png,image/jpeg,image/webp";
const MAX_BYTES = 10 * 1024 * 1024;

interface Props {
  label: string;
  hint: string;
  value: UploadedImage | null;
  onChange: (image: UploadedImage | null) => void;
}

export function ImageDrop({ label, hint, value, onChange }: Props) {
  const inputId = useId();
  const { busy, error, run } = useAsync();

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (file.size > MAX_BYTES) {
      await run(() => Promise.reject(new Error("La imagen debe pesar menos de 10 MB.")));
      return;
    }
    const uploaded = await run(() => api.uploadImage(file));
    if (uploaded) onChange({ fileId: uploaded.file_id, previewUrl: api.fileUrl(uploaded.file_id) });
  };

  return (
    <div className="image-drop">
      <label htmlFor={inputId} className={`image-drop__zone ${value ? "has-image" : ""}`}>
        {value ? <img src={value.previewUrl} alt={label} /> : <span className="image-drop__plus">＋</span>}
        <span className="image-drop__label">{busy ? "Subiendo…" : label}</span>
        <span className="image-drop__hint">{hint}</span>
      </label>
      <input id={inputId} type="file" accept={ACCEPTED} onChange={handleFile} hidden />
      {value && (
        <button type="button" className="link-button" onClick={() => onChange(null)}>
          Quitar
        </button>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
