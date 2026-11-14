"""
Diálogo modal (Lightbox) para inspeção rápida de prints em tamanho ampliado,
com navegação por teclado (← / →), seleção com Espaço e exclusão com Delete.
"""
import os
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image
from typing import List, Dict, Any, Callable

from src.core.utils import open_path_in_os


class LightboxDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        items: List[Dict[str, Any]],
        current_index: int,
        on_toggle_select: Callable[[Dict[str, Any]], bool],
        on_delete_item: Callable[[Dict[str, Any]], bool]
    ):
        """
        POR QUÊ:
        Substitui a necessidade de abrir o aplicativo de fotos do Windows para
        cada print. O usuário pode fazer a curadoria completa (ver detalhes,
        marcar favoritos com Espaço e deletar prints ruins com Delete) em fluxo contínuo.
        """
        super().__init__(parent)
        self.parent = parent
        self.items = items
        self.current_index = max(0, min(current_index, len(items) - 1)) if items else 0
        self.on_toggle_select = on_toggle_select
        self.on_delete_item = on_delete_item
        self.active_ctk_image: ctk.CTkImage = None

        self.title("Visualizador Rápido de Prints")
        self.geometry("900x640")
        self.minsize(680, 500)

        self._build_ui()
        self._bind_shortcuts()
        self._show_current_item()

        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ------------------------------------------
        # 1. Barra Superior (Metadados e Status)
        # ------------------------------------------
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        top_bar.columnconfigure(1, weight=1)

        self.lbl_counter = ctk.CTkLabel(
            top_bar,
            text="",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_counter.grid(row=0, column=0, sticky="w")

        self.lbl_filename = ctk.CTkLabel(
            top_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.lbl_filename.grid(row=0, column=1, padx=12, sticky="w")

        self.lbl_badge_selected = ctk.CTkLabel(
            top_bar,
            text="✓ SELECIONADO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38bdf8",
            fg_color=("#1e3a5f", "#0f2744"),
            corner_radius=4,
            padx=8,
            pady=2
        )

        # ------------------------------------------
        # 2. Área Central (Exibição da Imagem)
        # ------------------------------------------
        self.image_container = ctk.CTkFrame(self, fg_color=("#1e1e1e", "#121212"), corner_radius=8)
        self.image_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=4)
        self.image_container.columnconfigure(0, weight=1)
        self.image_container.rowconfigure(0, weight=1)

        self.lbl_image = ctk.CTkLabel(self.image_container, text="")
        self.lbl_image.grid(row=0, column=0, sticky="nsew")

        # ------------------------------------------
        # 3. Barra Inferior de Ações e Atalhos
        # ------------------------------------------
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 14))
        bottom_bar.columnconfigure(2, weight=1)

        self.btn_prev = ctk.CTkButton(
            bottom_bar,
            text="◀ Anterior (←)",
            width=110,
            command=self._prev_item
        )
        self.btn_prev.pack(side="left", padx=(0, 6))

        self.btn_next = ctk.CTkButton(
            bottom_bar,
            text="Próximo (→) ▶",
            width=110,
            command=self._next_item
        )
        self.btn_next.pack(side="left", padx=(0, 14))

        self.btn_toggle_select = ctk.CTkButton(
            bottom_bar,
            text="Marcar/Desmarcar (Espaço)",
            fg_color=("#2563eb", "#1d4ed8"),
            hover_color=("#3b82f6", "#2563eb"),
            command=self._toggle_current_selection
        )
        self.btn_toggle_select.pack(side="left", padx=(0, 6))

        self.btn_open_external = ctk.CTkButton(
            bottom_bar,
            text="↗ Abrir no Sistema (Enter)",
            fg_color=("#3a3a3a", "#4a4a4a"),
            hover_color=("#555555", "#666666"),
            command=self._open_in_system
        )
        self.btn_open_external.pack(side="left", padx=(0, 6))

        self.btn_delete = ctk.CTkButton(
            bottom_bar,
            text="🗑 Apagar (Del)",
            fg_color=("#c0392b", "#962d22"),
            hover_color=("#e74c3c", "#c0392b"),
            command=self._delete_current_item
        )
        self.btn_delete.pack(side="right")

    def _bind_shortcuts(self):
        """Atalhos de teclado ágeis para curadoria sem mouse."""
        self.bind("<Left>", lambda e: self._prev_item())
        self.bind("<Right>", lambda e: self._next_item())
        self.bind("<space>", lambda e: self._toggle_current_selection())
        self.bind("<Delete>", lambda e: self._delete_current_item())
        self.bind("<Return>", lambda e: self._open_in_system())
        self.bind("<Escape>", lambda e: self.destroy())

    def _get_current_item(self) -> Dict[str, Any]:
        if 0 <= self.current_index < len(self.items):
            return self.items[self.current_index]
        return None

    def _show_current_item(self):
        item = self._get_current_item()
        if not item:
            self.destroy()
            return

        filepath = item.get("filepath", "")
        total = len(self.items)
        self.lbl_counter.configure(text=f"Print {self.current_index + 1} de {total}")
        self.lbl_filename.configure(text=f"({item.get('label', '')}) {os.path.basename(filepath)}")

        is_selected = item.get("var") and item["var"].get()
        if is_selected:
            self.lbl_badge_selected.grid(row=0, column=2, sticky="e")
            self.btn_toggle_select.configure(text="Desmarcar (Espaço)")
        else:
            self.lbl_badge_selected.grid_forget()
            self.btn_toggle_select.configure(text="Marcar (Espaço)")

        self.btn_prev.configure(state="normal" if self.current_index > 0 else "disabled")
        self.btn_next.configure(state="normal" if self.current_index < total - 1 else "disabled")

        self._render_image(filepath)

    def _render_image(self, filepath: str):
        """
        Carrega a imagem para visualização ampla mantendo a proporção de aspecto.
        POR QUÊ: Copiamos em RAM (`raw.copy()`) para não reter file locks.
        """
        if not filepath or not os.path.exists(filepath):
            self.lbl_image.configure(image="", text="Imagem não encontrada no disco.")
            return

        try:
            with Image.open(filepath) as raw_img:
                pil_img = raw_img.copy()

            # Resolução máxima para visualização rápida no Lightbox
            max_w, max_h = 820, 500
            pil_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

            self.active_ctk_image = ctk.CTkImage(
                light_image=pil_img,
                dark_image=pil_img,
                size=pil_img.size
            )
            self.lbl_image.configure(image=self.active_ctk_image, text="")
        except Exception as e:
            self.lbl_image.configure(image="", text=f"Erro ao renderizar imagem:\n{e}")

    def _prev_item(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._show_current_item()

    def _next_item(self):
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            self._show_current_item()

    def _toggle_current_selection(self):
        item = self._get_current_item()
        if item and self.on_toggle_select:
            self.on_toggle_select(item)
            self._show_current_item()

    def _open_in_system(self):
        item = self._get_current_item()
        if item and item.get("filepath"):
            open_path_in_os(item["filepath"])

    def _delete_current_item(self):
        item = self._get_current_item()
        if not item or not self.on_delete_item:
            return

        # Executa a exclusão com confirmação
        success = self.on_delete_item(item)
        if success:
            if not self.items:
                self.destroy()
                return
            if self.current_index >= len(self.items):
                self.current_index = len(self.items) - 1
            self._show_current_item()
