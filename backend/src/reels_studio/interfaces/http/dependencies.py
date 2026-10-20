from __future__ import annotations

from typing import cast

from fastapi import Request

from reels_studio.bootstrap import Container


def get_container(request: Request) -> Container:
    return cast(Container, request.app.state.container)
