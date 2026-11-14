"""
Componente de interface para o Modo 2: Rajadas Periódicas com Stepper e Prévia Dinâmica.
"""
import customtkinter as ctk
from typing import Callable, List, Optional, Dict, Any
from src.core.video_processor import VideoProcessor
from src.core.utils import format_timestamp_display
from src.gui.components.stepper_entry import StepperEntry


class ModeBurstFrame(ctk.CTkFrame):
    def __init__(self, master, on_change: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_change = on_change
        self.video_duration: Optional[float] = None

        self._create_widgets()
        self._update_preview()

    def _create_widgets(self):
        self.title_label = ctk.CTkLabel(
            self,
            text="Configuração de Rajadas Periódicas (Concentrações)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_label.pack(anchor="w", padx=10, pady=(10, 4))

        self.desc_label = ctk.CTkLabel(
            self,
            text="Dispara sequências de fotos em momentos-chave, com espaçamento maior entre cada rajada.",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60")
        )
        self.desc_label.pack(anchor="w", padx=10, pady=(0, 6))

        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="x", padx=10, pady=2)
        self.grid_frame.columnconfigure(1, weight=1)

        # 1. Intervalo Principal (Ciclo)
        lbl_cycle = ctk.CTkLabel(
            self.grid_frame,
            text="Repetir a cada (segundos):",
            font=ctk.CTkFont(size=12)
        )
        lbl_cycle.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)

        self.stepper_cycle = StepperEntry(
            self.grid_frame,
            initial_value=30.0,
            step=5.0,
            min_value=1.0,
            max_value=3600.0,
            is_float=True,
            on_change=self._notify_change
        )
        self.stepper_cycle.grid(row=0, column=1, sticky="w", pady=4)

        lbl_cycle_hint = ctk.CTkLabel(
            self.grid_frame,
            text="(ciclo principal entre blocos)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        lbl_cycle_hint.grid(row=0, column=2, sticky="w", padx=10, pady=4)

        # 2. Quantidade por Rajada
        lbl_burst_count = ctk.CTkLabel(
            self.grid_frame,
            text="Prints por rajada (quantidade):",
            font=ctk.CTkFont(size=12)
        )
        lbl_burst_count.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)

        self.stepper_burst_count = StepperEntry(
            self.grid_frame,
            initial_value=5,
            step=1,
            min_value=1,
            max_value=500,
            is_float=False,
            on_change=self._notify_change
        )
        self.stepper_burst_count.grid(row=1, column=1, sticky="w", pady=4)

        lbl_burst_hint = ctk.CTkLabel(
            self.grid_frame,
            text="(fotos em sequência no bloco)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        lbl_burst_hint.grid(row=1, column=2, sticky="w", padx=10, pady=4)

        # 3. Espaçamento Interno na Rajada
        lbl_spacing = ctk.CTkLabel(
            self.grid_frame,
            text="Espaçamento na rajada (segundos):",
            font=ctk.CTkFont(size=12)
        )
        lbl_spacing.grid(row=2, column=0, sticky="w", padx=(0, 10), pady=4)

        self.stepper_spacing = StepperEntry(
            self.grid_frame,
            initial_value=0.5,
            step=0.1,
            min_value=0.01,
            max_value=60.0,
            is_float=True,
            on_change=self._notify_change
        )
        self.stepper_spacing.grid(row=2, column=1, sticky="w", pady=4)

        lbl_spacing_hint = ctk.CTkLabel(
            self.grid_frame,
            text="(tempo entre fotos da mesma rajada)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        lbl_spacing_hint.grid(row=2, column=2, sticky="w", padx=10, pady=4)

        # 4. Início / Offset
        lbl_offset = ctk.CTkLabel(
            self.grid_frame,
            text="Iniciar a partir do segundo:",
            font=ctk.CTkFont(size=12)
        )
        lbl_offset.grid(row=3, column=0, sticky="w", padx=(0, 10), pady=4)

        self.stepper_offset = StepperEntry(
            self.grid_frame,
            initial_value=0.0,
            step=1.0,
            min_value=0.0,
            max_value=3600.0,
            is_float=True,
            on_change=self._notify_change
        )
        self.stepper_offset.grid(row=3, column=1, sticky="w", pady=4)

        lbl_offset_hint = ctk.CTkLabel(
            self.grid_frame,
            text="(offset inicial configurável)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        lbl_offset_hint.grid(row=3, column=2, sticky="w", padx=10, pady=4)

        # ==========================================
        # CARD DE SIMULAÇÃO / PRÉVIA EM TEMPO REAL
        # ==========================================
        self.preview_card = ctk.CTkFrame(self, fg_color=("#f1f5f9", "#1e293b"), corner_radius=8)
        self.preview_card.pack(fill="x", padx=10, pady=(6, 10))

        self.lbl_preview_title = ctk.CTkLabel(
            self.preview_card,
            text="💡 Como vai funcionar na prática:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#0284c7", "#38bdf8")
        )
        self.lbl_preview_title.pack(anchor="w", padx=10, pady=(8, 2))

        self.lbl_preview_body = ctk.CTkLabel(
            self.preview_card,
            text="",
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=380
        )
        self.lbl_preview_body.pack(anchor="w", padx=10, pady=(0, 8))

    def set_duration(self, duration: Optional[float]):
        """Atualiza a duração do vídeo ativo para refletir na prévia."""
        self.video_duration = duration
        self._update_preview()

    def _update_preview(self):
        """Calcula e exibe a simulação das rajadas em tempo real."""
        is_mock = self.video_duration is None or self.video_duration <= 0
        dur = 600.0 if is_mock else float(self.video_duration)

        cycle = float(self.stepper_cycle.get_value())
        count = int(self.stepper_burst_count.get_value())
        spacing = float(self.stepper_spacing.get_value())
        offset = float(self.stepper_offset.get_value())

        ts = VideoProcessor.calculate_burst_timestamps(dur, cycle, count, spacing, offset)
        total_prints = len(ts)
        num_bursts = (total_prints + count - 1) // count if count > 0 else 0

        prefix_tag = "📌 [Exemplo com vídeo de 10 min]\n" if is_mock else f"🎬 [Vídeo atual: {format_timestamp_display(dur)}]\n"

        # Simula a primeira rajada
        first_burst_pts = [format_timestamp_display(offset + (i * spacing)) for i in range(min(count, 3))]
        burst1_str = ", ".join(first_burst_pts)
        if count > 3:
            burst1_str += f"... ({count} fotos)"

        # Próximo ciclo
        next_cycle_t = offset + cycle

        body = (
            f"{prefix_tag}"
            f"• A cada {cycle:.1f}s dispara 1 rajada com {count} prints (a cada {spacing:.2f}s).\n"
            f"• 1ª rajada (aos {format_timestamp_display(offset)}): {burst1_str}\n"
            f"• 2ª rajada ocorrerá aos {format_timestamp_display(next_cycle_t)}\n"
            f"• Total estimado: {total_prints} print(s) agrupados em ~{num_bursts} bloco(s)."
        )

        self.lbl_preview_body.configure(text=body)

    def _notify_change(self):
        self._update_preview()
        if self.on_change:
            self.on_change()

    def get_timestamps(self, duration: float) -> List[float]:
        if duration <= 0:
            return []

        cycle = float(self.stepper_cycle.get_value())
        count = int(self.stepper_burst_count.get_value())
        spacing = float(self.stepper_spacing.get_value())
        offset = float(self.stepper_offset.get_value())

        return VideoProcessor.calculate_burst_timestamps(
            duration=duration,
            cycle_interval_sec=cycle,
            burst_count=count,
            burst_spacing_sec=spacing,
            start_offset_sec=offset
        )

    def load_config(self, config: Dict[str, Any]):
        self.stepper_cycle.set_value(config.get("burst_cycle", 30.0))
        self.stepper_burst_count.set_value(config.get("burst_count", 5))
        self.stepper_spacing.set_value(config.get("burst_spacing", 0.5))
        self.stepper_offset.set_value(config.get("burst_offset", 0.0))
        self._update_preview()

    def get_config(self) -> Dict[str, Any]:
        return {
            "burst_cycle": self.stepper_cycle.get_value(),
            "burst_count": self.stepper_burst_count.get_value(),
            "burst_spacing": self.stepper_spacing.get_value(),
            "burst_offset": self.stepper_offset.get_value()
        }
