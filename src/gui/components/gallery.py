"""
Galeria com miniaturas de prints gerados, seleção com checkboxes e clique para abrir.
"""
import os
import shutil
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image
from typing import List, Dict, Any, Optional, Callable

from src.core.utils import resolve_unique_filepath, open_path_in_os
from src.gui.components.dialog_lightbox import LightboxDialog


class GalleryFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, on_selection_change: Optional[Callable[[int, List[Dict[str, Any]]], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.items: List[Dict[str, Any]] = []
        # POR QUÊ manter `self.image_references`:
        # O Garbage Collector do Python apaga variáveis locais assim que um método
        # termina. Como o motor gráfico C (Tcl/Tk) não incrementa o contador de
        # referências do Python, sem esta lista as miniaturas sumiriam da tela!
        self.image_references: List[ctk.CTkImage] = []
        self.on_selection_change = on_selection_change
        self.max_cols = 4

        for i in range(self.max_cols):
            self.columnconfigure(i, weight=1, uniform="col")

    def clear_gallery(self):
        """Limpa todos os cards e libera as referências de imagem da memória."""
        for widget in self.winfo_children():
            widget.destroy()
        self.items.clear()
        self.image_references.clear()
        self._notify_selection_change()

    def _load_ctk_thumbnail(self, filepath: str) -> ctk.CTkImage:
        """
        Carrega a imagem do disco, reduz para miniatura na RAM e empacota em CTkImage.

        POR QUÊ fazemos `raw_img.copy()` dentro do bloco `with`:
        O `Image.open()` do Pillow tem carregamento preguiçoso (lazy) e mantém um
        lock aberto no arquivo físico no Windows. Copiar os pixels para a RAM e
        fechar o `with` imediatamente destrava o arquivo no sistema operacional,
        permitindo que os botões 'Mover' e 'Apagar' funcionem sem dar [WinError 32].
        """
        with Image.open(filepath) as raw_img:
            pil_img = raw_img.copy()
        pil_img.thumbnail((140, 90), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
        self.image_references.append(ctk_img)
        return ctk_img

    def _remove_card_from_gallery(self, item: Dict[str, Any]) -> None:
        """Destrói o widget visual do card e remove seus metadados e referências de imagem."""
        if "card" in item and item["card"].winfo_exists():
            item["card"].destroy()
        if "ctk_img" in item and item["ctk_img"] in self.image_references:
            self.image_references.remove(item["ctk_img"])
        if item in self.items:
            self.items.remove(item)

    def _grid_single_item(self, idx: int, item: Dict[str, Any]):
        """Posiciona um item específico no grid em O(1)."""
        row = idx // self.max_cols
        col = idx % self.max_cols
        item["card"].grid(row=row, column=col, padx=5, pady=5, sticky="n")

    def add_thumbnail(
        self,
        filepath: str,
        label_text: str = "",
        timestamp: Optional[float] = None,
        is_refinement: bool = False,
        pil_thumbnail: Optional[Image.Image] = None,
        reorder: bool = False
    ):
        """
        Cria e insere um novo card de miniatura na galeria.

        POR QUÊ `pil_thumbnail` e `reorder=False`:
        1. Se a Worker Thread já gerou a miniatura na RAM, criamos o CTkImage direto,
           sem releitura de disco ou processamento pesado na Main Thread da UI.
        2. Nas extrações normais, os frames já chegam em ordem cronológica estrita;
           inserir o card em O(1) na posição final evita refazer o layout de toda a grade
           a cada frame capturado (eliminando complexidade O(N^2)).
        """
        if not os.path.exists(filepath):
            return

        try:
            if pil_thumbnail:
                ctk_img = ctk.CTkImage(
                    light_image=pil_thumbnail,
                    dark_image=pil_thumbnail,
                    size=pil_thumbnail.size
                )
                self.image_references.append(ctk_img)
            else:
                ctk_img = self._load_ctk_thumbnail(filepath)

            card = ctk.CTkFrame(self, corner_radius=6, border_width=0, border_color="#1f6aa5")

            top_bar = ctk.CTkFrame(card, fg_color="transparent")
            top_bar.pack(fill="x", padx=4, pady=(4, 1))

            check_var = ctk.BooleanVar(value=False)
            item_data: Dict[str, Any] = {
                "card": card,
                "filepath": filepath,
                "label": label_text,
                "timestamp": timestamp,
                "var": check_var,
                "is_refinement": is_refinement,
                "ctk_img": ctk_img
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

            btn = ctk.CTkButton(
                card,
                image=ctk_img,
                text="",
                fg_color="transparent",
                hover_color=("#c0c0c0", "#3a3a3a"),
                width=140,
                height=90,
                command=lambda it=item_data: self._open_lightbox(it)
            )
            btn.pack(padx=4, pady=(2, 4))

            idx = len(self.items)
            self.items.append(item_data)

            if reorder:
                self.reorder_grid()
            else:
                self._grid_single_item(idx, item_data)

        except Exception as e:
            print(f"Erro ao carregar miniatura: {e}")

    def reorder_grid(self):
        """
        Reorganiza todos os cards na grade em ordem cronológica de aparição no vídeo.
        POR QUÊ: É chamado uma única vez ao término do Refinamento (Modo 3) ou
        quando itens forem apagados/movidos.
        """
        self.items.sort(key=lambda x: (
            x["timestamp"] if x["timestamp"] is not None else float("inf"),
            x["filepath"]
        ))
        for idx, item in enumerate(self.items):
            self._grid_single_item(idx, item)

    def _open_lightbox(self, item_data: Dict[str, Any]):
        """Abre o visualizador Lightbox com foco no item selecionado."""
        try:
            curr_idx = self.items.index(item_data)
        except ValueError:
            curr_idx = 0

        LightboxDialog(
            parent=self.winfo_toplevel(),
            items=self.items,
            current_index=curr_idx,
            on_toggle_select=self.toggle_item_selection,
            on_delete_item=self.delete_item
        )

    def toggle_item_selection(self, item_data: Dict[str, Any]) -> bool:
        """Alterna a seleção de um card e atualiza o estado visual."""
        if "var" in item_data:
            current = item_data["var"].get()
            item_data["var"].set(not current)
            item_data["card"].configure(border_width=0 if current else 2)
            self._notify_selection_change()
            return not current
        return False

    def get_all_timestamps(self) -> List[float]:
        """Retorna todos os timestamps atualmente carregados na galeria."""
        return [item["timestamp"] for item in self.items if item.get("timestamp") is not None]

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

        self._remove_card_from_gallery(item_data)
        self.reorder_grid()
        self._notify_selection_change()
        return True

    def delete_selected(self) -> int:
        """Apaga em lote todos os prints selecionados do disco e atualiza a galeria."""
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
                self._remove_card_from_gallery(item)
                deleted_count += 1
            except Exception as e:
                errors.append(f"{os.path.basename(filepath) if filepath else 'Arquivo'}: {e}")

        self.reorder_grid()
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
        Move ou copia os prints selecionados para `dest_dir` sem sobrescrever arquivos.
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
            same_folder = os.path.abspath(os.path.dirname(src)) == os.path.abspath(dest_dir)
            dest_file = src if same_folder else resolve_unique_filepath(dest_dir, filename)

            try:
                if action == "move":
                    if not same_folder:
                        shutil.move(src, dest_file)

                    if remove_from_gallery:
                        self._remove_card_from_gallery(item)
                    else:
                        item["filepath"] = dest_file
                        item["var"].set(False)
                        item["card"].configure(border_width=0)
                else:
                    if not same_folder:
                        shutil.copy2(src, dest_file)
                    item["var"].set(False)
                    item["card"].configure(border_width=0)

                success_count += 1
            except Exception as e:
                errors.append(f"{filename}: {e}")

        if remove_from_gallery and action == "move":
            self.reorder_grid()

        self._notify_selection_change()
        return success_count, errors

    def get_selected_items(self) -> List[Dict[str, Any]]:
        """Retorna os itens atualmente marcados com seus metadados."""
        return [item for item in self.items if item["var"].get()]

    def select_all(self):
        """Marca todos os itens da galeria."""
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
