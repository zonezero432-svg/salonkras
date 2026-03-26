import customtkinter as ctk

# Цвета для выпадающего списка статусов в журнале
STATUS_COLORS = {
    "Ожидание": "#3498db",  # Синий
    "В процессе": "#f1c40f", # Желтый
    "Выполнена": "#2ecc71",  # Зеленый
    "Отмена": "#e74c3c",    # Красный
    "Неявка": "#9b59b6"     # Фиолетовый
}

def apply_styles():
    """Базовые настройки темы CustomTkinter"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")