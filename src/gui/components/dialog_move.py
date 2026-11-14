"""
Diálogo modal para transferir prints selecionados para outra pasta (subpasta interna ou personalizada).
"""
import os
from tkinter import filedialog, messagebox
import customtkinter as ctk
from typing import Callable, Optional

class MovePrintsDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        selected_count: int,
        current_output_dir: str,
        on_confirm: Callable[[str, str, bool], None]
    ):
        super().__init__(parent)
        self.parent = parent
        self.selected_count = selected_count
        self.current_output_dir = os.path.abspath(current_output_dir) if current_output_dir else os.getcwd()
        self.on_confirm = on_confirm

        self.title("Transferir Prints Selecionados")
        self.geometry("520x460")
        self.resizable(False, False)

        # Estado das opções
        self.dest_mode_var = ctk.StringVar(value="subfolder")  # "subfolder" ou "custom"
        self.subfolder_name_var = ctk.StringVar(value="selecionados")
        self.custom_path_var = ctk.StringVar(value="")
        self.action_var = ctk.StringVar(value="move")  # "move" ou "copy"
        self.remove_gal_var = ctk.BooleanVar(value=True)

        self._build_ui()
        self._center_window()

        self.transient(parent)
        self.grab_set()
        self.focus_set()

        # Atalhos
        self.bind("<Return>", lambda e: self._handle_confirm())
        self.bind("<Escape>", lambda e: self.destroy())

    def _center_window(self):
        self.update_idletasks()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_rootx()
        py = self.parent.winfo_rooty()

        w = 520
        h = 460
        x = max(0, px + (pw - w) // 2)
        y = max(0, py + (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        # Cabeçalho
        lbl_title = ctk.CTkLabel(
            container,
            text=f"📁 Transferir {self.selected_count} Print(s) Selecionado(s)",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        lbl_title.pack(anchor="w", pady=(0, 4))

        lbl_sub = ctk.CTkLabel(
            container,
            text="Escolha a pasta de destino e a ação desejada:",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        lbl_sub.pack(anchor="w", pady=(0, 12))

        # Seção Destino
        dest_card = ctk.CTkFrame(container, corner_radius=8)
        dest_card.pack(fill="x", pady=(0, 12), padx=0)

        lbl_dest_head = ctk.CTkLabel(
            dest_card,
            text="Pasta de Destino",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        lbl_dest_head.pack(anchor="w", padx=12, pady=(10, 6))

        # Opção 1: Subpasta interna
        rb_subfolder = ctk.CTkRadioButton(
            dest_card,
            text="Criar subpasta interna na pasta atual:",
            variable=self.dest_mode_var,
            value="subfolder",
            command=self._on_dest_mode_change,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        rb_subfolder.pack(anchor="w", padx=12, pady=(2, 4))

        sub_frame = ctk.CTkFrame(dest_card, fg_color="transparent")
        sub_frame.pack(fill="x", padx=32, pady=(0, 6))

        self.entry_subfolder = ctk.CTkEntry(
            sub_frame,
            textvariable=self.subfolder_name_var,
            placeholder_text="Nome da subpasta (ex: selecionados, favoritos)",
            height=28
        )
        self.entry_subfolder.pack(fill="x")
        self.subfolder_name_var.trace_add("write", lambda *args: self._update_preview())

        self.lbl_preview = ctk.CTkLabel(
            dest_card,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="#38bdf8",
            wraplength=450,
            justify="left"
        )
        self.lbl_preview.pack(anchor="w", padx=32, pady=(0, 8))

        # Opção 2: Outra pasta no computador
        rb_custom = ctk.CTkRadioButton(
            dest_card,
            text="Escolher outra pasta no computador:",
            variable=self.dest_mode_var,
            value="custom",
            command=self._on_dest_mode_change,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        rb_custom.pack(anchor="w", padx=12, pady=(4, 4))

        custom_frame = ctk.CTkFrame(dest_card, fg_color="transparent")
        custom_frame.pack(fill="x", padx=32, pady=(0, 12))
        custom_frame.columnconfigure(0, weight=1)

        self.entry_custom = ctk.CTkEntry(
            custom_frame,
            textvariable=self.custom_path_var,
            placeholder_text="Nenhuma pasta selecionada...",
            height=28
        )
        self.entry_custom.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_browse = ctk.CTkButton(
            custom_frame,
            text="📁 Procurar...",
            width=90,
            height=28,
            command=self._browse_custom_dir
        )
        self.btn_browse.grid(row=0, column=1)

        # Seção Ação (Mover vs Copiar)
        action_card = ctk.CTkFrame(container, corner_radius=8)
        action_card.pack(fill="x", pady=(0, 14), padx=0)

        lbl_action_head = ctk.CTkLabel(
            action_card,
            text="Operação",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        lbl_action_head.pack(anchor="w", padx=12, pady=(10, 6))

        opts_frame = ctk.CTkFrame(action_card, fg_color="transparent")
        opts_frame.pack(fill="x", padx=12, pady=(0, 6))

        rb_move = ctk.CTkRadioButton(
            opts_frame,
            text="Mover (transfere do local original)",
            variable=self.action_var,
            value="move",
            command=self._on_action_change,
            font=ctk.CTkFont(size=11)
        )
        rb_move.pack(side="left", padx=(0, 16))

        rb_copy = ctk.CTkRadioButton(
            opts_frame,
            text="Copiar (mantém cópia original)",
            variable=self.action_var,
            value="copy",
            command=self._on_action_change,
            font=ctk.CTkFont(size=11)
        )
        rb_copy.pack(side="left")

        self.chk_remove_gal = ctk.CTkCheckBox(
            action_card,
            text="Remover da galeria visual após mover",
            variable=self.remove_gal_var,
            font=ctk.CTkFont(size=11)
        )
        self.chk_remove_gal.pack(anchor="w", padx=12, pady=(2, 10))

        # Botões inferiores
        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", side="bottom")

        btn_cancel = ctk.CTkButton(
            btn_box,
            text="Cancelar",
            width=100,
            height=32,
            fg_color=("#4a4a4a", "#3a3a3a"),
            hover_color=("#5a5a5a", "#4a4a4a"),
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        self.btn_confirm = ctk.CTkButton(
            btn_box,
            text="Confirmar",
            width=140,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#2563eb", "#1d4ed8"),
            hover_color=("#3b82f6", "#2563eb"),
            command=self._handle_confirm
        )
        self.btn_confirm.pack(side="right")

        self._on_dest_mode_change()
        self._update_preview()

    def _on_dest_mode_change(self):
        is_sub = self.dest_mode_var.get() == "subfolder"
        self.entry_subfolder.configure(state="normal" if is_sub else "disabled")
        self.entry_custom.configure(state="normal" if not is_sub else "disabled")
        self.btn_browse.configure(state="normal" if not is_sub else "disabled")
        self._update_preview()

    def _on_action_change(self):
        is_move = self.action_var.get() == "move"
        if is_move:
            self.chk_remove_gal.configure(state="normal")
            self.remove_gal_var.set(True)
        else:
            self.chk_remove_gal.configure(state="disabled")
            self.remove_gal_var.set(False)

    def _update_preview(self):
        if self.dest_mode_var.get() == "subfolder":
            sub = self.subfolder_name_var.get().strip() or "selecionados"
            cleaned = "".join(c for c in sub if c not in '<>:"/\\|?*').strip()
            path = os.path.join(self.current_output_dir, cleaned)
            self.lbl_preview.configure(text=f"📁 Destino: {path}")
        else:
            custom = self.custom_path_var.get().strip()
            if custom:
                self.lbl_preview.configure(text=f"📁 Destino: {custom}")
            else:
                self.lbl_preview.configure(text="📁 Destino: Selecione uma pasta através do botão Procurar...")

    def _browse_custom_dir(self):
        chosen = filedialog.askdirectory(
            parent=self,
            title="Selecione a Pasta de Destino",
            initialdir=self.current_output_dir
        )
        if chosen:
            self.custom_path_var.set(chosen)
            self.dest_mode_var.set("custom")
            self._on_dest_mode_change()

    def _handle_confirm(self):
        mode = self.dest_mode_var.get()
        if mode == "subfolder":
            sub = self.subfolder_name_var.get().strip()
            cleaned = "".join(c for c in sub if c not in '<>:"/\\|?*').strip()
            if not cleaned:
                messagebox.showerror("Nome Inválido", "Por favor, digite um nome válido para a subpasta.", parent=self)
                return
            dest_dir = os.path.join(self.current_output_dir, cleaned)
        else:
            dest_dir = self.custom_path_var.get().strip()
            if not dest_dir:
                messagebox.showerror("Pasta Não Selecionada", "Por favor, selecione uma pasta de destino.", parent=self)
                return

        action = self.action_var.get()
        remove_gal = self.remove_gal_var.get() if action == "move" else False

        self.destroy()
        self.on_confirm(dest_dir, action, remove_gal)

