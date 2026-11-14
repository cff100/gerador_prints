"""
Utilitários de suporte para formatação de tempo, manipulação de arquivos e metadados de vídeo.
"""
import os
import re
import cv2
from typing import Dict, Any

def format_timestamp_display(seconds: float) -> str:
    """Formata segundos para exibição amigável: HH:MM:SS.m ou MM:SS.m."""
    total_sec = max(0.0, float(seconds))
    total_ms = int(round(total_sec * 1000))
    hours = total_ms // 3600000
    rem_ms = total_ms % 3600000
    minutes = rem_ms // 60000
    secs = (rem_ms % 60000) / 1000.0
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:04.1f}"
    return f"{minutes:02d}:{secs:04.1f}"

def format_timestamp_filename(seconds: float) -> str:
    """Formata segundos para uso seguro e estritamente ordenável em nomes de arquivo: 00h01m23s_450ms."""
    total_sec = max(0.0, float(seconds))
    total_ms = int(round(total_sec * 1000))
    hours = total_ms // 3600000
    rem_ms = total_ms % 3600000
    minutes = rem_ms // 60000
    rem_ms %= 60000
    secs = rem_ms // 1000
    millis = rem_ms % 1000
    return f"{hours:02d}h{minutes:02d}m{secs:02d}s_{millis:03d}ms"

def sanitize_filename(filename: str) -> str:
    """Remove caracteres inválidos para nomes de arquivos do Windows."""
    return re.sub(r'[\\/*?:"<>|]', "_", filename).strip()

def get_video_info(video_path: str) -> Dict[str, Any]:
    """Extrai informações essenciais do vídeo via OpenCV."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Não foi possível abrir o arquivo de vídeo: {video_path}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps is None or fps <= 0 or fps != fps: # NaN check
            fps = 30.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_sec = (total_frames / fps) if (total_frames > 0 and fps > 0) else 0.0

        return {
            "path": video_path,
            "filename": os.path.basename(video_path),
            "fps": fps,
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "duration_sec": duration_sec,
            "duration_display": format_timestamp_display(duration_sec)
        }
    finally:
        cap.release()
