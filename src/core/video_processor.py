"""
Motor de extração de frames de vídeo utilizando OpenCV e Pillow.
"""
import os
import random
import threading
import cv2
from typing import List, Callable, Optional
from PIL import Image

from src.core.utils import (
    format_timestamp_filename,
    sanitize_filename,
    resolve_unique_filepath
)


class VideoProcessor:
    @staticmethod
    def _deduplicate_and_sort(timestamps: List[float]) -> List[float]:
        """
        Arredonda para milissegundos, remove duplicatas e ordena cronologicamente.

        POR QUÊ: Ordenar os carimbos de tempo antes de ler o vídeo garante que a
        cabeça de leitura do OpenCV sempre avance para frente (seek sequencial),
        o que é muito mais rápido do que pular para trás e para frente no arquivo.
        """
        return sorted(list(set(round(float(t), 3) for t in timestamps if t >= 0)))

    @classmethod
    def calculate_uniform_timestamps(cls, duration: float, mode_type: str, value: float) -> List[float]:
        """
        Calcula os carimbos de tempo para espaçamento uniforme (Modo 1).
        - mode_type == "interval": segundos fixos entre cada print (ex: 5.0s)
        - mode_type == "count": quantidade total de prints distribuídos no vídeo (ex: 20)
        """
        if duration <= 0:
            return []

        timestamps = []
        if mode_type == "interval":
            interval = max(0.01, float(value))
            current = 0.0
            while current <= duration:
                timestamps.append(current)
                current += interval
        elif mode_type == "count":
            count = int(value)
            if count <= 0:
                return []
            if count == 1:
                return [round(duration / 2.0, 3)]

            # POR QUÊ `(count - 1)`: Para incluir tanto o instante 0.0 quanto o
            # final do vídeo (`duration`) perfeitamente espaçados em `count` pontos.
            step = duration / (count - 1)
            for i in range(count):
                timestamps.append(min(duration, i * step))

        return cls._deduplicate_and_sort(timestamps)

    @classmethod
    def calculate_burst_timestamps(
        cls,
        duration: float,
        cycle_interval_sec: float,
        burst_count: int,
        burst_spacing_sec: float,
        start_offset_sec: float = 0.0
    ) -> List[float]:
        """
        Calcula carimbos de tempo para Rajadas Periódicas / Concentrações (Modo 2).
        """
        if duration <= 0 or burst_count <= 0 or cycle_interval_sec <= 0:
            return []

        timestamps = []
        current_cycle_base = max(0.0, start_offset_sec)

        while current_cycle_base <= duration:
            for i in range(burst_count):
                t = current_cycle_base + (i * burst_spacing_sec)
                if t <= duration:
                    timestamps.append(t)
                else:
                    break
            current_cycle_base += cycle_interval_sec

        return cls._deduplicate_and_sort(timestamps)

    @classmethod
    def calculate_stratified_random_timestamps(cls, duration: float, count: int) -> List[float]:
        """
        Calcula carimbos de tempo por Amostragem Estratificada (Modo 3 - Etapa 1).

        POR QUÊ: Um sorteio puramente aleatório (`random.uniform(0, duration)`)
        frequentemente aglomera vários prints na mesma cena e deixa minutos inteiros
        vazios. Dividir o vídeo em `count` fatias iguais e sortear 1 ponto dentro
        de cada fatia garante cobertura total mantendo a aleatoriedade.
        """
        if duration <= 0 or count <= 0:
            return []

        step = duration / count
        timestamps = []
        for i in range(count):
            start = i * step
            end = (i + 1) * step
            t = random.uniform(start, end)
            timestamps.append(min(duration, max(0.0, t)))

        return cls._deduplicate_and_sort(timestamps)

    @classmethod
    def calculate_refinement_timestamps(
        cls,
        base_timestamps: List[float],
        window_sec: float,
        count_per_point: int,
        duration: float
    ) -> List[float]:
        """
        Gera novos carimbos de tempo na janela [T - window_sec, T + window_sec]
        ao redor de cada print favorito selecionado pelo usuário (Modo 3 - Etapa 2).
        """
        if duration <= 0 or count_per_point <= 0 or not base_timestamps:
            return []

        window = max(0.01, float(window_sec))
        all_timestamps = []

        for base_t in base_timestamps:
            start_t = max(0.0, base_t - window)
            end_t = min(duration, base_t + window)

            if count_per_point == 1:
                all_timestamps.append(base_t)
            else:
                step = (end_t - start_t) / (count_per_point - 1) if end_t > start_t else 0.0
                for i in range(count_per_point):
                    t = start_t + (i * step)
                    all_timestamps.append(min(duration, max(0.0, t)))

        return cls._deduplicate_and_sort(all_timestamps)

    @staticmethod
    def _seek_and_read_frame(cap: cv2.VideoCapture, timestamp_sec: float, fps: float, total_frames: int):
        """
        Posiciona o leitor do vídeo no segundo desejado e retorna o frame extraído.

        POR QUÊ (Dupla Estratégia de Busca):
        1. Tentamos primeiro `CAP_PROP_POS_FRAMES` porque é mais exato em vídeos CFR
           (taxa de quadros constante, como MP4 padrão).
        2. Usamos `CAP_PROP_POS_MSEC` como fallback porque vídeos MKV/WebM com VFR
           (taxa de quadros variável) podem falhar na indexação por número de quadro.
        """
        target_frame_no = int(round(timestamp_sec * fps))
        if total_frames > 0:
            target_frame_no = min(max(0, target_frame_no), total_frames - 1)

        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_no)
        ret, frame = cap.read()

        if not ret or frame is None:
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000.0)
            ret, frame = cap.read()

        return frame if ret else None

    @staticmethod
    def _build_frame_filepath(output_dir: str, prefix: str, timestamp_sec: float, ext: str) -> str:
        """
        Monta o caminho completo e único para salvar o frame extraído.
        """
        time_str = format_timestamp_filename(timestamp_sec)
        sanitized_prefix = sanitize_filename(prefix).strip() if prefix else ""
        base_name = f"{sanitized_prefix}_{time_str}" if sanitized_prefix else time_str
        filename = f"{base_name}.{ext}"
        return resolve_unique_filepath(output_dir, filename)

    @staticmethod
    def _save_frame_image(frame_bgr, filepath: str, ext: str, jpeg_quality: int) -> None:
        """
        Converte a matriz do OpenCV (BGR) para imagem Pillow (RGB) e salva no disco.

        POR QUÊ usar Pillow em vez de `cv2.imwrite()`:
        No Windows, o `cv2.imwrite` do OpenCV usa a API C ANSI antiga e falha
        silenciosamente (ou gera nomes corrompidos) quando o caminho tem acentos,
        colchetes ou caracteres especiais (ex: 'Caio_(fora_do_drive)' ou 'São Paulo').
        O Pillow usa o sistema de arquivos nativo UTF-8 do Python, funcionando sempre.
        """
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)

        if ext in ["jpg", "jpeg"]:
            img.save(filepath, format="JPEG", quality=jpeg_quality, optimize=True)
        else:
            img.save(filepath, format="PNG", compress_level=6)

    @classmethod
    def extract_frames(
        cls,
        video_path: str,
        output_dir: str,
        timestamps: List[float],
        image_format: str = "png",
        jpeg_quality: int = 95,
        prefix: str = "print",
        stop_event: Optional[threading.Event] = None,
        on_progress: Optional[Callable[[int, int, float, str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> List[str]:
        """
        Orquestra a extração dos frames nas posições de tempo informadas.
        Retorna a lista de caminhos dos arquivos gerados.
        """
        if not os.path.exists(video_path):
            if on_error:
                on_error(f"Arquivo de vídeo não encontrado: {video_path}")
            return []

        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            if on_error:
                on_error(f"Não foi possível criar a pasta de destino '{output_dir}': {e}")
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

        saved_files: List[str] = []
        sorted_timestamps = cls._deduplicate_and_sort(timestamps)
        total_targets = len(sorted_timestamps)

        ext = image_format.lower().replace(".", "")
        if ext not in ["png", "jpeg", "jpg"]:
            ext = "png"

        try:
            for idx, t in enumerate(sorted_timestamps, start=1):
                if stop_event and stop_event.is_set():
                    break

                frame = cls._seek_and_read_frame(cap, t, fps, total_video_frames)
                if frame is None:
                    continue

                try:
                    filepath = cls._build_frame_filepath(output_dir, prefix, t, ext)
                    cls._save_frame_image(frame, filepath, ext, jpeg_quality)
                    saved_files.append(filepath)

                    if on_progress:
                        on_progress(idx, total_targets, t, filepath)
                except Exception as save_err:
                    if on_error:
                        on_error(f"Erro ao salvar frame {idx}: {save_err}")

            if not saved_files and total_targets > 0 and not (stop_event and stop_event.is_set()):
                if on_error:
                    on_error("Nenhum frame pôde ser lido do vídeo selecionado. Verifique os codecs do vídeo.")

        except Exception as e:
            if on_error:
                on_error(f"Erro durante a extração: {e}")
        finally:
            cap.release()

        return saved_files
