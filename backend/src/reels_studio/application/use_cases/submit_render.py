from reels_studio.application.ports import AvatarRepositoryPort, FileStorePort, JobRepositoryPort
from reels_studio.domain.models import Job, ReelRequest


class SubmitRender:
    """Encola un render; el worker lo ejecuta en segundo plano (CPU, uno a la vez)."""

    def __init__(self, jobs: JobRepositoryPort, files: FileStorePort, avatars: AvatarRepositoryPort) -> None:
        self._jobs = jobs
        self._files = files
        self._avatars = avatars

    def execute(self, request: ReelRequest) -> Job:
        self._avatars.get(request.avatar_id)
        if request.overlay_file_id is not None:
            self._files.path_for(request.overlay_file_id)
        if request.brand.logo_file_id is not None:
            self._files.path_for(request.brand.logo_file_id)
        job = Job(request=request)
        self._jobs.save(job)
        return job
