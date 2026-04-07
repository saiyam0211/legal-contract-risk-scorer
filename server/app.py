"""OpenEnv server entry point.

This module re-exports the FastAPI app from the root app.py and provides
the `main()` entry point used by the [project.scripts] console script.
"""

import uvicorn

# Re-export the app object so openenv can discover it
from app import app  # noqa: F401


def main() -> None:
    """Start the uvicorn server. Called by the `serve` console script."""
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
