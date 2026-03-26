import psycopg2
from psycopg2 import extras
from datetime import datetime, timedelta

class DBManager:
    def __init__(self):
        self.params = {
            "dbname": "silkway_db", 
            "user": "postgres", 
            "password": "1234",
            "host": "localhost", 
            "port": "5432"
        }
        self.conn = None
        try:
            self.conn = psycopg2.connect(**self.params)
            self.conn.autocommit = True
            self._check_db_structure()
            self._migrate_db()
            self._ensure_admin_exists()
            print("База данных подключена. Система безопасности и связей активна.")
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")

    def _check_db_structure(self):
        if not self.conn: return
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS masters (
                    id SERIAL PRIMARY KEY, 
                    name TEXT UNIQUE,
                    specialization TEXT DEFAULT '',
                    work_start TEXT DEFAULT '09:00',
                    work_end TEXT DEFAULT '21:00'
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT DEFAULT 'master',
                    master_id INTEGER REFERENCES masters(id) ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id SERIAL PRIMARY KEY, 
                    name TEXT UNIQUE, 
                    phone TEXT, 
                    email TEXT DEFAULT ''
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id SERIAL PRIMARY KEY, 
                    name TEXT, 
                    category TEXT, 
                    price NUMERIC, 
                    duration INTEGER DEFAULT 60
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id SERIAL PRIMARY KEY,
                    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
                    master_id INTEGER REFERENCES masters(id) ON DELETE CASCADE,
                    appointment_date TIMESTAMP, 
                    status TEXT DEFAULT 'Ожидание'
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS appointment_services (
                    appointment_id INTEGER REFERENCES appointments(id) ON DELETE CASCADE,
                    service_id INTEGER REFERENCES services(id) ON DELETE CASCADE,
                    PRIMARY KEY (appointment_id, service_id)
                )
            """)

    def _migrate_db(self):
        if not self.conn: return
        with self.conn.cursor() as cur:
            # Миграция времени работы мастеров
            cur.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='masters' AND column_name='work_start') THEN
                        ALTER TABLE masters ADD COLUMN work_start TEXT DEFAULT '09:00';
                        ALTER TABLE masters ADD COLUMN work_end TEXT DEFAULT '21:00';
                    END IF;
                END $$;
            """)
            # Миграция для множественного выбора услуг (перенос старых service_id в новую таблицу)
            cur.execute("""
                DO $$ 
                BEGIN 
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='appointments' AND column_name='service_id') THEN
                        INSERT INTO appointment_services (appointment_id, service_id)
                        SELECT id, service_id FROM appointments WHERE service_id IS NOT NULL
                        ON CONFLICT DO NOTHING;
                        
                        ALTER TABLE appointments DROP COLUMN service_id;
                    END IF;
                END $$;
            """)

    def _ensure_admin_exists(self):
        if not self.conn: return
        admins = self.fetch("SELECT * FROM users WHERE role='admin'")
        if not admins:
            self.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", ('admin', 'admin', 'admin'))

    def is_first_run(self):
        if not self.conn: return False
        users_count = self.fetch("SELECT COUNT(id) as count FROM users")
        if users_count and users_count[0]['count'] <= 1:
            return True
        return False

    def login(self, username, password):
        user = self.fetch("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        return user[0] if user else None

    def register_user(self, username, password, role, master_id=None):
        try:
            self.execute("INSERT INTO users (username, password, role, master_id) VALUES (%s, %s, %s, %s)", 
                         (username, password, role, master_id))
            return True, "Успешно зарегистрировано"
        except psycopg2.IntegrityError:
            return False, "Пользователь с таким логином уже существует"
        except Exception as e:
            return False, str(e)

    def execute(self, query, params=None):
        if not self.conn: return
        with self.conn.cursor() as cur:
            cur.execute(query, params)

    def fetch(self, query, params=None):
        if not self.conn: return []
        with self.conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def update_status(self, app_id, status):
        self.execute("UPDATE appointments SET status = %s WHERE id = %s", (status, app_id))

    def get_journal(self, master_id=None):
        query = """
            SELECT a.id, c.name as client, m.name as master, 
                   a.appointment_date, a.status, 
                   COALESCE(string_agg(s.name, ', '), 'Без услуг') as service,
                   COALESCE(SUM(s.price), 0) as price,
                   MAX(s.category) as category
            FROM appointments a 
            JOIN clients c ON a.client_id = c.id
            JOIN masters m ON a.master_id = m.id
            LEFT JOIN appointment_services aserv ON a.id = aserv.appointment_id
            LEFT JOIN services s ON aserv.service_id = s.id
        """
        params = []
        if master_id:
            query += " WHERE a.master_id = %s "
            params.append(master_id)
            
        query += " GROUP BY a.id, c.name, m.name, a.appointment_date, a.status ORDER BY a.appointment_date DESC"
        return self.fetch(query, tuple(params) if params else None)

    def add_appointment(self, client_id, master_id, service_ids, dt_obj):
        if not self.conn: return False
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO appointments (client_id, master_id, appointment_date) VALUES (%s, %s, %s) RETURNING id",
                    (client_id, master_id, dt_obj)
                )
                app_id = cur.fetchone()[0]
                for sid in service_ids:
                    cur.execute(
                        "INSERT INTO appointment_services (appointment_id, service_id) VALUES (%s, %s)",
                        (app_id, sid)
                    )
            return True
        except Exception as e:
            print(f"Ошибка создания записи: {e}")
            return False

    def is_master_free(self, master_id, start_dt, service_ids):
        if start_dt < datetime.now():
            return False, "Нельзя записать на прошедшее время"
        if not service_ids:
            return False, "Не выбраны услуги"

        format_strings = ','.join(['%s'] * len(service_ids))
        res = self.fetch(f"SELECT SUM(duration) as total_duration FROM services WHERE id IN ({format_strings})", tuple(service_ids))
        duration = res[0]['total_duration'] if res and res[0]['total_duration'] else 60
        end_dt = start_dt + timedelta(minutes=int(duration))

        overlap = self.fetch("""
            WITH app_durations AS (
                SELECT a.id, a.appointment_date as start_time,
                       a.appointment_date + (COALESCE(SUM(s.duration), 60) || ' minutes')::interval as end_time
                FROM appointments a
                LEFT JOIN appointment_services aserv ON a.id = aserv.appointment_id
                LEFT JOIN services s ON aserv.service_id = s.id
                WHERE a.master_id = %s AND a.status NOT IN ('Отмена', 'Завершено')
                GROUP BY a.id, a.appointment_date
            )
            SELECT id FROM app_durations
            WHERE (start_time, end_time) OVERLAPS (%s, %s)
        """, (master_id, start_dt, end_dt))
        
        if overlap:
            return False, "Мастер занят в этот интервал (пересечение с другой записью)"
        return True, "OK"

    def get_stats_summary(self):
        rev = self.fetch("""
            SELECT SUM(s.price) as total 
            FROM appointments a 
            JOIN appointment_services aserv ON a.id = aserv.appointment_id
            JOIN services s ON aserv.service_id = s.id 
            WHERE a.status = 'Завершено'
        """)
        cli = self.fetch("SELECT COUNT(id) as total FROM clients")
        return (rev[0]['total'] or 0), (cli[0]['total'] or 0)

    def get_service_demand_report(self):
        return self.fetch("""
            SELECT s.name, COUNT(a.id) as count, SUM(s.price) as total_revenue
            FROM services s 
            LEFT JOIN appointment_services aserv ON s.id = aserv.service_id
            LEFT JOIN appointments a ON aserv.appointment_id = a.id AND a.status = 'Завершено'
            GROUP BY s.name ORDER BY count DESC
        """)