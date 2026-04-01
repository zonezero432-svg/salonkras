import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
import os

class COLORS:
    """Цветовая схема приложения для визуального разделения категорий."""
    HAIR = "#3498db"
    COLOR = "#9b59b6"
    FACE = "#e67e22"
    NAILS = "#e74c3c"
    PREMIUM = "#f1c40f"
    SPA = "#1abc9c"
    WAITING = "#7f8c8d"
    PROCESS = "#34495e"
    DONE = "#2ecc71"
    CANCEL = "#c0392b"

    @staticmethod
    def get(key, default="#3498db"):
        mapping = {
            "Стрижки": COLORS.HAIR,
            "Окрашивание": COLORS.COLOR,
            "Уход": COLORS.FACE,
            "Маникюр": COLORS.NAILS,
            "Премиум": COLORS.PREMIUM,
            "SPA": COLORS.SPA,
            "Ожидание": COLORS.WAITING,
            "В процессе": COLORS.PROCESS,
            "Завершено": COLORS.DONE,
            "Отмена": COLORS.CANCEL
        }
        return mapping.get(key, default)

class BaseModal(ctk.CTkToplevel):
    """Базовый класс для всех модальных окон системы."""
    def __init__(self, parent, title="Окно", size="550x750"):
        super().__init__(parent)
        self.title(title)
        self.geometry(size)
        self.configure(fg_color="#121212")
        
        # Поверх всех окон
        self.transient(parent)
        self.grab_set()
        
        # Центрирование
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

class LoginModal(BaseModal):
    """Окно авторизации."""
    def __init__(self, parent, db, on_success):
        super().__init__(parent, "Авторизация", "450x550")
        self.db = db
        self.on_success = on_success
        self.protocol("WM_DELETE_WINDOW", parent.destroy)

        self.label = ctk.CTkLabel(
            self, 
            text="⋆༺𓆩♕𓆪༻⋆\nКРАСНАЯ КОРОЛЕВА", 
            font=("Arial", 28, "bold"), 
            text_color="#ff4757",
            justify="center"
        )
        self.label.pack(pady=(50, 40))

        self.u_ent = ctk.CTkEntry(self, placeholder_text="Логин", width=350, height=50)
        self.u_ent.pack(pady=10)

        self.p_ent = ctk.CTkEntry(self, placeholder_text="Пароль", width=350, height=50, show="*")
        self.p_ent.pack(pady=10)

        self.btn = ctk.CTkButton(
            self, 
            text="ВОЙТИ", 
            fg_color="#2ecc71", 
            hover_color="#27ae60",
            width=350, 
            height=55, 
            font=("Arial", 16, "bold"), 
            command=self.login
        )
        self.btn.pack(pady=30)

    def login(self):
        username = self.u_ent.get()
        password = self.p_ent.get()
        user = self.db.login(username, password)
        if user:
            self.on_success(user)
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

class RegisterModal(BaseModal):
    """Окно регистрации новых пользователей (только для админа)."""
    def __init__(self, parent, db):
        super().__init__(parent, "Регистрация доступа", "500x650")
        self.db = db

        ctk.CTkLabel(
            self, 
            text="👑 РЕГИСТРАЦИЯ", 
            font=("Arial", 26, "bold"), 
            text_color="#ff4757"
        ).pack(pady=30)

        self.u_ent = ctk.CTkEntry(self, placeholder_text="Логин", width=400, height=50)
        self.u_ent.pack(pady=10)

        self.p_ent = ctk.CTkEntry(self, placeholder_text="Пароль", width=400, height=50)
        self.p_ent.pack(pady=10)

        self.role_var = ctk.StringVar(value="master")
        self.role_opt = ctk.CTkOptionMenu(
            self, 
            variable=self.role_var, 
            values=["admin", "master"], 
            width=400, 
            height=50
        )
        self.role_opt.pack(pady=10)

        self.btn = ctk.CTkButton(
            self, 
            text="СОЗДАТЬ АККАУНТ", 
            fg_color="#3498db", 
            width=400, 
            height=55, 
            command=self.register
        )
        self.btn.pack(pady=30)

    def register(self):
        u = self.u_ent.get().strip()
        p = self.p_ent.get().strip()
        r = self.role_var.get()
        
        if not u or not p:
            messagebox.showwarning("Ошибка", "Заполните все поля")
            return

        success, msg = self.db.register_user(u, p, r, None)
        if success:
            messagebox.showinfo("Успех", msg)
            self.destroy()
        else:
            messagebox.showerror("Ошибка", msg)

class ClientModal(BaseModal):
    """Карточка клиента."""
    def __init__(self, parent, db, data=None, on_save=None):
        super().__init__(parent, "Профиль клиента", "550x650")
        self.db = db
        self.data = data
        self.on_save = on_save

        ctk.CTkLabel(
            self, 
            text="ПРОФИЛЬ КЛИЕНТА", 
            font=("Arial", 26, "bold"), 
            text_color="#3498db"
        ).pack(pady=40)

        self.n_ent = ctk.CTkEntry(self, placeholder_text="ФИО", width=420, height=55)
        self.n_ent.pack(pady=10)

        self.p_ent = ctk.CTkEntry(self, placeholder_text="Номер телефона", width=420, height=55)
        self.p_ent.pack(pady=10)

        if data:
            self.n_ent.insert(0, data['name'])
            self.p_ent.insert(0, data.get('phone') or '')

        self.save_btn = ctk.CTkButton(
            self, 
            text="СОХРАНИТЬ", 
            fg_color="#3498db", 
            height=60, 
            width=420, 
            command=self.save
        )
        self.save_btn.pack(pady=(40, 10))

        if data:
            self.del_btn = ctk.CTkButton(
                self, 
                text="УДАЛИТЬ КЛИЕНТА", 
                fg_color="#c0392b", 
                height=45, 
                width=420, 
                command=self.delete
            )
            self.del_btn.pack(pady=5)

    def save(self):
        name = self.n_ent.get().strip()
        phone = self.p_ent.get().strip()
        
        if not name:
            messagebox.showwarning("!", "Введите имя")
            return

        if self.data:
            self.db.execute("UPDATE clients SET name=%s, phone=%s WHERE id=%s", (name, phone, self.data['id']))
        else:
            self.db.execute("INSERT INTO clients (name, phone) VALUES (%s, %s)", (name, phone))
        
        if self.on_save:
            self.on_save()
        self.destroy()

    def delete(self):
        if messagebox.askyesno("Удаление", "Удалить клиента и все его записи?"):
            self.db.execute("DELETE FROM clients WHERE id=%s", (self.data['id'],))
            if self.on_save:
                self.on_save()
            self.destroy()

class MasterModal(BaseModal):
    """Карточка мастера."""
    def __init__(self, parent, db, data=None, on_save=None):
        super().__init__(parent, "Мастер", "550x850")
        self.db = db
        self.data = data
        self.on_save = on_save
        
        # Сбор категорий для специализации
        categories_query = self.db.fetch("SELECT DISTINCT category FROM services")
        db_cats = [c['category'] for c in categories_query]
        self.available_categories = sorted(list(set(["Стрижки", "Окрашивание", "Уход", "Маникюр"] + db_cats)))
        
        self.checks = {}

        ctk.CTkLabel(
            self, 
            text="КАРТОЧКА МАСТЕРА", 
            font=("Arial", 26, "bold"), 
            text_color="#3498db"
        ).pack(pady=20)

        self.name_ent = ctk.CTkEntry(self, placeholder_text="ФИО Мастера", width=420, height=55)
        self.name_ent.pack(pady=10)

        ctk.CTkLabel(self, text="Специализация (категории):", font=("Arial", 14)).pack(pady=5)
        
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(pady=10)

        saved_specs = []
        if data and data.get('specialization'):
            saved_specs = data['specialization'].split(", ")

        for i, cat in enumerate(self.available_categories):
            var = ctk.BooleanVar(value=cat in saved_specs)
            cb = ctk.CTkCheckBox(grid, text=cat, variable=var)
            cb.grid(row=i//2, column=i%2, padx=15, pady=8, sticky="w")
            self.checks[cat] = var

        if data:
            self.name_ent.insert(0, data['name'])

        self.save_btn = ctk.CTkButton(
            self, 
            text="СОХРАНИТЬ", 
            fg_color="#3498db", 
            height=60, 
            width=420, 
            command=self.save
        )
        self.save_btn.pack(pady=30)
        
        if data:
            ctk.CTkButton(
                self, 
                text="УДАЛИТЬ", 
                fg_color="#c0392b", 
                height=45, 
                width=420, 
                command=self.delete
            ).pack()

    def save(self):
        name = self.name_ent.get().strip()
        selected_specs = [cat for cat, var in self.checks.items() if var.get()]
        specs_str = ", ".join(selected_specs)
        
        if not name:
            return

        if self.data:
            self.db.execute("UPDATE masters SET name=%s, specialization=%s WHERE id=%s", (name, specs_str, self.data['id']))
        else:
            self.db.execute("INSERT INTO masters (name, specialization) VALUES (%s, %s)", (name, specs_str))
        
        if self.on_save:
            self.on_save()
        self.destroy()

    def delete(self):
        if messagebox.askyesno("Удаление", "Удалить мастера из базы?"):
            self.db.execute("DELETE FROM masters WHERE id=%s", (self.data['id'],))
            if self.on_save:
                self.on_save()
            self.destroy()

class ServiceModal(BaseModal):
    """Окно управления услугами с поддержкой новых категорий."""
    def __init__(self, parent, db, data=None, on_save=None):
        super().__init__(parent, "Услуга", "550x700")
        self.db = db
        self.data = data
        self.on_save = on_save

        ctk.CTkLabel(
            self, 
            text="УПРАВЛЕНИЕ УСЛУГОЙ", 
            font=("Arial", 22, "bold"), 
            text_color="#3498db"
        ).pack(pady=30)

        self.name_ent = ctk.CTkEntry(self, placeholder_text="Название услуги", width=420, height=55)
        self.name_ent.pack(pady=8)
        
        # Категории: ComboBox позволяет вписать новую категорию вручную
        cats_data = self.db.fetch("SELECT DISTINCT category FROM services")
        cats = [c['category'] for c in cats_data] if cats_data else ["Стрижки", "Окрашивание"]
        
        ctk.CTkLabel(self, text="Категория (выберите или впишите новую):", font=("Arial", 12)).pack()
        self.cat_opt = ctk.CTkComboBox(self, values=cats, width=420, height=55)
        self.cat_opt.pack(pady=8)
        
        self.price_ent = ctk.CTkEntry(self, placeholder_text="Стоимость (руб)", width=420, height=55)
        self.price_ent.pack(pady=8)
        
        self.dur_ent = ctk.CTkEntry(self, placeholder_text="Длительность (мин)", width=420, height=55)
        self.dur_ent.pack(pady=8)

        if data:
            self.name_ent.insert(0, data['name'])
            self.cat_opt.set(data['category'])
            self.price_ent.insert(0, str(int(data['price'])))
            self.dur_ent.insert(0, str(data['duration']))
        else:
            self.dur_ent.insert(0, "60")

        self.save_btn = ctk.CTkButton(
            self, 
            text="СОХРАНИТЬ", 
            fg_color="#3498db", 
            height=60, 
            width=420, 
            command=self.save
        )
        self.save_btn.pack(pady=30)

        if data:
            ctk.CTkButton(
                self, 
                text="УДАЛИТЬ УСЛУГУ", 
                fg_color="#c0392b", 
                height=45, 
                width=420, 
                command=self.delete
            ).pack()

    def save(self):
        try:
            n = self.name_ent.get()
            c = self.cat_opt.get() # Получаем значение (выбранное или введенное)
            p = float(self.price_ent.get())
            d = int(self.dur_ent.get())
            
            if self.data:
                self.db.execute(
                    "UPDATE services SET name=%s, category=%s, price=%s, duration=%s WHERE id=%s", 
                    (n, c, p, d, self.data['id'])
                )
            else:
                self.db.execute(
                    "INSERT INTO services (name, category, price, duration) VALUES (%s, %s, %s, %s)", 
                    (n, c, p, d)
                )
            
            if self.on_save:
                self.on_save()
            self.destroy()
        except ValueError:
            messagebox.showerror("Ошибка", "Цена и длительность должны быть числами")

    def delete(self):
        if messagebox.askyesno("Удаление", "Удалить услугу из прайс-листа?"):
            self.db.execute("DELETE FROM services WHERE id=%s", (self.data['id'],))
            if self.on_save:
                self.on_save()
            self.destroy()

class AppointmentModal(BaseModal):
    """Главное окно записи на визит."""
    def __init__(self, parent, db, on_save=None, data=None):
        super().__init__(parent, "Запись", "600x850")
        self.db = db
        self.on_save = on_save
        self.data = data
        self.service_vars = {}

        ctk.CTkLabel(
            self, 
            text="ОФОРМЛЕНИЕ ЗАПИСИ", 
            font=("Arial", 26, "bold"), 
            text_color="#2ecc71"
        ).pack(pady=20)

        # Выбор клиента
        clients = self.db.fetch("SELECT id, name FROM clients ORDER BY name")
        self.c_map = {c['name']: c['id'] for c in clients}
        
        ctk.CTkLabel(self, text="Клиент:", font=("Arial", 12)).pack(anchor="w", padx=75)
        self.c_opt = ctk.CTkOptionMenu(self, values=list(self.c_map.keys()), width=450, height=50)
        self.c_opt.pack(pady=10)

        # Выбор мастера
        masters = self.db.fetch("SELECT id, name, specialization FROM masters ORDER BY name")
        self.m_map = {m['name']: m for m in masters}
        
        ctk.CTkLabel(self, text="Мастер:", font=("Arial", 12)).pack(anchor="w", padx=75)
        self.m_opt = ctk.CTkOptionMenu(
            self, 
            values=list(self.m_map.keys()), 
            width=450, 
            height=50, 
            command=self.filter_services
        )
        self.m_opt.pack(pady=10)

        # Список услуг мастера
        ctk.CTkLabel(self, text="Выберите услуги:", font=("Arial", 12)).pack(anchor="w", padx=75)
        self.services_frame = ctk.CTkScrollableFrame(self, width=420, height=220, fg_color="#1a1a1a")
        self.services_frame.pack(pady=10)

        # Дата и время
        ctk.CTkLabel(self, text="Дата и время (ДД.ММ.ГГГГ ЧЧ:ММ):", font=("Arial", 12)).pack(anchor="w", padx=75)
        self.dt_ent = ctk.CTkEntry(self, placeholder_text="ДД.ММ.ГГГГ ЧЧ:ММ", width=450, height=55)
        self.dt_ent.pack(pady=10)

        if data:
            self.c_opt.set(data['client'])
            self.m_opt.set(data['master'])
            self.dt_ent.insert(0, data['appointment_date'].strftime("%d.%m.%Y %H:%M"))
            self.filter_services(data['master'])
        else:
            self.dt_ent.insert(0, datetime.now().strftime("%d.%m.%Y 10:00"))
            if list(self.m_map.keys()):
                self.filter_services(list(self.m_map.keys())[0])

        self.save_btn = ctk.CTkButton(
            self, 
            text="СОХРАНИТЬ ЗАПИСЬ", 
            fg_color="#2ecc71", 
            hover_color="#27ae60",
            height=65, 
            width=450, 
            font=("Arial", 16, "bold"),
            command=self.save
        )
        self.save_btn.pack(pady=20)

    def filter_services(self, m_name):
        """Отображает только те услуги, которые умеет делать выбранный мастер."""
        for w in self.services_frame.winfo_children():
            w.destroy()
        
        self.service_vars.clear()
        master = self.m_map.get(m_name)
        specs = master['specialization'].split(", ") if master and master['specialization'] else []
        
        all_services = self.db.fetch("SELECT id, name, category, price FROM services ORDER BY name")
        
        # Получаем уже выбранные услуги, если это редактирование
        saved_sids = []
        if self.data:
            saved_sids = self.db.get_appointment_services(self.data['id'])

        for s in all_services:
            if s['category'] in specs:
                var = ctk.BooleanVar(value=s['id'] in saved_sids)
                cb = ctk.CTkCheckBox(
                    self.services_frame, 
                    text=f"{s['name']} — {int(s['price'])}р.", 
                    variable=var,
                    font=("Arial", 13)
                )
                cb.pack(pady=5, padx=10, anchor="w")
                self.service_vars[s['id']] = var

    def save(self):
        try:
            client_name = self.c_opt.get()
            master_name = self.m_opt.get()
            
            cid = self.c_map[client_name]
            mid = self.m_map[master_name]['id']
            
            selected_sids = [sid for sid, var in self.service_vars.items() if var.get()]
            
            date_str = self.dt_ent.get()
            appt_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
            
            if not selected_sids:
                messagebox.showwarning("Внимание", "Выберите хотя бы одну услугу")
                return

            if self.data:
                self.db.update_appointment(self.data['id'], cid, mid, selected_sids, appt_date)
            else:
                self.db.add_appointment(cid, mid, selected_sids, appt_date)
            
            if self.on_save:
                self.on_save()
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")