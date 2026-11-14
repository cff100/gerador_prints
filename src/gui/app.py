"""
Janela Principal da Aplicação Gerador de Prints de Vídeo (CustomTkinter).
"""
import os
import queue
import threading
import subprocess
import platform
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from src.core.utils import (
    get_video_info,
    format_timestamp_display,
    sanitize_filename
)
from src.core.video_processor import VideoProcessor
from src.core.config_manager import load_config, save_config, reset_to_defaults
from src.gui.components.mode_uniform import ModeUniformFrame
from src.gui.components.mode_burst import ModeBurstFrame
from src.gui.components.mode_random import ModeRandomFrame
from src.gui.components.gallery import GalleryFrame
from src.gui.components.dialog_move import MovePrintsDialog
from src.gui.components.progress_bar import ProgressSection

# Configurações globais de tema
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gerador Automático de Prints de Vídeo")
        self.geometry("1100x780")
        self.minsize(950, 680)

        # Ícone da janela e barra de tarefas
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Estado da aplicação
        self.video_info = None
        self.is_processing = False
        self.stop_event = threading.Event()
        self.msg_queue = queue.Queue()

        self._create_layout()
        self._load_and_apply_config()
        self._check_queue()

        # Atalhos de teclado
        self.bind("<Delete>", lambda e: self.gallery.delete_selected() if self.gallery.get_selected_items() else None)
        self.bind("<Control-m>", lambda e: self._open_move_dialog() if self.gallery.get_selected_items() else None)
        self.bind("<Control-M>", lambda e: self._open_move_dialog() if self.gallery.get_selected_items() else None)

    def _create_layout(self):
        # Grid Principal: 2 colunas
        self.columnconfigure(0, weight=4, minsize=420)
        self.columnconfigure(1, weight=6, minsize=500)
        self.rowconfigure(0, weight=1)

        # ==========================================
        # PAINEL ESQUERDO: CONFIGURAÇÕES E CONTROLES
        # ==========================================
        self.left_scroll = ctk.CTkScrollableFrame(self, label_text="Configurações de Extração")
        self.left_scroll.grid(row=0, column=0, sticky="nsew", padx=(15, 7), pady=15)
        self.left_scroll.columnconfigure(0, weight=1)

        # 1. Seção Seleção de Vídeo
        self._build_video_selection_section()

        # 2. Seção Pasta de Destino & Formato
        self._build_output_settings_section()

        # 3. Seção Seleção de Modo (Abas)
        self._build_mode_section()

        # 4. Seção de Gerenciamento de Padrões (Salvar / Restaurar)
        self._build_config_management_section()

        # 5. Painel de Estimativa e Ações
        self._build_actions_section()

        # ==========================================
        # PAINEL DIREITO: PROGRESSO E GALERIA
        # ==========================================
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(7, 15), pady=15)
        self.right_frame.columnconfigure(0, weight=1)
        self.right_frame.rowconfigure(2, weight=1)

        # Barra de Progresso
        self.progress_section = ProgressSection(self.right_frame)
        self.progress_section.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Cabeçalho da Galeria com Ações Rápidas (Marcar, Desmarcar e Apagar)
        gallery_header = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        gallery_header.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 2))
        gallery_header.columnconfigure(0, weight=1)

        self.gallery_label = ctk.CTkLabel(
            gallery_header,
            text="Galeria de Prints:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.gallery_label.grid(row=0, column=0, sticky="w")

        gallery_actions = ctk.CTkFrame(gallery_header, fg_color="transparent")
        gallery_actions.grid(row=0, column=1, sticky="e")

        self.btn_gal_select_all = ctk.CTkButton(
            gallery_actions,
            text="Marcar Todos",
            width=85,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("#4a4a4a", "#3a3a3a"),
            hover_color=("#5a5a5a", "#4a4a4a"),
            command=lambda: self.gallery.select_all()
        )
        self.btn_gal_select_all.pack(side="left", padx=(0, 4))

        self.btn_gal_clear_sel = ctk.CTkButton(
            gallery_actions,
            text="Desmarcar",
            width=75,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("#4a4a4a", "#3a3a3a"),
            hover_color=("#5a5a5a", "#4a4a4a"),
            command=lambda: self.gallery.clear_selection()
        )
        self.btn_gal_clear_sel.pack(side="left", padx=(0, 4))

        self.btn_gal_move = ctk.CTkButton(
            gallery_actions,
            text="📁 Mover",
            width=85,
            height=24,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#2563eb", "#1d4ed8"),
            hover_color=("#3b82f6", "#2563eb"),
            state="disabled",
            command=self._open_move_dialog
        )
        self.btn_gal_move.pack(side="left", padx=(0, 4))

        self.btn_gal_delete = ctk.CTkButton(
            gallery_actions,
            text="🗑 Apagar",
            width=85,
            height=24,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#c0392b", "#962d22"),
            hover_color=("#e74c3c", "#c0392b"),
            state="disabled",
            command=lambda: self.gallery.delete_selected()
        )
        self.btn_gal_delete.pack(side="left")

        self.gallery = GalleryFrame(self.right_frame, on_selection_change=self._on_gallery_selection_change)
        self.gallery.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))

    def _build_video_selection_section(self):
        sec = ctk.CTkFrame(self.left_scroll)
        sec.pack(fill="x", pady=(0, 10))

        lbl = ctk.CTkLabel(sec, text="1. Vídeo de Origem", font=ctk.CTkFont(size=13, weight="bold"))
        lbl.pack(anchor="w", padx=10, pady=(8, 4))

        picker_frame = ctk.CTkFrame(sec, fg_color="transparent")
        picker_frame.pack(fill="x", padx=10, pady=4)
        picker_frame.columnconfigure(0, weight=1)

        self.entry_video_path = ctk.CTkEntry(
            picker_frame,
            placeholder_text="Nenhum vídeo selecionado...",
            state="readonly"
        )
        self.entry_video_path.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_select_video = ctk.CTkButton(
            picker_frame,
            text="📁 Selecionar",
            width=100,
            command=self._choose_video
        )
        self.btn_select_video.grid(row=0, column=1)

        # Card de metadados do vídeo
        self.meta_frame = ctk.CTkFrame(sec, fg_color=("#e5e5e5", "#2b2b2b"), corner_radius=6)
        self.lbl_meta_duration = ctk.CTkLabel(self.meta_frame, text="⏱ Duração: --:--", font=ctk.CTkFont(size=11))
        self.lbl_meta_duration.pack(side="left", padx=10, pady=4)
        self.lbl_meta_res = ctk.CTkLabel(self.meta_frame, text="📺 Resolução: --x--", font=ctk.CTkFont(size=11))
        self.lbl_meta_res.pack(side="left", padx=10, pady=4)
        self.lbl_meta_fps = ctk.CTkLabel(self.meta_frame, text="⚡ FPS: --", font=ctk.CTkFont(size=11))
        self.lbl_meta_fps.pack(side="left", padx=10, pady=4)

    def _build_output_settings_section(self):
        sec = ctk.CTkFrame(self.left_scroll)
        sec.pack(fill="x", pady=(0, 10))

        lbl = ctk.CTkLabel(sec, text="2. Destino e Formato", font=ctk.CTkFont(size=13, weight="bold"))
        lbl.pack(anchor="w", padx=10, pady=(8, 4))

        lbl_dest = ctk.CTkLabel(sec, text="Pasta de Saída:", font=ctk.CTkFont(size=11))
        lbl_dest.pack(anchor="w", padx=10)

        dest_frame = ctk.CTkFrame(sec, fg_color="transparent")
        dest_frame.pack(fill="x", padx=10, pady=(2, 8))
        dest_frame.columnconfigure(0, weight=1)

        self.entry_output_dir = ctk.CTkEntry(dest_frame, placeholder_text="Pasta onde os prints serão salvos...")
        self.entry_output_dir.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        btn_dest = ctk.CTkButton(
            dest_frame,
            text="Procurar...",
            width=90,
            command=self._choose_output_dir
        )
        btn_dest.grid(row=0, column=1)

        # Formato e Qualidade
        fmt_frame = ctk.CTkFrame(sec, fg_color="transparent")
        fmt_frame.pack(fill="x", padx=10, pady=(0, 8))

        lbl_fmt = ctk.CTkLabel(fmt_frame, text="Formato:", font=ctk.CTkFont(size=11))
        lbl_fmt.pack(side="left", padx=(0, 6))

        self.opt_format = ctk.CTkOptionMenu(
            fmt_frame,
            values=["PNG", "JPEG"],
            width=90,
            command=self._on_format_change
        )
        self.opt_format.pack(side="left", padx=(0, 15))

        self.lbl_quality = ctk.CTkLabel(fmt_frame, text="Qualidade JPG (95%):", font=ctk.CTkFont(size=11))
        self.slider_quality = ctk.CTkSlider(
            fmt_frame,
            from_=30,
            to=100,
            number_of_steps=14,
            width=120,
            command=self._on_quality_slider
        )
        self.slider_quality.set(95)

        # Prefixo
        prefix_frame = ctk.CTkFrame(sec, fg_color="transparent")
        prefix_frame.pack(fill="x", padx=10, pady=(0, 8))

        lbl_prefix = ctk.CTkLabel(prefix_frame, text="Prefixo do arquivo:", font=ctk.CTkFont(size=11))
        lbl_prefix.pack(side="left", padx=(0, 6))

        self.entry_prefix = ctk.CTkEntry(prefix_frame, width=140)
        self.entry_prefix.insert(0, "print")
        self.entry_prefix.pack(side="left")

    def _build_mode_section(self):
        sec = ctk.CTkFrame(self.left_scroll)
        sec.pack(fill="x", pady=(0, 10))

        lbl = ctk.CTkLabel(sec, text="3. Modo de Captura", font=ctk.CTkFont(size=13, weight="bold"))
        lbl.pack(anchor="w", padx=10, pady=(8, 4))

        self.tabview_modes = ctk.CTkTabview(sec, command=self._update_estimation)
        self.tabview_modes.pack(fill="x", padx=10, pady=(0, 8))

        self.tab_uniform = self.tabview_modes.add("Modo 1: Espaçamento Uniforme")
        self.tab_burst = self.tabview_modes.add("Modo 2: Rajadas Periódicas")
        self.tab_random = self.tabview_modes.add("Modo 3: Aleatório & Refino")

        self.comp_uniform = ModeUniformFrame(self.tab_uniform, on_change=self._update_estimation)
        self.comp_uniform.pack(fill="both", expand=True)

        self.comp_burst = ModeBurstFrame(self.tab_burst, on_change=self._update_estimation)
        self.comp_burst.pack(fill="both", expand=True)

        self.comp_random = ModeRandomFrame(
            self.tab_random,
            on_change=self._update_estimation,
            on_refine_requested=self._start_refinement,
            on_select_all=lambda: self.gallery.select_all(),
            on_clear_selection=lambda: self.gallery.clear_selection(),
            on_delete_selected=lambda: self.gallery.delete_selected(),
            on_move_selected=self._open_move_dialog
        )
        self.comp_random.pack(fill="both", expand=True)

    def _build_config_management_section(self):
        sec = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        sec.pack(fill="x", pady=(0, 10))

        btn_frame = ctk.CTkFrame(sec, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        self.btn_save_default = ctk.CTkButton(
            btn_frame,
            text="💾 Salvar como Padrão",
            fg_color=("#2980b9", "#3498db"),
            hover_color=("#1c5980", "#2980b9"),
            height=30,
            command=self._save_defaults
        )
        self.btn_save_default.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_restore_default = ctk.CTkButton(
            btn_frame,
            text="🔄 Restaurar Padrões",
            fg_color=("#7f8c8d", "#95a5a6"),
            hover_color=("#6c7a7d", "#7f8c8d"),
            height=30,
            command=self._restore_defaults
        )
        self.btn_restore_default.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.lbl_config_toast = ctk.CTkLabel(
            sec,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#2ecc71"
        )
        self.lbl_config_toast.pack(anchor="center", pady=(4, 0))

    def _build_actions_section(self):
        sec = ctk.CTkFrame(self.left_scroll)
        sec.pack(fill="x", pady=(0, 10))

        self.lbl_estimation = ctk.CTkLabel(
            sec,
            text="🎯 Selecione um vídeo para calcular a estimativa de prints",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#3a86ff"
        )
        self.lbl_estimation.pack(anchor="center", padx=10, pady=10)

        btn_frame = ctk.CTkFrame(sec, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        self.btn_start = ctk.CTkButton(
            btn_frame,
            text="▶ Iniciar Extração",
            fg_color="#2ecc71",
            hover_color="#27ae60",
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            command=self._start_extraction
        )
        self.btn_start.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self.btn_cancel = ctk.CTkButton(
            btn_frame,
            text="⏹ Cancelar",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            height=32,
            state="disabled",
            command=self._cancel_extraction
        )
        self.btn_cancel.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        self.btn_open_folder = ctk.CTkButton(
            btn_frame,
            text="📂 Abrir Pasta",
            fg_color=("#3a3a3a", "#4a4a4a"),
            hover_color=("#555555", "#666666"),
            height=32,
            command=self._open_output_dir
        )
        self.btn_open_folder.grid(row=1, column=1, sticky="ew", padx=(4, 0))

    # ==========================================
    # GESTÃO DE CONFIGURAÇÕES PADRÃO (JSON)
    # ==========================================
    def _load_and_apply_config(self):
        cfg = load_config()
        self.comp_uniform.load_config(cfg)
        self.comp_burst.load_config(cfg)
        self.comp_random.load_config(cfg)

        active_tab = cfg.get("active_tab", "Modo 1: Espaçamento Uniforme")
        try:
            self.tabview_modes.set(active_tab)
        except Exception:
            self.tabview_modes.set("Modo 1: Espaçamento Uniforme")

        fmt = cfg.get("format", "PNG")
        self.opt_format.set(fmt)
        self._on_format_change(fmt)

        qual = cfg.get("jpeg_quality", 95)
        self.slider_quality.set(qual)
        self._on_quality_slider(qual)

        prefix = cfg.get("prefix", "print")
        self.entry_prefix.delete(0, "end")
        self.entry_prefix.insert(0, prefix)

        self._update_estimation()

    def _save_defaults(self):
        cfg = {}
        cfg.update(self.comp_uniform.get_config())
        cfg.update(self.comp_burst.get_config())
        cfg.update(self.comp_random.get_config())
        cfg["active_tab"] = self.tabview_modes.get()
        cfg["format"] = self.opt_format.get()
        cfg["jpeg_quality"] = int(self.slider_quality.get())
        cfg["prefix"] = self.entry_prefix.get().strip() or "print"

        if save_config(cfg):
            self._show_toast(" Configurações salvas como padrão!")
        else:
            self._show_toast(" Erro ao salvar padrão.", is_error=True)

    def _restore_defaults(self):
        cfg = reset_to_defaults()
        self._load_and_apply_config()
        self._show_toast(" Restaurado para os padrões de fábrica.")

    def _show_toast(self, text: str, is_error: bool = False):
        color = "#e74c3c" if is_error else "#2ecc71"
        self.lbl_config_toast.configure(text=text, text_color=color)
        self.after(3000, lambda: self.lbl_config_toast.configure(text=""))

    # ==========================================
    # EVENTOS E HANDLERS
    # ==========================================
    def _choose_video(self):
        filetypes = [
            ("Arquivos de Vídeo", "*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.m4v *.ts"),
            ("Todos os Arquivos", "*.*")
        ]
        chosen = filedialog.askopenfilename(title="Selecione o vídeo", filetypes=filetypes)
        if not chosen:
            return

        try:
            info = get_video_info(chosen)
            self.video_info = info

            self.entry_video_path.configure(state="normal")
            self.entry_video_path.delete(0, "end")
            self.entry_video_path.insert(0, chosen)
            self.entry_video_path.configure(state="readonly")

            self.lbl_meta_duration.configure(text=f"⏱ Duração: {info['duration_display']}")
            self.lbl_meta_res.configure(text=f"📺 Resolução: {info['width']}x{info['height']}")
            self.lbl_meta_fps.configure(text=f"⚡ FPS: {info['fps']:.1f}")
            self.meta_frame.pack(fill="x", padx=10, pady=(4, 8))

            video_dir = os.path.dirname(chosen)
            video_name_clean = sanitize_filename(os.path.splitext(info['filename'])[0])
            default_out = os.path.join(video_dir, f"prints_{video_name_clean}")
            
            self.entry_output_dir.delete(0, "end")
            self.entry_output_dir.insert(0, default_out)

            prefix = video_name_clean[:20] if video_name_clean else "print"
            self.entry_prefix.delete(0, "end")
            self.entry_prefix.insert(0, prefix)

            self._update_estimation()

        except Exception as e:
            messagebox.showerror("Erro ao abrir vídeo", f"Não foi possível ler o vídeo selecionado:\n{str(e)}")

    def _choose_output_dir(self):
        chosen = filedialog.askdirectory(title="Selecione a pasta de destino")
        if chosen:
            self.entry_output_dir.delete(0, "end")
            self.entry_output_dir.insert(0, chosen)

    def _on_format_change(self, value: str):
        if value == "JPEG":
            self.lbl_quality.pack(side="left", padx=(0, 6))
            self.slider_quality.pack(side="left")
        else:
            self.lbl_quality.pack_forget()
            self.slider_quality.pack_forget()

    def _on_quality_slider(self, value: float):
        val = int(value)
        self.lbl_quality.configure(text=f"Qualidade JPG ({val}%):")

    def _get_active_timestamps(self) -> list:
        if not self.video_info:
            return []
        duration = self.video_info["duration_sec"]
        current_tab = self.tabview_modes.get()
        if current_tab == "Modo 1: Espaçamento Uniforme":
            return self.comp_uniform.get_timestamps(duration)
        elif current_tab == "Modo 2: Rajadas Periódicas":
            return self.comp_burst.get_timestamps(duration)
        else:
            return self.comp_random.get_timestamps(duration)

    def _update_estimation(self):
        if not self.video_info:
            self.lbl_estimation.configure(
                text="🎯 Selecione um vídeo para calcular a estimativa de prints",
                text_color="#3a86ff"
            )
            return

        ts = self._get_active_timestamps()
        count = len(ts)
        self.lbl_estimation.configure(
            text=f"🎯 Total estimado para extração: {count} prints",
            text_color="#2ecc71" if count > 0 else "#e74c3c"
        )

    def _open_output_dir(self, target_dir=None):
        out_dir = target_dir or self.entry_output_dir.get().strip()
        if not out_dir:
            messagebox.showinfo("Aviso", "Por favor, especifique uma pasta de destino.")
            return

        if not os.path.exists(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível criar a pasta: {e}")
                return

        try:
            if platform.system() == "Windows":
                os.startfile(out_dir)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", out_dir])
            else:
                subprocess.Popen(["xdg-open", out_dir])
        except Exception as e:
            messagebox.showerror("Erro ao abrir pasta", str(e))

    def _open_move_dialog(self):
        selected = self.gallery.get_selected_items()
        if not selected:
            messagebox.showinfo("Aviso", "Selecione ao menos um print na galeria para transferir.")
            return

        # Descobre a pasta atual de saída como padrão
        current_out = self.entry_output_dir.get().strip()
        if not current_out or not os.path.isdir(current_out):
            first_file = selected[0].get("filepath")
            if first_file and os.path.exists(first_file):
                current_out = os.path.dirname(first_file)
            else:
                current_out = os.path.join(os.getcwd(), "prints")

        def on_confirm(dest_dir: str, action: str, remove_from_gallery: bool):
            count, errors = self.gallery.move_or_copy_selected(
                dest_dir=dest_dir,
                action=action,
                remove_from_gallery=remove_from_gallery
            )
            verb = "movido(s)" if action == "move" else "copiado(s)"
            if count > 0:
                msg = f"{count} print(s) {verb} com sucesso para:\n\n{dest_dir}\n\nDeseja abrir a pasta agora?"
                if errors:
                    msg += f"\n\nOcorreram {len(errors)} erro(s):\n" + "\n".join(errors[:3])
                if messagebox.askyesno("Transferência Concluída", msg):
                    self._open_output_dir(dest_dir)
            elif errors:
                messagebox.showerror("Erro ao Transferir", "\n".join(errors[:5]))

        MovePrintsDialog(
            parent=self,
            selected_count=len(selected),
            current_output_dir=current_out,
            on_confirm=on_confirm
        )

    def _on_gallery_selection_change(self, count: int, items: list):
        self.comp_random.update_selection_count(count)
        if count > 0:
            self.btn_gal_move.configure(
                state="normal",
                text=f"📁 Mover ({count})"
            )
            self.btn_gal_delete.configure(
                state="normal",
                text=f"🗑 Apagar ({count})"
            )
        else:
            self.btn_gal_move.configure(
                state="disabled",
                text="📁 Mover"
            )
            self.btn_gal_delete.configure(
                state="disabled",
                text="🗑 Apagar"
            )

    def _start_extraction(self):
        if not self.video_info:
            messagebox.showwarning("Atenção", "Por favor, selecione um arquivo de vídeo primeiro.")
            return

        output_dir = self.entry_output_dir.get().strip()
        if not output_dir:
            messagebox.showwarning("Atenção", "Por favor, informe a pasta de destino dos prints.")
            return

        timestamps = self._get_active_timestamps()
        if not timestamps:
            messagebox.showwarning("Atenção", "Nenhum ponto no tempo foi gerado com as configurações atuais.")
            return

        self.is_processing = True
        self.stop_event.clear()
        self.btn_start.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.btn_select_video.configure(state="disabled")
        self.comp_random.set_processing(True)
        self.gallery.clear_gallery()
        self.progress_section.reset()

        img_fmt = self.opt_format.get().lower()
        quality = int(self.slider_quality.get())
        prefix = self.entry_prefix.get().strip() or "print"
        video_path = self.video_info["path"]

        worker = threading.Thread(
            target=self._worker_thread,
            args=(video_path, output_dir, timestamps, img_fmt, quality, prefix, False),
            daemon=True
        )
        worker.start()

    def _start_refinement(self):
        if self.is_processing:
            return
        if not self.video_info:
            messagebox.showwarning("Atenção", "Por favor, selecione um arquivo de vídeo primeiro.")
            return

        output_dir = self.entry_output_dir.get().strip()
        if not output_dir:
            messagebox.showwarning("Atenção", "Por favor, informe a pasta de destino dos prints.")
            return

        selected_items = self.gallery.get_selected_items()
        if not selected_items:
            messagebox.showinfo("Aviso", "Selecione pelo menos um print na galeria para gerar frames ao redor.")
            return

        duration = self.video_info["duration_sec"]
        base_timestamps = [item["timestamp"] for item in selected_items if item.get("timestamp") is not None]
        if not base_timestamps:
            messagebox.showwarning("Atenção", "Os prints selecionados não possuem informações de tempo registradas.")
            return

        timestamps = self.comp_random.get_refinement_timestamps(base_timestamps, duration)
        if not timestamps:
            messagebox.showwarning("Atenção", "Nenhum ponto no tempo pôde ser gerado para o refinamento.")
            return

        self.is_processing = True
        self.stop_event.clear()
        self.btn_start.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.btn_select_video.configure(state="disabled")
        self.comp_random.set_processing(True)
        self.progress_section.reset()

        img_fmt = self.opt_format.get().lower()
        quality = int(self.slider_quality.get())
        prefix = self.entry_prefix.get().strip() or "print"
        video_path = self.video_info["path"]

        worker = threading.Thread(
            target=self._worker_thread,
            args=(video_path, output_dir, timestamps, img_fmt, quality, prefix, True),
            daemon=True
        )
        worker.start()

    def _worker_thread(self, video_path, output_dir, timestamps, img_fmt, quality, prefix, is_refinement=False):
        def on_progress(idx, total, t, filepath):
            self.msg_queue.put(("progress", (idx, total, t, filepath, is_refinement)))

        def on_error(err_msg):
            self.msg_queue.put(("error", err_msg))

        try:
            saved_files = VideoProcessor.extract_frames(
                video_path=video_path,
                output_dir=output_dir,
                timestamps=timestamps,
                image_format=img_fmt,
                jpeg_quality=quality,
                prefix=prefix,
                stop_event=self.stop_event,
                on_progress=on_progress,
                on_error=on_error
            )
            self.msg_queue.put(("finished", (len(saved_files), output_dir)))
        except Exception as e:
            err_details = f"{str(e)}\n{traceback.format_exc()}"
            self.msg_queue.put(("error", err_details))
            self.msg_queue.put(("finished", (0, output_dir)))

    def _cancel_extraction(self):
        if self.is_processing:
            self.stop_event.set()
            self.btn_cancel.configure(state="disabled")

    def _check_queue(self):
        try:
            while not self.msg_queue.empty():
                msg_type, payload = self.msg_queue.get_nowait()
                if msg_type == "progress":
                    if len(payload) == 5:
                        idx, total, t, filepath, is_refinement = payload
                    else:
                        idx, total, t, filepath = payload
                        is_refinement = False

                    time_str = format_timestamp_display(t)
                    self.progress_section.update_progress(idx, total, time_str)
                    tag = "🎯" if is_refinement else "⏱"
                    self.gallery.add_thumbnail(filepath, f"{tag} {time_str}", timestamp=t, is_refinement=is_refinement)
                elif msg_type == "error":
                    self.progress_section.set_error(payload)
                elif msg_type == "finished":
                    count, output_dir = payload
                    self.is_processing = False
                    self.btn_start.configure(state="normal")
                    self.btn_cancel.configure(state="disabled")
                    self.btn_select_video.configure(state="normal")
                    self.comp_random.set_processing(False)

                    if self.stop_event.is_set():
                        self.progress_section.set_cancelled(count)
                    elif count > 0:
                        self.progress_section.set_completed(count, output_dir)

        except Exception as e:
            print(f"Erro no loop de mensagens: {e}")
        finally:
            self.after(80, self._check_queue)
