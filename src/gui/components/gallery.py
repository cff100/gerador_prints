"""
Galeria com miniaturas de prints gerados, seleção com checkboxes e clique para abrir.
"""
import os
import shutil
import subprocess
import platform
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image
from typing import List, Dict, Any, Optional, Callable

class GalleryFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, on_selection_change: Optional[Callable[[int, List[Dict[str, Any]]], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.items: List[Dict[str, Any]] = []
        self.image_references: List[ctk.CTkImage] = []
        self.on_selection_change = on_selection_change
        self.max_cols = 4

        for i in range(self.max_cols):
            self.columnconfigure(i, weight=1, uniform="col")

    def clear_gallery(self):
        """Limpa todos os elementos da galeria."""
        for widget in self.winfo_children():
            widget.destroy()
        self.items.clear()
        self.image_references.clear()
        self._notify_selection_change()

    def add_thumbnail(
        self,
        filepath: str,
        label_text: str = "",
        timestamp: Optional[float] = None,
        is_refinement: bool = False
    ):
        """Adiciona uma nova miniatura à galeria com controle de seleção."""
        if not os.path.exists(filepath):
            return

        try:
            with Image.open(filepath) as raw_img:
                pil_img = raw_img.copy()
            pil_img.thumbnail((140, 90), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
            self.image_references.append(ctk_img)

            card = ctk.CTkFrame(self, corner_radius=6, border_width=0, border_color="#1f6aa5")

            # Barra superior do card: Checkbox, título e botão fechar/apagar
            top_bar = ctk.CTkFrame(card, fg_color="transparent")
            top_bar.pack(fill="x", padx=4, pady=(4, 1))

            check_var = ctk.BooleanVar(value=False)

            item_data: Dict[str, Any] = {
                "card": card,
                "filepath": filepath,
                "label": label_text,
                "timestamp": timestamp,
                "var": check_var,
                "is_refinement": is_refinement
            }

            def on_toggle():
                is_sel = check_var.get()
                card.configure(border_width=2 if is_sel else 0)
                self._notify_selection_change()

            chk = ctk.CTkCheckBox(
                top_bar,
                text="",
                variable=check_var,
                width=18,
                height=18,
                checkbox_width=18,
                checkbox_height=18,
                corner_radius=4,
                command=on_toggle
            )
            chk.pack(side="left")

            btn_del = ctk.CTkButton(
                top_bar,
                text="✕",
                width=20,
                height=20,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="transparent",
                hover_color=("#ff4d4f", "#e74c3c"),
                text_color=("gray60", "gray40"),
                command=lambda it=item_data: self.delete_item(it)
            )
            btn_del.pack(side="right", padx=(2, 0))

            display_name = label_text if label_text else os.path.basename(filepath)
            lbl_top = ctk.CTkLabel(
                top_bar,
                text=display_name,
                font=ctk.CTkFont(size=10, weight="bold" if is_refinement else "normal"),
                text_color="#38bdf8" if is_refinement else None,
                anchor="w"
            )
            lbl_top.pack(side="left", padx=(4, 2), fill="x", expand=True)

            # Botão com a imagem para visualização em tamanho real
            btn = ctk.CTkButton(
                card,
                image=ctk_img,
                text="",
                fg_color="transparent",
                hover_color=("#c0c0c0", "#3a3a3a"),
                width=140,
                height=90,
                command=lambda it=item_data: self._open_image(it["filepath"])
            )
            btn.pack(padx=4, pady=(2, 4))

            self.items.append(item_data)
            self._reorder_grid()

        except Exception as e:
            print(f"Erro ao carregar miniatura: {e}")

    def _reorder_grid(self):
        """Reorganiza todos os cards na grade em ordem cronológica de aparição no vídeo."""
        self.items.sort(key=lambda x: (
            x["timestamp"] if x["timestamp"] is not None else float("inf"),
            x["filepath"]
        ))
        for idx, item in enumerate(self.items):
            row = idx // self.max_cols
            col = idx % self.max_cols
            item["card"].grid(row=row, column=col, padx=5, pady=5, sticky="n")

    def delete_item(self, item_data: Dict[str, Any], confirm: bool = True) -> bool:
        """Apaga um print específico do disco e remove seu card da galeria."""
        filepath = item_data.get("filepath")
        filename = os.path.basename(filepath) if filepath else "este print"
        if confirm:
            if not messagebox.askyesno("Apagar Print", f"Deseja realmente apagar este print do disco?\n\n{filename}"):
                return False

        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            messagebox.showerror("Erro ao Apagar", f"Não foi possível apagar o arquivo do disco:\n{e}")
            return False

        if "card" in item_data and item_data["card"].winfo_exists():
            item_data["card"].destroy()

        if item_data in self.items:
            self.items.remove(item_data)

        self._reorder_grid()
        self._notify_selection_change()
        return True

    def delete_selected(self) -> int:
        """Apaga todos os prints selecionados do disco e remove da galeria."""
        selected = self.get_selected_items()
        if not selected:
            messagebox.showinfo("Aviso", "Nenhum print selecionado para apagar.")
            return 0

        count = len(selected)
        msg = "Deseja realmente apagar o print selecionado do disco?" if count == 1 else f"Deseja realmente apagar os {count} prints selecionados do disco?"
        if not messagebox.askyesno("Confirmar Exclusão", msg):
            return 0

        deleted_count = 0
        errors = []
        for item in selected:
            filepath = item.get("filepath")
            try:
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)
                if "card" in item and item["card"].winfo_exists():
                    item["card"].destroy()
                if item in self.items:
                    self.items.remove(item)
                deleted_count += 1
            except Exception as e:
                errors.append(f"{os.path.basename(filepath) if filepath else 'Arquivo'}: {e}")

        self._reorder_grid()
        self._notify_selection_change()

        if errors:
            messagebox.showwarning("Aviso de Exclusão", f"{deleted_count} print(s) apagado(s).\nErros ao apagar:\n" + "\n".join(errors[:5]))

        return deleted_count

    def move_or_copy_selected(
        self,
        dest_dir: str,
        action: str = "move",
        remove_from_gallery: bool = True
    ) -> tuple[int, List[str]]:
        """
        Move ou copia os prints selecionados para o diretório de destino.
        Se remove_from_gallery for True e action == "move", remove da galeria.
        Caso contrário, atualiza o caminho do arquivo para o novo destino.
        """
        selected = self.get_selected_items()
        if not selected:
            return 0, ["Nenhum print selecionado."]

        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            return 0, [f"Erro ao criar pasta de destino '{dest_dir}': {e}"]

        success_count = 0
        errors = []

        for item in selected:
            src = item.get("filepath")
            if not src or not os.path.exists(src):
                errors.append(f"Arquivo não encontrado: {src}")
                continue

            filename = os.path.basename(src)
            dest_file = os.path.join(dest_dir, filename)

            # Evita sobreescrita caso já exista arquivo com mesmo nome no destino
            if os.path.exists(dest_file) and os.path.abspath(src) != os.path.abspath(dest_file):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_file):
                    dest_file = os.path.join(dest_dir, f"{base}_{counter}{ext}")
                    counter += 1

            try:
                if action == "move":
                    if os.path.abspath(src) != os.path.abspath(dest_file):
                        shutil.move(src, dest_file)

                    if remove_from_gallery:
                        if "card" in item and item["card"].winfo_exists():
                            item["card"].destroy()
                        if item in self.items:
                            self.items.remove(item)
                    else:
                        item["filepath"] = dest_file
                        item["var"].set(False)
                        item["card"].configure(border_width=0)
                else:  # copy
                    if os.path.abspath(src) != os.path.abspath(dest_file):
                        shutil.copy2(src, dest_file)
                    item["var"].set(False)
                    item["card"].configure(border_width=0)

                success_count += 1
            except Exception as e:
                errors.append(f"{filename}: {e}")

        if remove_from_gallery and action == "move":
            self._reorder_grid()

        self._notify_selection_change()
        return success_count, errors

    def get_selected_items(self) -> List[Dict[str, Any]]:
        """Retorna os itens atualmente selecionados com seus metadados."""
        return [item for item in self.items if item["var"].get()]

    def select_all(self):
        """Seleciona todos os itens da galeria."""
        for item in self.items:
            item["var"].set(True)
            item["card"].configure(border_width=2)
        self._notify_selection_change()

    def clear_selection(self):
        """Desmarca todos os itens da galeria."""
        for item in self.items:
            item["var"].set(False)
            item["card"].configure(border_width=0)
        self._notify_selection_change()

    def _notify_selection_change(self):
        if self.on_selection_change:
            selected = self.get_selected_items()
            self.on_selection_change(len(selected), selected)

    def _open_image(self, filepath: str):
        if not os.path.exists(filepath):
            return
        try:
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", filepath])
            else:
                subprocess.Popen(["xdg-open", filepath])
        except Exception as e:
            print(f"Erro ao abrir arquivo: {e}")
