"""
Componente reutilizável de entrada numérica com botões de incremento e decremento (+ / -).
"""
import customtkinter as ctk
from typing import Callable, Optional, Union

class StepperEntry(ctk.CTkFrame):
    def __init__(
        self,
        master,
        initial_value: Union[int, float] = 0,
        step: Union[int, float] = 1,
        min_value: Union[int, float] = 0,
        max_value: Union[int, float] = 99999,
        is_float: bool = False,
        entry_width: int = 70,
        on_change: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.step = step
        self.min_value = min_value
        self.max_value = max_value
        self.is_float = is_float
        self.on_change = on_change

        self._create_widgets(initial_value, entry_width)

    def _create_widgets(self, initial_value: Union[int, float], entry_width: int):
        # Botão Decrementar (-)
        self.btn_minus = ctk.CTkButton(
            self,
            text="-",
            width=28,
            height=28,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#3a3a3a", "#4a4a4a"),
            hover_color=("#555555", "#666666"),
            command=self.decrement
        )
        self.btn_minus.pack(side="left", padx=(0, 2))

        # Campo de Texto Digitável
        self.entry = ctk.CTkEntry(
            self,
            width=entry_width,
            height=28,
            justify="center"
        )
        self.entry.pack(side="left")
        self.entry.bind("<KeyRelease>", lambda e: self._on_key_release())

        # Botão Incrementar (+)
        self.btn_plus = ctk.CTkButton(
            self,
            text="+",
            width=28,
            height=28,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#3a3a3a", "#4a4a4a"),
            hover_color=("#555555", "#666666"),
            command=self.increment
        )
        self.btn_plus.pack(side="left", padx=(2, 0))

        self.set_value(initial_value)

    def get_value(self) -> Union[int, float]:
        raw = self.entry.get().strip().replace(",", ".")
        if not raw:
            return self.min_value
        try:
            val = float(raw) if self.is_float else int(float(raw))
            val = max(self.min_value, min(self.max_value, val))
            return val
        except ValueError:
            return self.min_value

    def set_value(self, val: Union[int, float]):
        val = max(self.min_value, min(self.max_value, val))
        self.entry.delete(0, "end")
        if self.is_float:
            # Formata sem casas decimais desnecessárias (ex: 5.0 -> 5 ou 0.5 -> 0.5)
            formatted = f"{val:.2f}".rstrip("0").rstrip(".") if "." in f"{val:.2f}" else str(val)
            self.entry.insert(0, formatted)
        else:
            self.entry.insert(0, str(int(val)))

    def increment(self):
        curr = self.get_value()
        new_val = curr + self.step
        self.set_value(new_val)
        self._notify_change()

    def decrement(self):
        curr = self.get_value()
        new_val = curr - self.step
        self.set_value(new_val)
        self._notify_change()

    def _on_key_release(self):
        self._notify_change()

    def _notify_change(self):
        if self.on_change:
            self.on_change()
