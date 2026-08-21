"""Render Mermaid source to PNG with mermaid-cli (mmdc)."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.utils.module_loading import import_string


class InvalidMermaidError(ValueError):
    """Source is empty or mermaid-cli rejected it as invalid."""


class RenderUnavailableError(RuntimeError):
    """mermaid-cli could not produce a PNG (binary missing, crash, timeout)."""


def render_png(source: str) -> bytes:
    renderer = getattr(settings, "MERMAID_RENDERER", render_with_mmdc)
    if callable(renderer) and renderer is not render_png:
        return renderer(source)
    if isinstance(renderer, str):
        return import_string(renderer)(source)
    return render_with_mmdc(source)


def render_with_mmdc(source: str) -> bytes:
    cli = getattr(settings, "MERMAID_CLI", "mmdc")
    config = getattr(settings, "MERMAID_PUPPETEER_CONFIG", "")
    timeout = int(getattr(settings, "MERMAID_RENDER_TIMEOUT", 30))
    env = os.environ.copy()
    skip = getattr(settings, "PUPPETEER_SKIP_DOWNLOAD", None)
    if skip:
        env["PUPPETEER_SKIP_DOWNLOAD"] = str(skip)
    executable = getattr(settings, "PUPPETEER_EXECUTABLE_PATH", "")
    if executable:
        env["PUPPETEER_EXECUTABLE_PATH"] = executable

    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / "diagram.mmd"
        output_path = Path(tmp) / "diagram.png"
        input_path.write_text(source, encoding="utf-8")
        cmd = [cli, "-i", str(input_path), "-o", str(output_path), "-b", "transparent"]
        if config:
            cmd.extend(["-p", str(config)])
        try:
            completed = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
        except FileNotFoundError as exc:
            raise RenderUnavailableError("mermaid-cli is not installed") from exc
        except subprocess.TimeoutExpired as exc:
            raise RenderUnavailableError("mermaid-cli timed out") from exc

        stderr = (completed.stderr or "") + (completed.stdout or "")
        if completed.returncode != 0:
            lowered = stderr.lower()
            if "parse error" in lowered or "syntax error" in lowered:
                raise InvalidMermaidError(stderr.strip() or "Invalid Mermaid source")
            raise RenderUnavailableError(stderr.strip() or "mermaid-cli failed")
        if not output_path.is_file():
            raise RenderUnavailableError("mermaid-cli produced no PNG")
        return output_path.read_bytes()
