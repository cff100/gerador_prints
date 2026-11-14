"""
Componente de interface para o Modo 3: Amostragem Aleatória & Refinamento ao Redor.
"""
import customtkinter as ctk
from typing import Callable, List, Optional, Dict, Any
from src.core.video_processor import VideoProcessor
from src.gui.components.stepper_entry import StepperEntry

class ModeRandomFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_change: Optional[Callable[[], None]] = None,
        on_refine_requested: Optional[Callable[[], None]] = None,
        on_select_all: Optional[Callable[[], None]] = None,
        on_clear_selection: Optional[Callable[[], None]] = None,
        on_delete_selected: Optional[Callable[[], None]] = None,
        on_move_selected: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_change = on_change
        self.on_refine_requested = on_refine_requested
        self.on_select_all = on_select_all
        self.on_clear_selection = on_clear_selection
        self.on_delete_selected = on_delete_selected
        self.on_move_selected = on_move_selected

        self.selected_gallery_count = 0

        self._create_widgets()

    def _create_widgets(self):
        # Título principal
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
            text_color=("gray30", "gray70"),
            wraplength=380,
            justify="left"
        )
        lbl_desc.pack(anchor="w", padx=10, pady=(0, 8))

        # ==========================================
        # ETAPA 1: AMOSTRAGEM ALEATÓRIA
        # ==========================================
        box_step1 = ctk.CTkFrame(self, corner_radius=6)
        box_step1.pack(fill="x", padx=10, pady=(0, 8))

        lbl_s1 = ctk.CTkLabel(
            box_step1,
            text="Etapa 1: Amostragem Inicial",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        lbl_s1.pack(anchor="w", padx=8, pady=(6, 4))

        count_frame = ctk.CTkFrame(box_step1, fg_color="transparent")
        count_frame.pack(fill="x", padx=8, pady=(0, 6))

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
        lbl_stratified.pack(anchor="w", padx=8, pady=(0, 6))

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
        lbl_s2.pack(anchor="w", padx=8, pady=(6, 4))

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
            text="ex: ±2s",
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray60")
        )
        lbl_win_hint.pack(side="left", padx=6)

        # Quantidade por ponto
        per_point_frame = ctk.CTkFrame(box_step2, fg_color="transparent")
        per_point_frame.pack(fill="x", padx=8, pady=(0, 6))

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

        # Controles de seleção rápida da galeria
        sel_ctrl_frame = ctk.CTkFrame(box_step2, fg_color="transparent")
        sel_ctrl_frame.pack(fill="x", padx=8, pady=(2, 4))

        self.btn_select_all = ctk.CTkButton(
            sel_ctrl_frame,
            text="Marcar Todos",
            width=95,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("#4a4a4a", "#3a3a3a"),
            hover_color=("#5a5a5a", "#4a4a4a"),
            command=self._handle_select_all
        )
        self.btn_select_all.pack(side="left", padx=(0, 6))

        self.btn_clear_sel = ctk.CTkButton(
            sel_ctrl_frame,
            text="Desmarcar Todos",
            width=105,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("#4a4a4a", "#3a3a3a"),
            hover_color=("#5a5a5a", "#4a4a4a"),
            command=self._handle_clear_selection
        )
        self.btn_clear_sel.pack(side="left")

        self.btn_move_selected = ctk.CTkButton(
            sel_ctrl_frame,
            text="📁 Mover",
            width=80,
            height=24,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#2563eb", "#1d4ed8"),
            hover_color=("#3b82f6", "#2563eb"),
            state="disabled",
            command=self._handle_move_selected
        )
        self.btn_move_selected.pack(side="left", padx=(6, 0))

        self.btn_delete_selected = ctk.CTkButton(
            sel_ctrl_frame,
            text="🗑 Apagar",
            width=80,
            height=24,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#c0392b", "#962d22"),
            hover_color=("#e74c3c", "#c0392b"),
            state="disabled",
            command=self._handle_delete_selected
        )
        self.btn_delete_selected.pack(side="left", padx=(6, 0))

        # Indicador de prints selecionados
        self.lbl_selected_status = ctk.CTkLabel(
            box_step2,
            text="Nenhum print selecionado na galeria.",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray40", "gray60")
        )
        self.lbl_selected_status.pack(anchor="w", padx=8, pady=(4, 6))

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
        self.btn_refine_action.pack(fill="x", padx=8, pady=(0, 8))

    def _notify_change(self):
        self._update_status_display()
        if self.on_change:
            self.on_change()

    def _handle_select_all(self):
        if self.on_select_all:
            self.on_select_all()

    def _handle_clear_selection(self):
        if self.on_clear_selection:
            self.on_clear_selection()

    def _handle_move_selected(self):
        if self.on_move_selected:
            self.on_move_selected()

    def _handle_delete_selected(self):
        if self.on_delete_selected:
            self.on_delete_selected()

    def _handle_refine_requested(self):
        if self.on_refine_requested:
            self.on_refine_requested()

    def update_selection_count(self, count: int):
        """Atualiza a contagem de itens selecionados e o estado do botão de refinamento."""
        self.selected_gallery_count = count
        self._update_status_display()

    def _update_status_display(self):
        pts = self.selected_gallery_count
        per_point = int(self.stepper_refine_count.get_value())
        total_to_generate = pts * per_point

        if pts == 0:
            self.lbl_selected_status.configure(
                text="Nenhum print selecionado na galeria.",
                text_color=("gray40", "gray60")
            )
            self.btn_refine_action.configure(
                state="disabled",
                text="🎯 Gerar Prints ao Redor (0 selecionados)"
            )
            self.btn_move_selected.configure(
                state="disabled",
                text="📁 Mover"
            )
            self.btn_delete_selected.configure(
                state="disabled",
                text="🗑 Apagar"
            )
        else:
            self.lbl_selected_status.configure(
                text=f"{pts} print(s) selecionado(s) na galeria (Total: {total_to_generate} frames)",
                text_color=("#0284c7", "#38bdf8")
            )
            self.btn_refine_action.configure(
                state="normal",
                text=f"🎯 Gerar Prints ao Redor ({total_to_generate} frames)"
            )
            self.btn_move_selected.configure(
                state="normal",
                text=f"📁 Mover ({pts})"
            )
            self.btn_delete_selected.configure(
                state="normal",
                text=f"🗑 Apagar ({pts})"
            )

    def set_processing(self, is_processing: bool):
        """Habilita ou desabilita botões durante o processamento."""
        if is_processing:
            self.btn_refine_action.configure(state="disabled")
            self.btn_select_all.configure(state="disabled")
            self.btn_clear_sel.configure(state="disabled")
            self.btn_move_selected.configure(state="disabled")
            self.btn_delete_selected.configure(state="disabled")
        else:
            self.btn_select_all.configure(state="normal")
            self.btn_clear_sel.configure(state="normal")
            self._update_status_display()

    def get_timestamps(self, duration: float) -> List[float]:
        """Gera os timestamps aleatórios da Etapa 1."""
        if duration <= 0:
            return []
        count = int(self.stepper_random_count.get_value())
        return VideoProcessor.calculate_stratified_random_timestamps(duration, count)

    def get_refinement_timestamps(self, base_timestamps: List[float], duration: float) -> List[float]:
        """Gera os timestamps de refinamento da Etapa 2 ao redor dos pontos base."""
        if duration <= 0 or not base_timestamps:
            return []
        window = float(self.stepper_refine_window.get_value())
        count = int(self.stepper_refine_count.get_value())
        return VideoProcessor.calculate_refinement_timestamps(base_timestamps, window, count, duration)

    def load_config(self, config: Dict[str, Any]):
        self.stepper_random_count.set_value(config.get("random_count", 15))
        self.stepper_refine_window.set_value(config.get("refine_window", 2.0))
        self.stepper_refine_count.set_value(config.get("refine_count", 5))
        self._update_status_display()

    def get_config(self) -> Dict[str, Any]:
        return {
            "random_count": self.stepper_random_count.get_value(),
            "refine_window": self.stepper_refine_window.get_value(),
            "refine_count": self.stepper_refine_count.get_value()
        }

