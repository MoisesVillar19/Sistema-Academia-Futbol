import customtkinter as ctk


class CampeonatoView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="🏆 Campeonatos", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        ctk.CTkLabel(self, text="Módulo en construcción", text_color="gray").pack()
