"""
Componente de interface para o Modo 3: Amostragem Aleatória & Refinamento ao Redor.
"""
import customtkinter as ctk
from typing import Callable, List, Optional, Dict, Any
from src.core.video_processor import VideoProcessor
from src.core.utils import format_timestamp_display
from src.gui.components.stepper_entry import StepperEntry


class ModeRandomFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_change: Optional[Callable[[], None]] = None,
        on_refine_requested: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_change = on_change
        self.on_refine_requested = on_refine_requested

        self.video_duration: Optional[float] = None
        self.selected_gallery_count = 0
        self.selected_timestamps: List[float] = []
        self.existing_gallery_timestamps: List[float] = []

        self._create_widgets()
        self._update_preview()

    def _create_widgets(self):
        self.title_label = ctk.CTkLabel(
            self,
            text="Amostragem Aleatória & Refino ao Redor",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_label.pack(anchor="w", padx=10, pady=(8, 2))

        lbl_desc = ctk.CTkLabel(
            self,
            text="Gere prints aleatórios ao longo do vídeo e selecione os melhores na galeria para capturar frames adjacentes.",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            wraplength=380,
            justify="left"
        )
        lbl_desc.pack(anchor="w", padx=10, pady=(0, 6))

        # ==========================================
        # ETAPA 1: AMOSTRAGEM ALEATÓRIA
        # ==========================================
        box_step1 = ctk.CTkFrame(self, corner_radius=6)
        box_step1.pack(fill="x", padx=10, pady=(0, 6))

        lbl_s1 = ctk.CTkLabel(
            box_step1,
            text="Etapa 1: Amostragem Inicial Equilibrada",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        lbl_s1.pack(anchor="w", padx=8, pady=(4, 2))

        count_frame = ctk.CTkFrame(box_step1, fg_color="transparent")
        count_frame.pack(fill="x", padx=8, pady=(0, 4))

        lbl_count = ctk.CTkLabel(count_frame, text="Quantidade de prints:", font=ctk.CTkFont(size=12))
        lbl_count.pack(side="left", padx=(0, 8))

        self.stepper_random_count = StepperEntry(
            count_frame,
            initial_value=15,
            step=1,
            min_value=1,
            max_value=1000,
            is_float=False,
            entry_width=65,
            on_change=self._notify_change
        )
        self.stepper_random_count.pack(side="left")

        lbl_stratified = ctk.CTkLabel(
            box_step1,
            text="(Distribuição estratificada: cobre todo o vídeo sem aglomeração)",
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray60")
        )
        lbl_stratified.pack(anchor="w", padx=8, pady=(0, 4))

        # ==========================================
        # ETAPA 2: REFINAMENTO AO REDOR DOS SELECIONADOS
        # ==========================================
        box_step2 = ctk.CTkFrame(self, corner_radius=6)
        box_step2.pack(fill="x", padx=10, pady=(0, 6))

        lbl_s2 = ctk.CTkLabel(
            box_step2,
            text="Etapa 2: Refinamento ao Redor dos Selecionados",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        lbl_s2.pack(anchor="w", padx=8, pady=(4, 2))

        # Janela de tempo (± segundos)
        win_frame = ctk.CTkFrame(box_step2, fg_color="transparent")
        win_frame.pack(fill="x", padx=8, pady=(0, 4))

        lbl_win = ctk.CTkLabel(win_frame, text="Janela de busca (± seg):", font=ctk.CTkFont(size=12))
        lbl_win.pack(side="left", padx=(0, 8))

        self.stepper_refine_window = StepperEntry(
            win_frame,
            initial_value=2.0,
            step=0.5,
            min_value=0.1,
            max_value=120.0,
            is_float=True,
            entry_width=65,
            on_change=self._notify_change
        )
        self.stepper_refine_window.pack(side="left")

        lbl_win_hint = ctk.CTkLabel(
            win_frame,
            text="(ex: ±2s ao redor de cada print)",
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray60")
        )
        lbl_win_hint.pack(side="left", padx=6)

        # Quantidade por ponto
        per_point_frame = ctk.CTkFrame(box_step2, fg_color="transparent")
        per_point_frame.pack(fill="x", padx=8, pady=(0, 4))

        lbl_per = ctk.CTkLabel(per_point_frame, text="Prints por ponto:", font=ctk.CTkFont(size=12))
        lbl_per.pack(side="left", padx=(0, 8))

        self.stepper_refine_count = StepperEntry(
            per_point_frame,
            initial_value=5,
            step=1,
            min_value=1,
            max_value=50,
            is_float=False,
            entry_width=65,
            on_change=self._notify_change
        )
        self.stepper_refine_count.pack(side="left")

        lbl_per_hint = ctk.CTkLabel(
            per_point_frame,
            text="frames",
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray60")
        )
        lbl_per_hint.pack(side="left", padx=6)

        # Indicador de prints selecionados
        self.lbl_selected_status = ctk.CTkLabel(
            box_step2,
            text="Nenhum print selecionado na galeria.",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray40", "gray60")
        )
        self.lbl_selected_status.pack(anchor="w", padx=8, pady=(4, 4))

        # Botão de Ação do Refinamento
        self.btn_refine_action = ctk.CTkButton(
            box_step2,
            text="🎯 Gerar Prints ao Redor",
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            state="disabled",
            command=self._handle_refine_requested
        )
        self.btn_refine_action.pack(fill="x", padx=8, pady=(0, 6))

        # ==========================================
        # CARD DE SIMULAÇÃO / PRÉVIA EM TEMPO REAL
        # ==========================================
        self.preview_card = ctk.CTkFrame(self, fg_color=("#f1f5f9", "#1e293b"), corner_radius=8)
        self.preview_card.pack(fill="x", padx=10, pady=(2, 10))

        self.lbl_preview_title = ctk.CTkLabel(
            self.preview_card,
            text="💡 Como vai funcionar na prática:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#0284c7", "#38bdf8")
        )
        self.lbl_preview_title.pack(anchor="w", padx=10, pady=(6, 2))

        self.lbl_preview_body = ctk.CTkLabel(
            self.preview_card,
            text="",
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=380
        )
        self.lbl_preview_body.pack(anchor="w", padx=10, pady=(0, 6))

    def set_duration(self, duration: Optional[float]):
        """Atualiza a duração do vídeo ativo para refletir na prévia."""
        self.video_duration = duration
        self._update_preview()

    def update_selection(
        self,
        count: int,
        timestamps: Optional[List[float]] = None,
        existing_timestamps: Optional[List[float]] = None
    ):
        """Atualiza a quantidade, instantes dos itens marcados e lista total da galeria."""
        self.selected_gallery_count = count
        self.selected_timestamps = timestamps or []
        if existing_timestamps is not None:
            self.existing_gallery_timestamps = existing_timestamps
        self._update_status_display()
        self._update_preview()

    def update_selection_count(self, count: int):
        """Compatibilidade para atualização simples da contagem."""
        self.selected_gallery_count = count
        self._update_status_display()
        self._update_preview()

    def _update_preview(self):
        """Calcula e exibe a explicação da janela de busca e limites em tempo real."""
        is_mock = self.video_duration is None or self.video_duration <= 0
        dur = 600.0 if is_mock else float(self.video_duration)

        rnd_count = int(self.stepper_random_count.get_value())
        slice_sec = dur / rnd_count if rnd_count > 0 else 0
        window = float(self.stepper_refine_window.get_value())
        per_pt = int(self.stepper_refine_count.get_value())

        prefix_tag = "📌 [Exemplo com vídeo de 10 min]\n" if is_mock else f"🎬 [Vídeo atual: {format_timestamp_display(dur)}]\n"

        # Explicação Etapa 1
        txt_s1 = f"• Etapa 1: Divide o vídeo em {rnd_count} fatias de ~{slice_sec:.1f}s e sorteia 1 instante em cada, cobrindo o vídeo todo sem aglomerar."

        # Explicação Etapa 2 (com ou sem seleção ativa)
        if self.selected_timestamps:
            ref_t = self.selected_timestamps[0]
            start_t = max(0.0, ref_t - window)
            end_t = min(dur, ref_t + window)
            exclude = self.existing_gallery_timestamps or self.selected_timestamps
            pts = VideoProcessor.calculate_refinement_timestamps([ref_t], window, per_pt, dur, exclude_timestamps=exclude)
            pts_str = ", ".join(format_timestamp_display(t) for t in pts[:4])
            if len(pts) > 4:
                pts_str += f"... ({len(pts)} novos frames)"
            elif not pts:
                pts_str = "nenhum frame novo (todos já existem)"

            edge_note = ""
            if (ref_t - window) < 0:
                edge_note = " (trava de início ativada: não gera tempo negativo!)"
            elif (ref_t + window) > dur:
                edge_note = " (trava de fim ativada: não ultrapassa a duração!)"

            txt_s2 = (
                f"• Etapa 2 (Ex: seu print em {format_timestamp_display(ref_t)}):\n"
                f"  Busca ±{window:.1f}s -> janela [{format_timestamp_display(start_t)} até {format_timestamp_display(end_t)}]{edge_note}.\n"
                f"  Gera novos frames espaçados (excluindo o original): {pts_str}."
            )
        else:
            sample_center = 10.0
            start_t = max(0.0, sample_center - window)
            end_t = min(dur, sample_center + window)
            step_calc = (end_t - start_t) / (per_pt - 1) if per_pt > 1 else 0.0

            txt_s2 = (
                f"• Etapa 2 (Exemplo didático para um print aos 00:10.0):\n"
                f"  Janela ±{window:.1f}s -> extrai {per_pt} fotos entre {format_timestamp_display(start_t)} e {format_timestamp_display(end_t)} (passo de {step_calc:.1f}s).\n"
                f"  Trava de borda ativa: nunca gera tempo negativo (abaixo de 0s) ou acima do fim do vídeo."
            )

        body = f"{prefix_tag}{txt_s1}\n{txt_s2}"
        self.lbl_preview_body.configure(text=body)

    def _notify_change(self):
        self._update_status_display()
        self._update_preview()
        if self.on_change:
            self.on_change()

    def _handle_refine_requested(self):
        if self.on_refine_requested:
            self.on_refine_requested()

    def _update_status_display(self):
        pts = self.selected_gallery_count
        if pts == 0 or not self.selected_timestamps:
            self.lbl_selected_status.configure(
                text="Nenhum print selecionado na galeria.",
                text_color=("gray40", "gray60")
            )
            self.btn_refine_action.configure(
                state="disabled",
                text="🎯 Gerar Prints ao Redor (0 selecionados)"
            )
        else:
            window = float(self.stepper_refine_window.get_value())
            per_point = int(self.stepper_refine_count.get_value())
            dur = self.video_duration or 600.0
            exclude = self.existing_gallery_timestamps or self.selected_timestamps
            timestamps_to_gen = VideoProcessor.calculate_refinement_timestamps(
                self.selected_timestamps, window, per_point, dur, exclude_timestamps=exclude
            )
            total_to_generate = len(timestamps_to_gen)

            self.lbl_selected_status.configure(
                text=f"{pts} print(s) selecionado(s) na galeria (Inéditos: {total_to_generate} frames)",
                text_color=("#0284c7", "#38bdf8")
            )
            self.btn_refine_action.configure(
                state="normal" if total_to_generate > 0 else "disabled",
                text=f"🎯 Gerar Prints ao Redor ({total_to_generate} novos frames)"
            )

    def set_processing(self, is_processing: bool):
        if is_processing:
            self.btn_refine_action.configure(state="disabled")
        else:
            self._update_status_display()

    def get_timestamps(self, duration: float) -> List[float]:
        if duration <= 0:
            return []
        count = int(self.stepper_random_count.get_value())
        return VideoProcessor.calculate_stratified_random_timestamps(duration, count)

    def get_refinement_timestamps(
        self,
        base_timestamps: List[float],
        duration: float,
        exclude_timestamps: Optional[List[float]] = None
    ) -> List[float]:
        if duration <= 0 or not base_timestamps:
            return []
        window = float(self.stepper_refine_window.get_value())
        count = int(self.stepper_refine_count.get_value())
        exclude = exclude_timestamps if exclude_timestamps is not None else self.existing_gallery_timestamps
        return VideoProcessor.calculate_refinement_timestamps(
            base_timestamps, window, count, duration, exclude_timestamps=exclude
        )

    def load_config(self, config: Dict[str, Any]):
        self.stepper_random_count.set_value(config.get("random_count", 15))
        self.stepper_refine_window.set_value(config.get("refine_window", 2.0))
        self.stepper_refine_count.set_value(config.get("refine_count", 5))
        self._update_status_display()
        self._update_preview()

    def get_config(self) -> Dict[str, Any]:
        return {
            "random_count": self.stepper_random_count.get_value(),
            "refine_window": self.stepper_refine_window.get_value(),
            "refine_count": self.stepper_refine_count.get_value()
        }
