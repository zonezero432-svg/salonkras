import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta

class COLORS:
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
            "Стрижки": COLORS.HAIR, "Окрашивание": COLORS.COLOR,
            "Уход": COLORS.FACE, "Маникюр": COLORS.NAILS,
            "Премиум": COLORS.PREMIUM, "SPA": COLORS.SPA,
            "Ожидание": COLORS.WAITING, "В процессе": COLORS.PROCESS,
            "Завершено": COLORS.DONE, "Отмена": COLORS.CANCEL
        }
        return mapping.get(key, default)

class BaseModal(ctk.CTkToplevel):
    def __init__(self, parent, title="Окно", size="550x750"):
        super().__init__(parent)
        self.title(title)
        self.geometry(size)
        self.configure(fg_color="#121212")
        self.transient(parent)
        self.grab_set()
        
        # Центрирование окна
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

class LoginModal(BaseModal):
    def __init__(self, parent, db, on_success):
        super().__init__(parent, "Авторизация", "450x550")
        self.db = db
        self.on_success = on_success
        # Если закрыть окно входа, закрывается всё приложение
        self.protocol("WM_DELETE_WINDOW", parent.destroy)

        ctk.CTkLabel(self, text="SILK WAY CLOUD", font=("Arial", 28, "bold"), text_color="#3498db").pack(pady=(50, 20))
        
        if self.db.is_first_run():
            ctk.CTkLabel(self, text="⚠️ Первый запуск! Дефолтный вход:\nЛогин: admin | Пароль: admin", 
                         font=("Arial", 14, "bold"), text_color="#f1c40f").pack(pady=(0, 20))
        else:
            ctk.CTkLabel(self, text="Введите ваши данные для входа", font=("Arial", 12), text_color="#7f8c8d").pack(pady=(0, 20))
        
        self.u_ent = ctk.CTkEntry(self, placeholder_text="Логин", width=350, height=50)
        self.u_ent.pack(pady=10)
        self.p_ent = ctk.CTkEntry(self, placeholder_text="Пароль", width=350, height=50, show="*")
        self.p_ent.pack(pady=10)

        ctk.CTkButton(self, text="ВОЙТИ", fg_color="#2ecc71", width=350, height=55, font=("Arial", 16, "bold"), command=self.login).pack(pady=30)

    def login(self):
        user = self.db.login(self.u_ent.get(), self.p_ent.get())
        if user:
            self.on_success(user)
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

class RegisterModal(BaseModal):
    def __init__(self, parent, db):
        super().__init__(parent, "Регистрация доступа", "500x650")
        self.db = db

        ctk.CTkLabel(self, text="РЕГИСТРАЦИЯ", font=("Arial", 26, "bold")).pack(pady=30)
        self.u_ent = ctk.CTkEntry(self, placeholder_text="Логин", width=400, height=50); self.u_ent.pack(pady=10)
        self.p_ent = ctk.CTkEntry(self, placeholder_text="Пароль", width=400, height=50); self.p_ent.pack(pady=10)

        self.role_var = ctk.StringVar(value="master")
        ctk.CTkOptionMenu(self, variable=self.role_var, values=["admin", "master"], width=400, height=50, command=self.toggle_master_menu).pack(pady=10)

        # Подгружаем мастеров для привязки аккаунта
        self.masters = self.db.fetch("SELECT id, name FROM masters")
        self.m_map = {m['name']: m['id'] for m in self.masters}
        
        master_values = list(self.m_map.keys()) if self.m_map else ["Нет мастеров"]
        self.m_opt = ctk.CTkOptionMenu(self, values=master_values, width=400, height=50)
        self.m_opt.pack(pady=10)

        ctk.CTkButton(self, text="СОЗДАТЬ АККАУНТ", fg_color="#3498db", width=400, height=55, command=self.register).pack(pady=30)

    def toggle_master_menu(self, role):
        if role == "admin": 
            self.m_opt.configure(state="disabled")
        else: 
            self.m_opt.configure(state="normal")

    def register(self):
        u, p, r = self.u_ent.get().strip(), self.p_ent.get().strip(), self.role_var.get()
        m_id = self.m_map.get(self.m_opt.get()) if r == "master" and self.m_map else None
        
        if not u or not p: 
            return messagebox.showwarning("Ошибка", "Заполните все поля")
        
        success, msg = self.db.register_user(u, p, r, m_id)
        if success:
            messagebox.showinfo("Успех", msg)
            self.destroy()
        else: 
            messagebox.showerror("Ошибка", msg)

class ClientModal(BaseModal):
    def __init__(self, parent, db, data=None, on_save=None):
        super().__init__(parent, "Профиль клиента")
        self.db, self.data, self.on_save = db, data, on_save
        
        ctk.CTkLabel(self, text="КЛИЕНТ", font=("Arial", 26, "bold"), text_color="#3498db").pack(pady=40)
        self.name_ent = ctk.CTkEntry(self, placeholder_text="ФИО", width=420, height=55, fg_color="#1a1a1a"); self.name_ent.pack(pady=10)
        self.phone_ent = ctk.CTkEntry(self, placeholder_text="Телефон", width=420, height=55, fg_color="#1a1a1a"); self.phone_ent.pack(pady=10)
        self.email_ent = ctk.CTkEntry(self, placeholder_text="Email", width=420, height=55, fg_color="#1a1a1a"); self.email_ent.pack(pady=10)

        if data:
            self.name_ent.insert(0, str(data.get('name') or ''))
            self.phone_ent.insert(0, str(data.get('phone') or ''))
            self.email_ent.insert(0, str(data.get('email') or ''))

        ctk.CTkButton(self, text="СОХРАНИТЬ", fg_color="#3498db", height=60, width=420, font=("Arial", 16, "bold"), command=self.save).pack(pady=(40, 10))
        if data: 
            ctk.CTkButton(self, text="УДАЛИТЬ КЛИЕНТА", fg_color="#c0392b", height=45, width=420, command=self.delete).pack(pady=5)

    def save(self):
        n, p, e = self.name_ent.get().strip(), self.phone_ent.get().strip(), self.email_ent.get().strip()
        if not n: return
        
        if self.data: 
            self.db.execute("UPDATE clients SET name=%s, phone=%s, email=%s WHERE id=%s", (n, p, e, self.data['id']))
        else: 
            self.db.execute("INSERT INTO clients (name, phone, email) VALUES (%s, %s, %s)", (n, p, e))
        
        if self.on_save: self.on_save()
        self.destroy()

    def delete(self):
        if messagebox.askyesno("Удаление", f"Удалить клиента {self.data['name']}?"):
            self.db.execute("DELETE FROM clients WHERE id=%s", (self.data['id'],))
            if self.on_save: self.on_save()
            self.destroy()

class MasterModal(BaseModal):
    def __init__(self, parent, db, data=None, on_save=None):
        super().__init__(parent, "Мастер", "550x850")
        self.db, self.data, self.on_save = db, data, on_save
        self.categories = ["Стрижки", "Окрашивание", "Уход", "Маникюр", "Премиум", "SPA"]
        self.checks = {}

        ctk.CTkLabel(self, text="МАСТЕР", font=("Arial", 26, "bold"), text_color="#3498db").pack(pady=20)
        self.name_ent = ctk.CTkEntry(self, placeholder_text="ФИО Мастера", width=420, height=55)
        self.name_ent.pack(pady=5)
        
        sched_f = ctk.CTkFrame(self, fg_color="transparent")
        sched_f.pack(pady=10)
        ctk.CTkLabel(sched_f, text="График (Начало - Конец):").pack()
        self.start_ent = ctk.CTkEntry(sched_f, placeholder_text="09:00", width=100); self.start_ent.pack(side="left", padx=5)
        self.end_ent = ctk.CTkEntry(sched_f, placeholder_text="21:00", width=100); self.end_ent.pack(side="left", padx=5)

        if data: 
            self.name_ent.insert(0, str(data.get('name') or ''))
            self.start_ent.insert(0, str(data.get('work_start') or '09:00'))
            self.end_ent.insert(0, str(data.get('work_end') or '21:00'))

        ctk.CTkLabel(self, text="Специализация:", font=("Arial", 14), text_color="#666").pack(pady=10)
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(pady=5)
        
        specs_str = data.get('specialization', '') if data else ''
        saved_specs = specs_str.split(", ") if specs_str else []
        
        for i, cat in enumerate(self.categories):
            var = ctk.BooleanVar(value=cat in saved_specs)
            cb = ctk.CTkCheckBox(grid, text=cat, variable=var, text_color="#ccc")
            cb.grid(row=i//2, column=i%2, padx=20, pady=10, sticky="w")
            self.checks[cat] = var

        ctk.CTkButton(self, text="СОХРАНИТЬ", fg_color="#3498db", height=60, width=420, command=self.save).pack(pady=(20, 10))
        if data: 
            ctk.CTkButton(self, text="УДАЛИТЬ МАСТЕРА", fg_color="#c0392b", height=45, width=420, command=self.delete).pack(pady=5)

    def save(self):
        name = self.name_ent.get().strip()
        ws = self.start_ent.get().strip() or '09:00'
        we = self.end_ent.get().strip() or '21:00'
        specs = ", ".join([cat for cat, var in self.checks.items() if var.get()])
        
        if name:
            if self.data: 
                self.db.execute("UPDATE masters SET name=%s, specialization=%s, work_start=%s, work_end=%s WHERE id=%s", (name, specs, ws, we, self.data['id']))
            else: 
                self.db.execute("INSERT INTO masters (name, specialization, work_start, work_end) VALUES (%s, %s, %s, %s)", (name, specs, ws, we))
            
            if self.on_save: self.on_save()
            self.destroy()

    def delete(self):
        if messagebox.askyesno("Удаление", f"Удалить мастера {self.data['name']}?"):
            self.db.execute("DELETE FROM masters WHERE id=%s", (self.data['id'],))
            if self.on_save: self.on_save()
            self.destroy()

class AppointmentModal(BaseModal):
    def __init__(self, parent, db, on_save=None):
        super().__init__(parent, "Новая запись", "600x850")
        self.db, self.on_save = db, on_save
        self.service_vars = {}

        ctk.CTkLabel(self, text="ЗАПИСЬ", font=("Arial", 26, "bold"), text_color="#2ecc71").pack(pady=20)

        # Клиенты
        clients = self.db.fetch("SELECT id, name FROM clients ORDER BY name")
        self.c_map = {c['name']: c['id'] for c in clients}
        client_vals = list(self.c_map.keys()) if self.c_map else ["Нет клиентов"]
        self.c_opt = ctk.CTkOptionMenu(self, values=client_vals, width=450, height=50); self.c_opt.pack(pady=10)

        # Мастера
        self.masters_data = self.db.fetch("SELECT id, name, specialization FROM masters ORDER BY name")
        self.m_map = {m['name']: m for m in self.masters_data}
        master_vals = list(self.m_map.keys()) if self.m_map else ["Нет мастеров"]
        self.m_opt = ctk.CTkOptionMenu(self, values=master_vals, width=450, height=50, command=self.filter_services)
        self.m_opt.pack(pady=10)

        # Все услуги (для фильтрации)
        self.all_services = self.db.fetch("SELECT id, name, category, price FROM services ORDER BY name")
        
        ctk.CTkLabel(self, text="Выберите услуги:", font=("Arial", 14), text_color="#aaa").pack(pady=(10, 0))
        self.services_frame = ctk.CTkScrollableFrame(self, width=420, height=180, fg_color="#1a1a1a")
        self.services_frame.pack(pady=5)

        # Дата и время
        f_time = ctk.CTkFrame(self, fg_color="transparent"); f_time.pack(pady=20)
        self.date_ent = ctk.CTkEntry(f_time, placeholder_text="ДД.ММ.ГГГГ", width=210, height=55); self.date_ent.pack(side="left", padx=5)
        self.date_ent.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.time_ent = ctk.CTkEntry(f_time, placeholder_text="ЧЧ:ММ", width=210, height=55); self.time_ent.pack(side="left", padx=5)

        ctk.CTkButton(self, text="Ближайшее свободное время", fg_color="#34495e", height=40, width=450, command=self.find_slot).pack(pady=5)
        ctk.CTkButton(self, text="ПОДТВЕРДИТЬ", fg_color="#2ecc71", height=65, width=450, command=self.save).pack(pady=20)
        
        if self.masters_data:
            self.filter_services(self.masters_data[0]['name'])

    def filter_services(self, master_name):
        for widget in self.services_frame.winfo_children():
            widget.destroy()
        self.service_vars.clear()

        master = self.m_map.get(master_name)
        if not master or not master.get('specialization'):
            ctk.CTkLabel(self.services_frame, text="У мастера нет специализаций").pack(pady=20)
            return

        allowed_cats = master['specialization'].split(", ")
        filtered = [s for s in self.all_services if s['category'] in allowed_cats]
        
        if not filtered:
            ctk.CTkLabel(self.services_frame, text="Нет услуг по профилю мастера").pack(pady=20)
            return

        for s in filtered:
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(self.services_frame, text=f"{s['name']} — {int(s['price'])} ₽", variable=var, font=("Arial", 14))
            cb.pack(pady=8, padx=10, anchor="w")
            self.service_vars[s['id']] = var

    def find_slot(self):
        self.time_ent.delete(0, 'end')
        self.time_ent.insert(0, (datetime.now() + timedelta(hours=1)).strftime("%H:00"))

    def save(self):
        try:
            if not self.c_map: return messagebox.showwarning("Ошибка", "Сначала добавьте клиента")
            
            cid = self.c_map.get(self.c_opt.get())
            mid = self.m_map.get(self.m_opt.get())['id']
            selected_sids = [sid for sid, var in self.service_vars.items() if var.get()]
            
            if not selected_sids:
                return messagebox.showwarning("Внимание", "Выберите минимум одну услугу")

            dt_str = f"{self.date_ent.get().strip()} {self.time_ent.get().strip()}"
            dt_obj = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")

            # Проверка доступности мастера через твой SQL метод
            free, msg = self.db.is_master_free(mid, dt_obj, selected_sids)
            if free:
                success = self.db.add_appointment(cid, mid, selected_sids, dt_obj)
                if success:
                    if self.on_save: self.on_save()
                    self.destroy()
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить запись")
            else: 
                messagebox.showwarning("Занято", msg)
        except ValueError: 
            messagebox.showerror("Ошибка", "Формат даты/времени: ДД.ММ.ГГГГ ЧЧ:ММ")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {e}")

class ServiceModal(BaseModal):
    def __init__(self, parent, db, data=None, on_save=None):
        super().__init__(parent, "Услуга", "550x700")
        self.db, self.data, self.on_save = db, data, on_save
        
        ctk.CTkLabel(self, text="УСЛУГА", font=("Arial", 22, "bold"), text_color="#3498db").pack(pady=30)
        self.name_ent = ctk.CTkEntry(self, placeholder_text="Название", width=420, height=55); self.name_ent.pack(pady=8)
        self.cat_opt = ctk.CTkOptionMenu(self, values=["Стрижки", "Окрашивание", "Уход", "Маникюр", "Премиум", "SPA"], width=420, height=55); self.cat_opt.pack(pady=8)
        self.price_ent = ctk.CTkEntry(self, placeholder_text="Цена", width=420, height=55); self.price_ent.pack(pady=8)
        self.dur_ent = ctk.CTkEntry(self, placeholder_text="Мин.", width=420, height=55); self.dur_ent.pack(pady=8)

        if data:
            self.name_ent.insert(0, str(data.get('name') or ''))
            self.cat_opt.set(str(data.get('category') or 'Стрижки'))
            self.price_ent.insert(0, str(int(data.get('price', 0))))
            self.dur_ent.insert(0, str(data.get('duration', 60)))

        ctk.CTkButton(self, text="СОХРАНИТЬ", fg_color="#3498db", height=60, width=420, command=self.save).pack(pady=(35, 10))
        if data: 
            ctk.CTkButton(self, text="УДАЛИТЬ", fg_color="#c0392b", height=45, width=420, command=self.delete).pack(pady=5)

    def save(self):
        try:
            n, c, p, d = self.name_ent.get(), self.cat_opt.get(), float(self.price_ent.get()), int(self.dur_ent.get())
            if self.data:
                self.db.execute("UPDATE services SET name=%s, category=%s, price=%s, duration=%s WHERE id=%s", (n, c, p, d, self.data['id']))
            else:
                self.db.execute("INSERT INTO services (name, category, price, duration) VALUES (%s, %s, %s, %s)", (n, c, p, d))
            if self.on_save: self.on_save()
            self.destroy()
        except Exception: 
            messagebox.showerror("Ошибка", "Проверьте числовые поля (Цена и Минуты)")

    def delete(self):
        if messagebox.askyesno("Удаление", "Удалить услугу?"):
            self.db.execute("DELETE FROM services WHERE id=%s", (self.data['id'],))
            if self.on_save: self.on_save()
            self.destroy()