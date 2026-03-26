import customtkinter as ctk
from database import DBManager
from gui_components import AppointmentModal, ServiceModal, MasterModal, ClientModal, LoginModal, RegisterModal, COLORS
from tkinter import messagebox, filedialog
from datetime import datetime
from docx import Document
import os

class SilkWayApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("SILK WAY PREMIUM SYSTEM")
        self.geometry("1450x900")
        ctk.set_appearance_mode("dark")
        
        self.db = DBManager()
        self.current_user = None

        # Навигационная панель
        self.nav_frame = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#0a0a0a")
        self.nav_frame.pack_propagate(False)

        # Основная рабочая область
        self.main_view = ctk.CTkFrame(self, fg_color="#121212", corner_radius=0)
        
        self.journal_data = []
        self.clients_data = []
        
        self.after(100, self.require_login)

    def require_login(self):
        """Вызов окна входа"""
        LoginModal(self, self.db, self.on_login_success)

    def on_login_success(self, user):
        self.current_user = user
        self.nav_frame.pack(side="left", fill="y")
        self.main_view.pack(side="right", fill="both", expand=True)
        self.build_ui()

    def logout(self):
        """Функция выхода из системы"""
        if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти из системы?"):
            self.current_user = None
            self.nav_frame.pack_forget()
            self.main_view.pack_forget()
            self.clear_view()
            self.require_login()

    def build_ui(self):
        for widget in self.nav_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.nav_frame, text="SILK WAY", font=("Arial", 36, "bold"), text_color="#3498db").pack(pady=(60, 5))
        role_txt = "АДМИНИСТРАТОР" if self.current_user['role'] == 'admin' else "МАСТЕР"
        ctk.CTkLabel(self.nav_frame, text=role_txt, font=("Arial", 11, "bold"), text_color="#2ecc71").pack(pady=(0, 60))

        if self.current_user['role'] == 'admin':
            self.create_nav_btn("📋   Журнал записей", self.show_journal)
            self.create_nav_btn("👥   Клиенты", self.show_clients)
            self.create_nav_btn("💰   Прайс-лист", self.show_services)
            self.create_nav_btn("👤   Мастера", self.show_masters)
            self.create_nav_btn("📊   Аналитика", self.show_analytics)
            self.create_nav_btn("🔐   Доступ (Регистрация)", self.show_registration)
            
            # Кнопка выхода внизу
            ctk.CTkButton(self.nav_frame, text="ВЫХОД", fg_color="#c0392b", hover_color="#a93226", 
                          height=45, font=("Arial", 14), command=self.logout).pack(side="bottom", pady=20, padx=30)

            ctk.CTkButton(self.nav_frame, text="+ НОВАЯ ЗАПИСЬ", fg_color="#2ecc71", hover_color="#27ae60", 
                          height=55, font=("Arial", 15, "bold"), corner_radius=12,
                          command=lambda: AppointmentModal(self, self.db, self.show_journal)).pack(side="bottom", pady=10, padx=30)
        else:
            self.create_nav_btn("📋   Мои записи", self.show_journal)
            ctk.CTkButton(self.nav_frame, text="ВЫХОД", fg_color="#c0392b", hover_color="#a93226", 
                          height=45, font=("Arial", 14), command=self.logout).pack(side="bottom", pady=50, padx=30)

        self.show_journal()

    def create_nav_btn(self, text, command):
        btn = ctk.CTkButton(self.nav_frame, text=text, anchor="w", fg_color="transparent", 
                            text_color="#aaa", hover_color="#161616", height=60, 
                            font=("Arial", 16), command=command)
        btn.pack(fill="x", padx=15, pady=3)

    def clear_view(self):
        for widget in self.main_view.winfo_children():
            widget.destroy()

    def show_registration(self):
        RegisterModal(self, self.db)

    # --- ЖУРНАЛ ---
    def confirm_delete_appointment(self, aid):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту запись?"):
            self.db.execute("DELETE FROM appointments WHERE id=%s", (aid,))
            self.show_journal()

    def print_receipt(self, r):
        """Система генерации чеков в формате TXT"""
        try:
            filename = f"Receipt_{r['id']}_{datetime.now().strftime('%H%M%S')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("      SILK WAY PREMIUM SALON      \n")
                f.write("----------------------------------\n")
                f.write(f"Чек №: {r['id']}\n")
                f.write(f"Дата: {r['appointment_date'].strftime('%d.%m.%Y %H:%M')}\n")
                f.write(f"Клиент: {r['client']}\n")
                f.write(f"Мастер: {r['master']}\n")
                f.write("----------------------------------\n")
                f.write(f"Услуга: {r['service']}\n")
                f.write(f"ИТОГО К ОПЛАТЕ: {int(r['price'])} руб.\n")
                f.write("----------------------------------\n")
                f.write("   Спасибо, что выбираете нас!    \n")
            
            os.startfile(filename) # Открывает файл в Блокноте
            messagebox.showinfo("Успех", f"Чек сформирован: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать чек: {e}")

    def show_journal(self):
        self.clear_view()
        hdr = ctk.CTkFrame(self.main_view, fg_color="transparent")
        hdr.pack(fill="x", padx=50, pady=(50, 30))
        title_text = "РАСПИСАНИЕ" if self.current_user['role'] == 'admin' else "МОИ ВИЗИТЫ"
        ctk.CTkLabel(hdr, text=title_text, font=("Arial", 38, "bold")).pack(side="left")
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.render_journal_list)
        ctk.CTkEntry(hdr, textvariable=self.search_var, placeholder_text="Поиск по имени или услуге...", width=300, height=45).pack(side="right")

        self.journal_container = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent")
        self.journal_container.pack(fill="both", expand=True, padx=40)

        master_id = self.current_user['master_id'] if self.current_user['role'] == 'master' else None
        self.journal_data = self.db.get_journal(master_id=master_id)
        self.render_journal_list()

    def render_journal_list(self, *args):
        for widget in self.journal_container.winfo_children():
            widget.destroy()

        query = self.search_var.get().lower()
        filtered_data = [r for r in self.journal_data if query in r['client'].lower() or query in r['service'].lower()]

        for r in filtered_data:
            clr = COLORS.get(r['category'])
            dt = r['appointment_date']
            
            card = ctk.CTkFrame(self.journal_container, fg_color="#1a1a1a", height=125, corner_radius=15)
            card.pack(fill="x", pady=8); card.pack_propagate(False)
            ctk.CTkFrame(card, width=7, fg_color=clr).pack(side="left", fill="y")

            t_f = ctk.CTkFrame(card, fg_color="transparent")
            t_f.pack(side="left", padx=30)
            ctk.CTkLabel(t_f, text=dt.strftime('%H:%M'), font=("Arial", 30, "bold")).pack()
            ctk.CTkLabel(t_f, text=dt.strftime('%d.%m'), font=("Arial", 13), text_color="#555").pack()

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", padx=20, fill="both", expand=True, pady=15)
            
            ctk.CTkLabel(info, text=f"{r['service']} — {int(r['price'])} ₽", font=("Arial", 18, "bold"), text_color=clr, anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"👤 {r['client']}  |  ✂️ {r['master']}", font=("Arial", 15), text_color="#777", anchor="w").pack(fill="x", pady=(5, 0))

            # Кнопка печати чека (видна если статус Завершено)
            if r['status'] == "Завершено":
                ctk.CTkButton(card, text="🧾 ЧЕК", width=80, height=42, fg_color="#f39c12", hover_color="#e67e22",
                              command=lambda row=r: self.print_receipt(row)).pack(side="right", padx=10)

            if self.current_user['role'] == 'admin':
                ctk.CTkButton(card, text="🗑", width=45, height=45, fg_color="#262626", hover_color="#c0392b",
                              command=lambda aid=r['id']: self.confirm_delete_appointment(aid)).pack(side="right", padx=10)
                
                s_var = ctk.StringVar(value=r['status'])
                opt = ctk.CTkOptionMenu(card, values=["Ожидание", "В процессе", "Завершено", "Отмена"],
                                        variable=s_var, width=155, height=42, fg_color="#262626",
                                        command=lambda val, aid=r['id']: (self.db.update_status(aid, val), self.show_journal()))
                opt.pack(side="right", padx=5)
            else:
                vals = [r['status'], "Завершено"] if r['status'] != "Завершено" else ["Завершено"]
                s_var = ctk.StringVar(value=r['status'])
                opt = ctk.CTkOptionMenu(card, values=vals,
                                        variable=s_var, width=155, height=42, fg_color="#262626",
                                        command=lambda val, aid=r['id']: (self.db.update_status(aid, val), self.show_journal()))
                opt.pack(side="right", padx=30)

    # --- КЛИЕНТЫ ---
    def show_clients(self):
        self.clear_view()
        hdr = ctk.CTkFrame(self.main_view, fg_color="transparent")
        hdr.pack(fill="x", padx=50, pady=45)
        ctk.CTkLabel(hdr, text="КЛИЕНТСКАЯ БАЗА", font=("Arial", 38, "bold")).pack(side="left")
        
        controls = ctk.CTkFrame(hdr, fg_color="transparent")
        controls.pack(side="right")
        self.client_search_var = ctk.StringVar()
        self.client_search_var.trace_add("write", self.render_clients_list)
        ctk.CTkEntry(controls, textvariable=self.client_search_var, placeholder_text="Поиск...", width=200, height=45).pack(side="left", padx=15)
        ctk.CTkButton(controls, text="+ НОВЫЙ КЛИЕНТ", fg_color="#3498db", height=45, font=("Arial", 14, "bold"),
                      command=lambda: ClientModal(self, self.db, on_save=self.show_clients)).pack(side="left")

        self.clients_container = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent")
        self.clients_container.pack(fill="both", expand=True, padx=40)
        
        self.clients_data = self.db.fetch("SELECT * FROM clients ORDER BY name")
        self.render_clients_list()

    def render_clients_list(self, *args):
        for widget in self.clients_container.winfo_children():
            widget.destroy()
            
        query = self.client_search_var.get().lower()
        filtered = [c for c in self.clients_data if query in c['name'].lower() or (c.get('phone') and query in c['phone'])]

        for c in filtered:
            f = ctk.CTkFrame(self.clients_container, fg_color="#1a1a1a", height=100, corner_radius=15)
            f.pack(fill="x", pady=8); f.pack_propagate(False)
            
            info = ctk.CTkFrame(f, fg_color="transparent")
            info.pack(side="left", padx=30, fill="y")
            ctk.CTkLabel(info, text=c['name'], font=("Arial", 22, "bold"), anchor="w").pack(pady=(15, 0))
            ctk.CTkLabel(info, text=f"📞 {c.get('phone') or 'Нет номера'}  |  📧 {c.get('email') or '---'}", 
                         font=("Arial", 14), text_color="#555", anchor="w").pack()
            
            ctk.CTkButton(f, text="ПРОФИЛЬ", width=140, height=45, fg_color="#262626",
                          command=lambda d=c: ClientModal(self, self.db, d, self.show_clients)).pack(side="right", padx=30)

    # --- УСЛУГИ ---
    def show_services(self):
        self.clear_view()
        hdr = ctk.CTkFrame(self.main_view, fg_color="transparent")
        hdr.pack(fill="x", padx=50, pady=45)
        ctk.CTkLabel(hdr, text="ПРАЙС-ЛИСТ", font=("Arial", 38, "bold")).pack(side="left")
        ctk.CTkButton(hdr, text="+ ДОБАВИТЬ УСЛУГУ", fg_color="#3498db", 
                      command=lambda: ServiceModal(self, self.db, on_save=self.show_services)).pack(side="right")

        scroll = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=40)
        for s in self.db.fetch("SELECT * FROM services ORDER BY category, name"):
            clr = COLORS.get(s['category'])
            f = ctk.CTkFrame(scroll, fg_color="#1a1a1a", height=85, corner_radius=12)
            f.pack(fill="x", pady=6); f.pack_propagate(False)
            ctk.CTkFrame(f, width=7, fg_color=clr).pack(side="left", fill="y")
            ctk.CTkLabel(f, text=s['name'], font=("Arial", 20, "bold"), anchor="w").pack(side="left", padx=30)
            ctk.CTkLabel(f, text=f"{int(s['price'])} ₽", font=("Arial", 22, "bold"), text_color="#2ecc71").pack(side="left", padx=50)
            
            ctk.CTkLabel(f, text=f"⏳ {s.get('duration', 60)} мин", font=("Arial", 16), text_color="#7f8c8d").pack(side="left", padx=20)
            
            ctk.CTkButton(f, text="✎", width=50, height=50, fg_color="#262626", 
                          command=lambda d=s: ServiceModal(self, self.db, d, self.show_services)).pack(side="right", padx=25)

    # --- МАСТЕРА ---
    def show_masters(self):
        self.clear_view()
        hdr = ctk.CTkFrame(self.main_view, fg_color="transparent")
        hdr.pack(fill="x", padx=50, pady=45)
        ctk.CTkLabel(hdr, text="НАША КОМАНДА", font=("Arial", 38, "bold")).pack(side="left")
        ctk.CTkButton(hdr, text="+ НОВЫЙ МАСТЕР", fg_color="#3498db", 
                      command=lambda: MasterModal(self, self.db, on_save=self.show_masters)).pack(side="right")
        
        scroll = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=40)
        for m in self.db.fetch("SELECT * FROM masters ORDER BY name"):
            f = ctk.CTkFrame(scroll, fg_color="#1a1a1a", height=105, corner_radius=15)
            f.pack(fill="x", pady=8); f.pack_propagate(False)
            
            info = ctk.CTkFrame(f, fg_color="transparent")
            info.pack(side="left", padx=30, fill="y")
            ctk.CTkLabel(info, text=m['name'], font=("Arial", 22, "bold")).pack(pady=(10, 0), anchor="w")
            ctk.CTkLabel(info, text=f"Спец: {m.get('specialization') or 'Все'}  |  График: {m.get('work_start')} - {m.get('work_end')}", 
                         font=("Arial", 14), text_color="#555").pack(anchor="w")
            
            ctk.CTkButton(f, text="РЕДАКТИРОВАТЬ", width=150, height=45, fg_color="#262626",
                          command=lambda d=m: MasterModal(self, self.db, d, self.show_masters)).pack(side="right", padx=30)

    # --- АНАЛИТИКА ---
    def show_analytics(self):
        self.clear_view()
        rev, cli = self.db.get_stats_summary()
        hdr = ctk.CTkFrame(self.main_view, fg_color="transparent")
        hdr.pack(fill="x", padx=50, pady=50)
        ctk.CTkLabel(hdr, text="СТАТИСТИКА", font=("Arial", 38, "bold")).pack(side="left")
        ctk.CTkButton(hdr, text="ОТЧЕТ В WORD", fg_color="#2ecc71", font=("Arial", 13, "bold"), height=45,
                      command=self.export_to_word).pack(side="right")

        stats_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        stats_f.pack(fill="x", padx=50, pady=20)
        
        for label, val, color, icon in [("ОБЩИЙ ДОХОД", f"{int(rev):,} ₽", "#2ecc71", "💰"), 
                                        ("ВСЕГО КЛИЕНТОВ", str(cli), "#3498db", "👥")]:
            card = ctk.CTkFrame(stats_f, fg_color="#1a1a1a", width=420, height=180, corner_radius=20)
            card.pack(side="left", padx=(0, 40)); card.pack_propagate(False)
            ctk.CTkLabel(card, text=f"{icon} {label}", font=("Arial", 14, "bold"), text_color="#444").pack(pady=(35, 10))
            ctk.CTkLabel(card, text=val.replace(',', ' '), font=("Arial", 44, "bold"), text_color=color).pack()

    def export_to_word(self):
        path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word Document", "*.docx")])
        if not path: return
        try:
            doc = Document()
            doc.add_heading('SILK WAY PREMIUM REPORT', 0)
            rev, cli = self.db.get_stats_summary()
            doc.add_heading(f'Дата: {datetime.now().strftime("%d.%m.%Y")}', level=1)
            doc.add_paragraph(f"Доход: {int(rev)} руб.")
            doc.add_paragraph(f"Клиентов: {cli}")
            doc.add_heading('Популярность услуг', level=2)
            for item in self.db.get_service_demand_report():
                doc.add_paragraph(f"• {item['name']}: {item['count']} визитов (на сумму {int(item['total_revenue'])} руб.)")
            doc.save(path)
            messagebox.showinfo("Готово", f"Отчет сохранен в {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать файл: {e}")

if __name__ == "__main__":
    app = SilkWayApp()
    app.mainloop()