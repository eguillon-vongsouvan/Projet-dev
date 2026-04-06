import os
import sys
import time

import pymysql

from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.config import Config  # noqa: E402
from app.security import encrypt_value, hash_password  # noqa: E402


def connect():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        charset="utf8mb4",
    )


def wait_for_db(max_wait_seconds: int = 30):
    deadline = time.time() + max_wait_seconds
    last_err = None
    while time.time() < deadline:
        try:
            conn = connect()
            conn.close()
            return True
        except Exception as e:
            last_err = e
            time.sleep(1.5)
    print(f"[init_db] DB indisponible après {max_wait_seconds}s: {last_err}", file=sys.stderr)
    return False


def create_schema(cur):
    # Mini-migrations idempotentes (pour évoluer sans drop la DB)
    def ensure_column(table: str, column: str, ddl: str):
        cur.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s
            """,
            (Config.MYSQL_DB, table, column),
        )
        if cur.fetchone()["cnt"] == 0:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
          id INT AUTO_INCREMENT PRIMARY KEY,
          username VARCHAR(50) NOT NULL UNIQUE,
          password_hash BLOB NOT NULL,
          role VARCHAR(20) NOT NULL,
          is_banned TINYINT(1) NOT NULL DEFAULT 0,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )
    ensure_column("users", "is_banned", "TINYINT(1) NOT NULL DEFAULT 0")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS classes (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(100) NOT NULL UNIQUE,
          teacher_id INT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_classes_teacher
            FOREIGN KEY (teacher_id) REFERENCES users(id)
            ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS class_students (
          class_id INT NOT NULL,
          student_id INT NOT NULL,
          PRIMARY KEY (class_id, student_id),
          CONSTRAINT fk_class_students_class
            FOREIGN KEY (class_id) REFERENCES classes(id)
            ON DELETE CASCADE,
          CONSTRAINT fk_class_students_student
            FOREIGN KEY (student_id) REFERENCES users(id)
            ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schedules (
          id INT AUTO_INCREMENT PRIMARY KEY,
          class_id INT NOT NULL,
          day_of_week TINYINT NOT NULL,
          start_time TIME NOT NULL,
          end_time TIME NOT NULL,
          location VARCHAR(100) NULL,
          CONSTRAINT fk_schedules_class
            FOREIGN KEY (class_id) REFERENCES classes(id)
            ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS assessments (
          id INT AUTO_INCREMENT PRIMARY KEY,
          class_id INT NOT NULL,
          title VARCHAR(100) NOT NULL,
          due_date DATE NULL,
          created_by INT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_assessments_class
            FOREIGN KEY (class_id) REFERENCES classes(id)
            ON DELETE CASCADE,
          CONSTRAINT fk_assessments_creator
            FOREIGN KEY (created_by) REFERENCES users(id)
            ON DELETE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS grades (
          id INT AUTO_INCREMENT PRIMARY KEY,
          assessment_id INT NOT NULL,
          student_id INT NOT NULL,
          grade_encrypted TEXT NOT NULL,
          updated_by INT NOT NULL,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          CONSTRAINT fk_grades_assessment
            FOREIGN KEY (assessment_id) REFERENCES assessments(id)
            ON DELETE CASCADE,
          CONSTRAINT fk_grades_student
            FOREIGN KEY (student_id) REFERENCES users(id)
            ON DELETE CASCADE,
          CONSTRAINT fk_grades_updater
            FOREIGN KEY (updated_by) REFERENCES users(id)
            ON DELETE RESTRICT,
          UNIQUE KEY uq_grade (assessment_id, student_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS homeworks (
          id INT AUTO_INCREMENT PRIMARY KEY,
          class_id INT NOT NULL,
          title VARCHAR(140) NOT NULL,
          description TEXT NULL,
          due_date DATE NULL,
          created_by INT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_homeworks_class
            FOREIGN KEY (class_id) REFERENCES classes(id)
            ON DELETE CASCADE,
          CONSTRAINT fk_homeworks_creator
            FOREIGN KEY (created_by) REFERENCES users(id)
            ON DELETE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS absences (
          id INT AUTO_INCREMENT PRIMARY KEY,
          class_id INT NOT NULL,
          student_id INT NOT NULL,
          absence_date DATE NOT NULL,
          reason VARCHAR(255) NULL,
          recorded_by INT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_absences_class
            FOREIGN KEY (class_id) REFERENCES classes(id)
            ON DELETE CASCADE,
          CONSTRAINT fk_absences_student
            FOREIGN KEY (student_id) REFERENCES users(id)
            ON DELETE CASCADE,
          CONSTRAINT fk_absences_recorder
            FOREIGN KEY (recorded_by) REFERENCES users(id)
            ON DELETE RESTRICT,
          UNIQUE KEY uq_absence (class_id, student_id, absence_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS blackjack_history (
          id INT AUTO_INCREMENT PRIMARY KEY,
          student_id INT NOT NULL,
          score VARCHAR(10) NOT NULL,
          result VARCHAR(10) NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_bh_student
            FOREIGN KEY (student_id) REFERENCES users(id)
            ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    # App de rencontre (LOVERBOY)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dating_profiles (
          user_id INT PRIMARY KEY,
          display_name VARCHAR(80) NOT NULL,
          bio VARCHAR(800) NULL,
          city VARCHAR(80) NULL,
          interests VARCHAR(200) NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_profiles_user
            FOREIGN KEY (user_id) REFERENCES users(id)
            ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS swipes (
          swiper_user_id INT NOT NULL,
          target_user_id INT NOT NULL,
          action VARCHAR(10) NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (swiper_user_id, target_user_id),
          CONSTRAINT fk_swipes_swiper FOREIGN KEY (swiper_user_id) REFERENCES users(id) ON DELETE CASCADE,
          CONSTRAINT fk_swipes_target FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
          id INT AUTO_INCREMENT PRIMARY KEY,
          user_low INT NOT NULL,
          user_high INT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE KEY uq_match (user_low, user_high),
          CONSTRAINT fk_matches_low FOREIGN KEY (user_low) REFERENCES users(id) ON DELETE CASCADE,
          CONSTRAINT fk_matches_high FOREIGN KEY (user_high) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
          id INT AUTO_INCREMENT PRIMARY KEY,
          match_id INT NOT NULL,
          sender_user_id INT NOT NULL,
          content VARCHAR(1000) NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_messages_match FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
          CONSTRAINT fk_messages_sender FOREIGN KEY (sender_user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )


def upsert_user(cur, username: str, role: str, password_plain: str):
    password_hash = hash_password(password_plain)
    cur.execute(
        """
        INSERT INTO users(username, password_hash, role)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
          password_hash=VALUES(password_hash),
          role=VALUES(role)
        """,
        (username, password_hash, role),
    )
    cur.execute("SELECT id, username, role FROM users WHERE username=%s", (username,))
    return cur.fetchone()["id"]


def seed(cur):
    admin_id = upsert_user(cur, "admin", "ADMIN", "Admin123!")
    prof_id = upsert_user(cur, "prof1", "PROFESSOR", "Prof123!")
    stud_id = upsert_user(cur, "stud1", "STUDENT", "Stud123!")
    stud2_id = upsert_user(cur, "stud2", "STUDENT", "Stud123!")
    loverboy_id = upsert_user(cur, "Loverboy1", "LOVERBOY", "Love123!")

    cur.execute(
        """
        INSERT INTO classes(name, teacher_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE teacher_id=VALUES(teacher_id)
        """,
        ("GCS2-101", prof_id),
    )
    cur.execute("SELECT id FROM classes WHERE name=%s", ("GCS2-101",))
    class_id = cur.fetchone()["id"]

    cur.execute(
        """
        INSERT INTO class_students(class_id, student_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE student_id=student_id
        """,
        (class_id, stud_id),
    )
    cur.execute(
        """
        INSERT INTO class_students(class_id, student_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE student_id=student_id
        """,
        (class_id, stud2_id),
    )

    # Une entrée d’emploi du temps
    cur.execute(
        """
        INSERT INTO schedules(class_id, day_of_week, start_time, end_time, location)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (class_id, 1, "09:00:00", "10:30:00", "Salle A"),
    )

    # Évaluation + note chiffrée
    cur.execute(
        """
        INSERT INTO assessments(class_id, title, due_date, created_by)
        VALUES (%s, %s, %s, %s)
        """,
        (class_id, "Contrôle 1", "2026-04-10", prof_id),
    )
    cur.execute(
        "SELECT id FROM assessments WHERE class_id=%s AND title=%s ORDER BY id DESC LIMIT 1",
        (class_id, "Contrôle 1"),
    )
    assessment_id = cur.fetchone()["id"]

    cur.execute(
        """
        INSERT INTO grades(assessment_id, student_id, grade_encrypted, updated_by)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          grade_encrypted=VALUES(grade_encrypted),
          updated_by=VALUES(updated_by)
        """,
        (assessment_id, stud_id, encrypt_value("14.5"), admin_id),
    )

    # Devoirs (exemples)
    cur.execute(
        """
        INSERT INTO homeworks(class_id, title, description, due_date, created_by)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            class_id,
            "TP Sécurité Web — CSRF & Sessions",
            "Mettre en place la protection CSRF sur tous les formulaires et vérifier la rotation de session au login.",
            "2026-04-03",
            prof_id,
        ),
    )

    # Profils dating seed (LOVERBOY + quelques profils fictifs)
    def execute_profile(uid, name, bio, city, interests):
        cur.execute(
        """
        INSERT INTO dating_profiles(user_id, display_name, bio, city, interests)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE display_name=VALUES(display_name), bio=VALUES(bio), city=VALUES(city), interests=VALUES(interests)
        """,
        (uid, name, bio, city, interests),
        )
    execute_profile(loverboy_id, "Loverboy1", "Ici pour matcher (et shipper du DevSecOps).", "Paris", "cyber, musique, café")
    a_id = upsert_user(cur, "Aline", "LOVERBOY", "Love123!")
    b_id = upsert_user(cur, "Bastien", "LOVERBOY", "Love123!")
    c_id = upsert_user(cur, "Cleo", "LOVERBOY", "Love123!")
    execute_profile(a_id, "Aline", "Team blue team, mais je swipe vite.", "Lyon", "sécu, séries, running")
    execute_profile(b_id, "Bastien", "J'aime les pull requests propres.", "Nantes", "dev, foot, ramen")
    execute_profile(c_id, "Cléo", "CSP enjoyer.", "Lille", "ux, musique, travel")
    cur.execute(
        """
        INSERT INTO homeworks(class_id, title, description, due_date, created_by)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            class_id,
            "Devoir : Revue de code (SAST)",
            "Exécuter flake8 + bandit, corriger les points critiques, et rédiger 5 recommandations.",
            "2026-04-05",
            prof_id,
        ),
    )


def main():
    load_dotenv(override=False)
    if not wait_for_db():
        raise SystemExit(1)

    conn = connect()
    try:
        with conn.cursor() as cur:
            create_schema(cur)
            seed(cur)
    finally:
        conn.close()

    print("[init_db] Schéma et seed OK.")


if __name__ == "__main__":
    main()

