import { useEditor } from "../../state/EditorContext";
import { ImageDrop } from "../../ui/ImageDrop";

const HANDLE_PATTERN = /^@?[A-Za-z0-9._]{0,30}$/;

export function BrandPanel() {
  const { state, dispatch } = useEditor();
  const handle = state.brief.handle;

  return (
    <section className="panel-section">
      <h2>Marca y cierre</h2>
      <label className="field">
        <span>Usuario de Instagram</span>
        <input
          value={handle}
          placeholder="@juvisy.cloud"
          onChange={(e) => {
            if (HANDLE_PATTERN.test(e.target.value)) dispatch({ type: "updateBrief", patch: { handle: e.target.value } });
          }}
        />
      </label>
      <ImageDrop
        label="Logo para el cierre"
        hint="Se muestra al final del reel"
        value={state.logo}
        onChange={(image) => dispatch({ type: "setImage", slot: "logo", image })}
      />
      <ImageDrop
        label="Captura de apoyo (opcional)"
        hint="Aparece en un marco de celular en la escena 2"
        value={state.overlay}
        onChange={(image) => dispatch({ type: "setImage", slot: "overlay", image })}
      />
    </section>
  );
}
