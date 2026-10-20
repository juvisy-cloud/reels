import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Avatar } from "../../api/types";
import { useEditor } from "../../state/EditorContext";
import { useAsync } from "../../ui/useAsync";

/** Carga, crea y borra avatares guardados; mantiene sincronizada la selección del editor. */
export function useAvatarLibrary() {
  const { state, dispatch } = useEditor();
  const [avatars, setAvatars] = useState<Avatar[]>([]);
  const creation = useAsync();
  const removal = useAsync();

  useEffect(() => {
    api.listAvatars().then(setAvatars).catch(() => setAvatars([]));
  }, []);

  const select = useCallback((avatar: Avatar) => dispatch({ type: "setAvatar", avatar }), [dispatch]);

  const create = async (photoFileId: string, name: string): Promise<boolean> => {
    const avatar = await creation.run(() => api.createAvatar(photoFileId, name));
    if (!avatar) return false;
    setAvatars((current) => [avatar, ...current]);
    select(avatar);
    return true;
  };

  const remove = async (avatar: Avatar) => {
    if (!window.confirm(`¿Borrar el avatar "${avatar.name}"?`)) return;
    const done = await removal.run(() => api.deleteAvatar(avatar.id).then(() => true));
    if (!done) return;
    setAvatars((current) => current.filter((a) => a.id !== avatar.id));
    if (state.avatar?.id === avatar.id) dispatch({ type: "setAvatar", avatar: null });
  };

  return {
    avatars,
    selectedId: state.avatar?.id ?? null,
    select,
    create,
    remove,
    creating: creation.busy,
    error: creation.error ?? removal.error,
  };
}
