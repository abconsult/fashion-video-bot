import httpx
import os
import tempfile
import subprocess
from typing import Optional


async def assemble_final_video(
    video_url: str,
    product_name: str,
    product_price: str,
    caption: Optional[str] = None,
) -> bytes:
    """
    Скачивает видео и добавляет текстовый оверлей через FFmpeg.
    Если FFmpeg недоступен, возвращает оригинальное видео.
    """
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.get(video_url)
        resp.raise_for_status()
        video_bytes = resp.content

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        output_path = os.path.join(tmpdir, "output.mp4")

        with open(input_path, "wb") as f:
            f.write(video_bytes)

        title_text = (product_name or "Новая коллекция")[:40]
        price_text = f"Цена: {product_price}" if product_price else ""

        vf_filter = (
            f"drawtext=text='{_esc(title_text)}'"
            f":fontsize=48:fontcolor=white"
            f":x=(w-text_w)/2:y=h-200"
            f":shadowcolor=black:shadowx=2:shadowy=2"
        )
        if price_text:
            vf_filter += (
                f",drawtext=text='{_esc(price_text)}'"
                f":fontsize=36:fontcolor=yellow"
                f":x=(w-text_w)/2:y=h-140"
                f":shadowcolor=black:shadowx=2:shadowy=2"
            )

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "copy",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=120)

        if result.returncode != 0:
            print(f"FFmpeg stderr: {result.stderr.decode()}")
            return video_bytes  # фоллбэк: оригинальное видео

        with open(output_path, "rb") as f:
            return f.read()


def _esc(text: str) -> str:
    """FFmpeg drawtext escaping."""
    return text.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")
