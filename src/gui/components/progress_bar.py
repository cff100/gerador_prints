"""
Componente de barra de progresso e status de execução.
"""
import customtkinter as ctk

class ProgressSection(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._create_widgets()

    def _create_widgets(self):
        self.columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self,
            text="Pronto para iniciar.",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))

        self.progressbar = ctk.CTkProgressBar(self)
        self.progressbar.set(0.0)
        self.progressbar.grid(row=1, column=0, sticky="ew", padx=10, pady=4)

        self.details_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        self.details_label.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

    def update_progress(self, current: int, total: int, current_time_str: str = ""):
        if total > 0:
            fraction = min(1.0, current / total)
            percent = int(fraction * 100)
            self.progressbar.set(fraction)
            self.status_label.configure(
                text=f"Processando: {current} de {total} prints ({percent}%)",
                text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"]
            )
            if current_time_str:
                self.details_label.configure(
                    text=f"Frame capturado no tempo: {current_time_str}"
                )
        else:
            self.progressbar.set(0.0)

    def set_completed(self, total: int, output_dir: str):
        self.progressbar.set(1.0)
        self.status_label.configure(
            text=f"✅ Concluído! {total} prints salvos com sucesso.",
            text_color=("#107c41", "#2ecc71")
        )
        self.details_label.configure(text=f"Pasta de destino: {output_dir}")

    def set_cancelled(self, saved_count: int):
        self.status_label.configure(
            text=f"⏹ Cancelado pelo usuário. {saved_count} prints gerados.",
            text_color=("#d83b01", "#e74c3c")
        )

    def set_error(self, message: str):
        self.status_label.configure(
            text=f"❌ Erro: {message}",
            text_color=("#d83b01", "#e74c3c")
        )

    def reset(self):
        self.progressbar.set(0.0)
        self.status_label.configure(
            text="Pronto para iniciar.",
            text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        )
        self.details_label.configure(text="")
