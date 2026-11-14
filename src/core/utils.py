"""
Utilitários de suporte para formatação de tempo, manipulação de arquivos,
integração com o sistema operacional e leitura de metadados de vídeo.
"""
import os
import re
import platform
import subprocess
import cv2
from typing import Dict, Any, Tuple


def _decompose_time_ms(seconds: float) -> Tuple[int, int, int, int]:
    """
    Decompõe segundos em (horas, minutos, segundos_inteiros, milissegundos).

    POR QUÊ: Converter tudo para milissegundos inteiros logo na entrada evita
    erros clássicos de ponto flutuante (IEEE 754), onde um valor como 59.9999s
    poderia ser arredondado para "00:60.0" em vez de virar "01:00.0".
    """
    total_sec = max(0.0, float(seconds))
    total_ms = int(round(total_sec * 1000))

    hours = total_ms // 3_600_000
    rem_ms = total_ms % 3_600_000
    minutes = rem_ms // 60_000
    rem_ms %= 60_000
    secs = rem_ms // 1_000
    millis = rem_ms % 1_000

    return hours, minutes, secs, millis


def format_timestamp_display(seconds: float) -> str:
    """
    Formata segundos para exibição na UI: 'HH:MM:SS.d' ou 'MM:SS.d'.

    POR QUÊ: Omitimos as horas quando são zero para economizar espaço horizontal
    nos cards pequenos da galeria de miniaturas.
    """
    hours, minutes, secs, millis = _decompose_time_ms(seconds)
    secs_with_tenths = secs + (millis / 1000.0)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs_with_tenths:04.1f}"
    return f"{minutes:02d}:{secs_with_tenths:04.1f}"


def format_timestamp_filename(seconds: float) -> str:
    """
    Formata segundos para nomes de arquivo: '00h01m23s_450ms'.

    POR QUÊ: Diferente da exibição visual, aqui SEMPRE incluímos as horas com
    zeros à esquerda (00h) e evitamos dois-pontos (:), que são proibidos no Windows.
    Esse formato garante que a ordenação alfabética do Windows Explorer bata
    100% com a ordem cronológica do vídeo.
    """
    hours, minutes, secs, millis = _decompose_time_ms(seconds)
    return f"{hours:02d}h{minutes:02d}m{secs:02d}s_{millis:03d}ms"


def sanitize_filename(filename: str) -> str:
    """
    Substitui caracteres reservados do sistema de arquivos por '_'.

    POR QUÊ: Títulos de vídeos frequentemente contêm ':', '?' ou '/', que causam
    OSError imediato ao tentar criar pastas ou arquivos no Windows/NTFS.
    """
    return re.sub(r'[\\/*?:"<>|]', "_", filename).strip()


def resolve_unique_filepath(directory: str, filename: str) -> str:
    """
    Retorna um caminho completo garantindo que não sobrescreva um arquivo existente
    (adicionando '_1', '_2', etc. se necessário).

    POR QUÊ: No Modo 3 (Refinamento) ou ao mover prints para subpastas, o usuário
    faz múltiplas operações no mesmo diretório. Nunca sobrescrever protege
    capturas anteriores contra perda acidental.
    """
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        return filepath

    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(filepath):
        filepath = os.path.join(directory, f"{base}_{counter}{ext}")
        counter += 1
    return filepath


def open_path_in_os(path: str) -> None:
    """
    Abre um arquivo ou pasta usando o aplicativo padrão do sistema operacional.

    POR QUÊ: Python só oferece `os.startfile()` no Windows. Isolar essa verificação
    de plataforma em uma função única evita espalhar `if platform.system()`
    pela camada de interface gráfica.
    """
    if not os.path.exists(path):
        return

    system = platform.system()
    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def get_video_info(video_path: str) -> Dict[str, Any]:
    """
    Extrai metadados essenciais do vídeo (duração, FPS, resolução) via OpenCV.

    POR QUÊ: Usamos um bloco `try...finally` garantindo `cap.release()` porque,
    se uma exceção ocorrer ou o objeto C++ do OpenCV ficar aberto na memória,
    o Windows trava o arquivo de vídeo impedindo o usuário de movê-lo ou renomeá-lo.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Não foi possível abrir o arquivo de vídeo: {video_path}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        # POR QUÊ `fps != fps`: Em ponto flutuante IEEE 754, NaN é o único valor
        # que não é igual a si mesmo. Contêineres corrompidos podem retornar NaN.
        if fps is None or fps <= 0 or fps != fps:
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
