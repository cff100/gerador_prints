"""
Motor de extração de frames de vídeo utilizando OpenCV e Pillow.
"""
import os
import random
import cv2
import threading
from typing import List, Dict, Any, Callable, Optional
from PIL import Image

from src.core.utils import (
    format_timestamp_filename,
    format_timestamp_display,
    sanitize_filename
)

class VideoProcessor:
    @staticmethod
    def calculate_uniform_timestamps(duration: float, mode_type: str, value: float) -> List[float]:
        """
        Calcula os carimbos de tempo para espaçamento uniforme.
        - mode_type == "interval": value representa os segundos entre cada print (ex: 5.0s)
        - mode_type == "count": value representa o número total de prints desejados (ex: 20)
        """
        if duration <= 0:
            return []

        timestamps = []
        if mode_type == "interval":
            interval = max(0.01, float(value))
            current = 0.0
            while current <= duration:
                timestamps.append(round(current, 3))
                current += interval
        elif mode_type == "count":
            count = int(value)
            if count <= 0:
                return []
            if count == 1:
                return [round(duration / 2.0, 3)]
            
            step = duration / (count - 1) if count > 1 else duration
            for i in range(count):
                t = min(duration, i * step)
                timestamps.append(round(t, 3))

        return sorted(list(set(timestamps)))

    @staticmethod
    def calculate_burst_timestamps(
        duration: float,
        cycle_interval_sec: float,
        burst_count: int,
        burst_spacing_sec: float,
        start_offset_sec: float = 0.0
    ) -> List[float]:
        """
        Calcula carimbos de tempo para o Modo 2 (Rajadas Periódicas / Concentrações).
        - cycle_interval_sec: Intervalo principal entre cada bloco de concentração (ex: a cada 60s)
        - burst_count: Quantidade de prints por bloco (ex: 5 fotos)
        - burst_spacing_sec: Espaçamento entre cada foto dentro do mesmo bloco (ex: 0.5s)
        - start_offset_sec: Momento inicial do primeiro ciclo (ex: 0.0s)
        """
        if duration <= 0 or burst_count <= 0 or cycle_interval_sec <= 0:
            return []

        timestamps = []
        current_cycle_base = max(0.0, start_offset_sec)

        while current_cycle_base <= duration:
            for i in range(burst_count):
                t = current_cycle_base + (i * burst_spacing_sec)
                if t <= duration:
                    timestamps.append(round(t, 3))
                else:
                    break
            current_cycle_base += cycle_interval_sec

        return sorted(list(set(timestamps)))

    @staticmethod
    def calculate_stratified_random_timestamps(duration: float, count: int) -> List[float]:
        """
        Calcula carimbos de tempo dividindo a duração em 'count' intervalos iguais
        e sorteando um instante aleatório em cada intervalo (amostragem estratificada).
        Garante cobertura do vídeo inteiro sem sobreposições excessivas.
        """
        if duration <= 0 or count <= 0:
            return []

        step = duration / count
        timestamps = []
        for i in range(count):
            start = i * step
            end = (i + 1) * step
            t = random.uniform(start, end)
            timestamps.append(round(min(duration, max(0.0, t)), 3))

        return sorted(list(set(timestamps)))

    @staticmethod
    def calculate_refinement_timestamps(
        base_timestamps: List[float],
        window_sec: float,
        count_per_point: int,
        duration: float
    ) -> List[float]:
        """
        Para cada timestamp base selecionado, calcula 'count_per_point' instantes
        uniformemente distribuídos na janela [T - window_sec, T + window_sec].
        """
        if duration <= 0 or count_per_point <= 0 or not base_timestamps:
            return []

        window = max(0.01, float(window_sec))
        all_timestamps = []

        for base_t in base_timestamps:
            start_t = max(0.0, base_t - window)
            end_t = min(duration, base_t + window)

            if count_per_point == 1:
                all_timestamps.append(round(base_t, 3))
            else:
                step = (end_t - start_t) / (count_per_point - 1) if end_t > start_t else 0.0
                for i in range(count_per_point):
                    t = start_t + (i * step)
                    all_timestamps.append(round(min(duration, max(0.0, t)), 3))

        return sorted(list(set(all_timestamps)))

    @classmethod
    def extract_frames(
        cls,
        video_path: str,
        output_dir: str,
        timestamps: List[float],
        image_format: str = "png", # "png" ou "jpeg"
        jpeg_quality: int = 95,
        prefix: str = "print",
        stop_event: Optional[threading.Event] = None,
        on_progress: Optional[Callable[[int, int, float, str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> List[str]:
        """
        Extrai os frames nas posições de tempo especificadas e salva no disco.
        Retorna a lista de caminhos dos arquivos salvos.
        """
        if not os.path.exists(video_path):
            if on_error:
                on_error(f"Arquivo de vídeo não encontrado: {video_path}")
            return []

        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            if on_error:
                on_error(f"Não foi possível criar a pasta de destino '{output_dir}': {str(e)}")
            return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            if on_error:
                on_error(f"Falha ao abrir vídeo com OpenCV: {video_path}")
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps is None or fps <= 0 or fps != fps:
            fps = 30.0
        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_video_frames / fps if (total_video_frames > 0 and fps > 0) else 0.0

        saved_files: List[str] = []
        # Garante timestamps únicos e estritamente ordenados cronologicamente
        sorted_timestamps = sorted(list(set(round(float(t), 3) for t in timestamps if t >= 0)))
        total_targets = len(sorted_timestamps)

        ext = image_format.lower().replace(".", "")
        if ext not in ["png", "jpeg", "jpg"]:
            ext = "png"

        try:
            for idx, t in enumerate(sorted_timestamps, start=1):
                if stop_event and stop_event.is_set():
                    break

                target_frame_no = int(round(t * fps))
                if total_video_frames > 0:
                    target_frame_no = min(max(0, target_frame_no), total_video_frames - 1)

                # Busca o frame no vídeo
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_no)
                ret, frame = cap.read()

                # Fallback por POS_MSEC se a busca por frame falhar
                if not ret or frame is None:
                    target_msec = t * 1000.0
                    cap.set(cv2.CAP_PROP_POS_MSEC, target_msec)
                    ret, frame = cap.read()

                if not ret or frame is None:
                    continue

                try:
                    # Converte BGR (OpenCV) para RGB (Pillow)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(rgb_frame)

                    time_str = format_timestamp_filename(t)
                    sanitized_prefix = sanitize_filename(prefix).strip() if prefix else ""
                    base_name = f"{sanitized_prefix}_{time_str}" if sanitized_prefix else time_str
                    filename = f"{base_name}.{ext}"
                    filepath = os.path.join(output_dir, filename)

                    # Evita sobrescrever arquivos no mesmo milissegundo de capturas anteriores
                    if os.path.exists(filepath):
                        dup = 1
                        while os.path.exists(filepath):
                            filename = f"{base_name}_{dup}.{ext}"
                            filepath = os.path.join(output_dir, filename)
                            dup += 1

                    if ext in ["jpg", "jpeg"]:
                        img.save(filepath, format="JPEG", quality=jpeg_quality, optimize=True)
                    else:
                        img.save(filepath, format="PNG", compress_level=6)

                    saved_files.append(filepath)

                    if on_progress:
                        on_progress(idx, total_targets, t, filepath)

                except Exception as save_err:
                    if on_error:
                        on_error(f"Erro ao salvar frame {idx}: {str(save_err)}")

            if not saved_files and total_targets > 0 and not (stop_event and stop_event.is_set()):
                if on_error:
                    on_error("Nenhum frame pôde ser lido do vídeo selecionado. Verifique os codecs do vídeo.")

        except Exception as e:
            if on_error:
                on_error(f"Erro durante a extração: {str(e)}")
        finally:
            cap.release()

        return saved_files
