import customtkinter as ctk

STATUS_COLORS = {
    "Ожидание": "#3498db",
    "В процессе": "#f1c40f",
    "Завершено": "#2ecc71",
    "Отмена": "#e74c3c",
    "Неявка": "#9b59b6"
}

def apply_styles():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")