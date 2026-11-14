"""
Componente de interface para o Modo 2: Rajadas Periódicas com Stepper.
"""
import customtkinter as ctk
from typing import Callable, List, Optional, Dict, Any
from src.core.video_processor import VideoProcessor
from src.gui.components.stepper_entry import StepperEntry

class ModeBurstFrame(ctk.CTkFrame):
    def __init__(self, master, on_change: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_change = on_change

        self._create_widgets()

    def _create_widgets(self):
        self.title_label = ctk.CTkLabel(
            self,
            text="Configuração de Rajadas Periódicas (Concentrações)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.desc_label = ctk.CTkLabel(
            self,
            text="Dispara sequências de fotos em momentos chave, com espaçamento maior entre cada rajada.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.desc_label.pack(anchor="w", padx=10, pady=(0, 10))

        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="x", padx=10, pady=5)
        self.grid_frame.columnconfigure(1, weight=1)

        # 1. Intervalo Principal (Ciclo)
        lbl_cycle = ctk.CTkLabel(
            self.grid_frame,
            text="Repetir a cada (segundos):",
            font=ctk.CTkFont(size=12)
        )
        lbl_cycle.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        
        self.stepper_cycle = StepperEntry(
            self.grid_frame,
            initial_value=30.0,
            step=5.0,
            min_value=1.0,
            max_value=3600.0,
            is_float=True,
            on_change=self._notify_change
        )
        self.stepper_cycle.grid(row=0, column=1, sticky="w", pady=6)

        lbl_cycle_hint = ctk.CTkLabel(
            self.grid_frame,
            text="(ex: 30s = uma nova rajada a cada 30 segundos)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        lbl_cycle_hint.grid(row=0, column=2, sticky="w", padx=10, pady=6)

        # 2. Quantidade por Rajada
        lbl_burst_count = ctk.CTkLabel(
            self.grid_frame,
            text="Prints por rajada (quantidade):",
            font=ctk.CTkFont(size=12)
        )
        lbl_burst_count.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)

        self.stepper_burst_count = StepperEntry(
            self.grid_frame,
            initial_value=5,
            step=1,
            min_value=1,
            max_value=500,
            is_float=False,
            on_change=self._notify_change
        )
        self.stepper_burst_count.grid(row=1, column=1, sticky="w", pady=6)

        lbl_burst_hint = ctk.CTkLabel(
            self.grid_frame,
            text="(ex: 5 = tira 5 prints seguidos em cada ciclo)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        lbl_burst_hint.grid(row=1, column=2, sticky="w", padx=10, pady=6)

        # 3. Espaçamento Interno na Rajada
        lbl_spacing = ctk.CTkLabel(
            self.grid_frame,
            text="Espaçamento na rajada (segundos):",
            font=ctk.CTkFont(size=12)
        )
        lbl_spacing.grid(row=2, column=0, sticky="w", padx=(0, 10), pady=6)

        self.stepper_spacing = StepperEntry(
            self.grid_frame,
            initial_value=0.5,
            step=0.1,
            min_value=0.01,
            max_value=60.0,
            is_float=True,
            on_change=self._notify_change
        )
        self.stepper_spacing.grid(row=2, column=1, sticky="w", pady=6)

        lbl_spacing_hint = ctk.CTkLabel(
            self.grid_frame,
            text="(ex: 0.5s = meio segundo entre cada print)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        lbl_spacing_hint.grid(row=2, column=2, sticky="w", padx=10, pady=6)

        # 4. Início / Offset
        lbl_offset = ctk.CTkLabel(
            self.grid_frame,
            text="Iniciar a partir do segundo:",
            font=ctk.CTkFont(size=12)
        )
        lbl_offset.grid(row=3, column=0, sticky="w", padx=(0, 10), pady=6)

        self.stepper_offset = StepperEntry(
            self.grid_frame,
            initial_value=0.0,
            step=1.0,
            min_value=0.0,
            max_value=3600.0,
            is_float=True,
            on_change=self._notify_change
        )
        self.stepper_offset.grid(row=3, column=1, sticky="w", pady=6)

        lbl_offset_hint = ctk.CTkLabel(
            self.grid_frame,
            text="(ex: 0s = começa no início do vídeo)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        lbl_offset_hint.grid(row=3, column=2, sticky="w", padx=10, pady=6)

    def _notify_change(self):
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

    def get_config(self) -> Dict[str, Any]:
        return {
            "burst_cycle": self.stepper_cycle.get_value(),
            "burst_count": self.stepper_burst_count.get_value(),
            "burst_spacing": self.stepper_spacing.get_value(),
            "burst_offset": self.stepper_offset.get_value()
        }
