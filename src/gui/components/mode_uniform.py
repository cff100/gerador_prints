"""
Componente de interface para o Modo 1: Espaçamento Uniforme com Stepper e Prévia Dinâmica.
"""
import customtkinter as ctk
from typing import Callable, List, Optional, Dict, Any
from src.core.video_processor import VideoProcessor
from src.core.utils import format_timestamp_display
from src.gui.components.stepper_entry import StepperEntry


class ModeUniformFrame(ctk.CTkFrame):
    def __init__(self, master, on_change: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_change = on_change
        self.video_duration: Optional[float] = None
        self.submode_var = ctk.StringVar(value="interval")

        self._create_widgets()
        self._update_preview()

    def _create_widgets(self):
        self.title_label = ctk.CTkLabel(
            self,
            text="Configuração de Espaçamento Uniforme",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.submode_seg = ctk.CTkSegmentedButton(
            self,
            values=["Por Intervalo de Tempo", "Por Quantidade Total de Prints"],
            command=self._on_submode_change
        )
        self.submode_seg.set("Por Intervalo de Tempo")
        self.submode_seg.pack(fill="x", padx=10, pady=5)

        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.pack(fill="x", padx=10, pady=(6, 2))

        # --- Campo Intervalo com Stepper ---
        self.interval_container = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.lbl_interval = ctk.CTkLabel(
            self.interval_container,
            text="Intervalo entre prints (segundos):",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_interval.pack(side="left", padx=(0, 10))

        self.stepper_interval = StepperEntry(
            self.interval_container,
            initial_value=5.0,
            step=1.0,
            min_value=0.1,
            max_value=3600.0,
            is_float=True,
            entry_width=70,
            on_change=self._notify_change
        )
        self.stepper_interval.pack(side="left")

        self.lbl_interval_hint = ctk.CTkLabel(
            self.interval_container,
            text="(ex: 5s = 1 print a cada 5 segundos)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.lbl_interval_hint.pack(side="left", padx=10)

        # --- Campo Quantidade Total com Stepper ---
        self.count_container = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.lbl_count = ctk.CTkLabel(
            self.count_container,
            text="Quantidade total de prints:",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_count.pack(side="left", padx=(0, 10))

        self.stepper_count = StepperEntry(
            self.count_container,
            initial_value=20,
            step=5,
            min_value=1,
            max_value=5000,
            is_float=False,
            entry_width=70,
            on_change=self._notify_change
        )
        self.stepper_count.pack(side="left")

        self.lbl_count_hint = ctk.CTkLabel(
            self.count_container,
            text="(distribuídos igualmente pelo vídeo)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.lbl_count_hint.pack(side="left", padx=10)

        self.interval_container.pack(fill="x", pady=4)

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
        """Calcula e exibe a simulação em tempo real dos parâmetros atuais."""
        is_mock = self.video_duration is None or self.video_duration <= 0
        dur = 600.0 if is_mock else float(self.video_duration)
        submode = self.submode_var.get()

        prefix_tag = "📌 [Exemplo com vídeo de 10 min]\n" if is_mock else f"🎬 [Vídeo atual: {format_timestamp_display(dur)}]\n"

        if submode == "interval":
            interval = float(self.stepper_interval.get_value())
            ts = VideoProcessor.calculate_uniform_timestamps(dur, "interval", interval)
            count = len(ts)
            sample_pts = [format_timestamp_display(t) for t in ts[:4]]
            pts_str = ", ".join(sample_pts)
            if count > 4:
                pts_str += f"... até {format_timestamp_display(ts[-1])}"

            body = (
                f"{prefix_tag}"
                f"• Extrai 1 print a cada {interval:.1f} segundo(s).\n"
                f"• Sequência inicial: {pts_str}\n"
                f"• Total calculado: {count} print(s) ao longo do vídeo."
            )
        else:
            count = int(self.stepper_count.get_value())
            ts = VideoProcessor.calculate_uniform_timestamps(dur, "count", count)
            step_sec = dur / (count - 1) if count > 1 else dur
            sample_pts = [format_timestamp_display(t) for t in ts[:3]]
            pts_str = ", ".join(sample_pts)
            if count > 3:
                pts_str += f"... até {format_timestamp_display(ts[-1])}"

            body = (
                f"{prefix_tag}"
                f"• Divide o vídeo em {count} momentos com passo exato de {step_sec:.1f}s entre cada um.\n"
                f"• Sequência de prints: {pts_str}\n"
                f"• Abrange do primeiro segundo (00:00.0) até o final exato do vídeo."
            )

        self.lbl_preview_body.configure(text=body)

    def _on_submode_change(self, value: str):
        if value == "Por Intervalo de Tempo":
            self.submode_var.set("interval")
            self.count_container.pack_forget()
            self.interval_container.pack(fill="x", pady=4)
        else:
            self.submode_var.set("count")
            self.interval_container.pack_forget()
            self.count_container.pack(fill="x", pady=4)

        self._notify_change()

    def _notify_change(self):
        self._update_preview()
        if self.on_change:
            self.on_change()

    def get_timestamps(self, duration: float) -> List[float]:
        if duration <= 0:
            return []

        submode = self.submode_var.get()
        if submode == "interval":
            val = float(self.stepper_interval.get_value())
            return VideoProcessor.calculate_uniform_timestamps(duration, "interval", val)
        else:
            val = int(self.stepper_count.get_value())
            return VideoProcessor.calculate_uniform_timestamps(duration, "count", val)

    def load_config(self, config: Dict[str, Any]):
        submode_str = config.get("uniform_submode", "Por Intervalo de Tempo")
        self.submode_seg.set(submode_str)
        self._on_submode_change(submode_str)
        self.stepper_interval.set_value(config.get("uniform_interval", 5.0))
        self.stepper_count.set_value(config.get("uniform_count", 20))
        self._update_preview()

    def get_config(self) -> Dict[str, Any]:
        return {
            "uniform_submode": self.submode_seg.get(),
            "uniform_interval": self.stepper_interval.get_value(),
            "uniform_count": self.stepper_count.get_value()
        }
