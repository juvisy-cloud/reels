import { useState, type FormEvent } from "react";
import type { UploadedImage } from "../../state/editorState";
import { ImageDrop } from "../../ui/ImageDrop";

interface Props {
  creating: boolean;
  onCreate: (photoFileId: string, name: string) => Promise<boolean>;
  onCancel: () => void;
}

export function NewAvatarForm({ creating, onCreate, onCancel }: Props) {
  const [photo, setPhoto] = useState<UploadedImage | null>(null);
  const [name, setName] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!photo || !name.trim()) return;
    if (await onCreate(photo.fileId, name)) {
      setPhoto(null);
      setName("");
    }
  };

  return (
    <form className="new-avatar" onSubmit={submit}>
      <ImageDrop label="Foto del avatar" hint="De frente, buena luz · PNG/JPG/WebP · máx. 10 MB" value={photo} onChange={setPhoto} />
      <label className="field">
        <span>Nombre</span>
        <input maxLength={40} placeholder="Ej: Julián oficina" value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      <div className="field-row">
        <button type="submit" className="primary" disabled={creating || !photo || !name.trim()}>
          {creating ? "Quitando el fondo… (~1 min)" : "Crear avatar"}
        </button>
        <button type="button" className="link-button" onClick={onCancel} disabled={creating}>
          Cancelar
        </button>
      </div>
      {creating && <p className="muted small">La primera vez descarga el modelo (~900 MB) y tarda más.</p>}
    </form>
  );
}
