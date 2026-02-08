import sys
from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QGroupBox,
    QComboBox, QScrollArea, QGridLayout, QLayout, QStackedWidget
)
from PyQt6.QtGui import QPixmap, QColor, QFont
from PyQt6.QtCore import Qt
import pymysql

DB_NAME = "shs_enrollment"
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""

def get_connection():
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, charset='utf8mb4', autocommit=False)
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cur.execute(f"USE {DB_NAME}")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(100),
            role VARCHAR(20)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(20),
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            date_of_birth VARCHAR(20),
            gender VARCHAR(20),
            email VARCHAR(100),
            phone VARCHAR(50),
            status VARCHAR(20),
            guardian_name VARCHAR(100),
            guardian_relation VARCHAR(50),
            previous_school VARCHAR(100),
            strand VARCHAR(50),
            semester VARCHAR(20),
            school_year VARCHAR(20),
            submitted_by VARCHAR(100),
            submitted_role VARCHAR(50)
        )
    """)
    conn.commit()
    return conn

def load_students_from_db() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("SELECT * FROM students")
    rows = cur.fetchall()
    conn.close()
    return rows

def save_students_to_db(data: List[Dict[str, Any]]):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students")
    for s in data:
        guardian_name = None
        guardian_relation = None
        previous_school = None
        if s.get("guardian"):
            guardian_name = s["guardian"].get("name") if s["guardian"].get("name") not in (None, "") else None
            guardian_relation = s["guardian"].get("relation") if s["guardian"].get("relation") not in (None, "") else None
        if s.get("academic"):
            previous_school = s["academic"].get("previous_school") if s["academic"].get("previous_school") not in (None, "") else None

        cur.execute("""
            INSERT INTO students (student_id, first_name, last_name, date_of_birth, gender, email, phone, status,
                                  guardian_name, guardian_relation, previous_school, strand, semester, school_year,
                                  submitted_by, submitted_role)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            s.get("student_id"), s.get("first_name"), s.get("last_name"), s.get("date_of_birth"),
            s.get("gender"), s.get("email"), s.get("phone"), s.get("status"),
            guardian_name, guardian_relation,
            previous_school, s.get("academic", {}).get("strand"), s.get("academic", {}).get("semester"), s.get("academic", {}).get("school_year"),
            s.get("submitted_by"), s.get("submitted_role")
        ))
    conn.commit()
    conn.close()

def generate_student_id() -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT student_id FROM students")
    ids = cur.fetchall()
    maxn = 0
    for row in ids:
        sid = row[0] if isinstance(row, (list, tuple)) else row
        if sid and isinstance(sid, str) and sid.startswith("SID-"):
            try:
                n = int(sid.split("-")[1])
                maxn = max(maxn, n)
            except Exception:
                pass
    conn.close()
    return f"SID-{maxn+1:04d}"

def load_students_from_file() -> List[Dict[str, Any]]:
    rows = load_students_from_db()
    out = []
    for r in rows:
        out.append({
            "student_id": r.get("student_id"),
            "first_name": r.get("first_name"),
            "last_name": r.get("last_name"),
            "date_of_birth": r.get("date_of_birth"),
            "gender": r.get("gender"),
            "email": r.get("email"),
            "phone": r.get("phone"),
            "status": r.get("status") or "pending",
            "guardian": {
                "name": r.get("guardian_name") if r.get("guardian_name") is not None else None,
                "relation": r.get("guardian_relation") if r.get("guardian_relation") is not None else None,
                "phone": ""
            },
            "academic": {
                "previous_school": r.get("previous_school") if r.get("previous_school") is not None else None,
                "strand": r.get("strand") or "",
                "semester": r.get("semester") or "",
                "school_year": r.get("school_year") or ""
            },
            "submitted_by": r.get("submitted_by") or "",
            "submitted_role": r.get("submitted_role") or ""
        })
    return out

def save_students_to_file(data: List[Dict[str, Any]]):
    save_students_to_db(data)

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setMinimumSize(380, 320)
        self.user = None
        self.setStyleSheet("background-color: #eef7ff;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        logo_label = QLabel()
        pixmap = QPixmap("logo.png")
        if pixmap.isNull():
            pixmap = QPixmap("img.png")
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(96, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        container = QFrame()
        container.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(6)

        container_layout.addWidget(QLabel("Username"))
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username")
        self.username_edit.setMinimumHeight(28)
        self.username_edit.setStyleSheet("padding:4px; border:1px solid #d0d7de; border-radius:6px;")
        container_layout.addWidget(self.username_edit)

        container_layout.addWidget(QLabel("Password"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")
        self.password_edit.setMinimumHeight(28)
        self.password_edit.setStyleSheet("padding:4px; border:1px solid #d0d7de; border-radius:6px;")
        container_layout.addWidget(self.password_edit)

        login_btn = QPushButton("Login")
        login_btn.setMinimumHeight(32)
        login_btn.setStyleSheet(
            "QPushButton { background-color: #2563eb; color: white; padding: 6px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #1d4ed8; }"
        )
        login_btn.clicked.connect(self.attempt_login)
        container_layout.addWidget(login_btn)

        layout.addWidget(container)

        self._ensure_users_in_db()

        self.username_edit.returnPressed.connect(lambda: self.password_edit.setFocus())
        self.password_edit.returnPressed.connect(login_btn.click)

    def _ensure_users_in_db(self):
        conn = get_connection()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute("SELECT COUNT(*) AS cnt FROM users")
        row = cur.fetchone()
        count = row.get("cnt", 0) if row else 0
        if count == 0:
            cur.execute("INSERT INTO users (username,password,role) VALUES (%s,%s,%s)", ("admin", "admin123", "admin"))
            cur.execute("INSERT INTO users (username,password,role) VALUES (%s,%s,%s)", ("staff", "staff123", "staff"))
            conn.commit()
        conn.close()

    def attempt_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Login failed", "Please enter username and password.")
            return
        conn = get_connection()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            self.user = {"username": user["username"], "role": user["role"]}
            self.accept()
        else:
            QMessageBox.warning(self, "Login failed", "Invalid username or password.")

class RecordDialog(QDialog):
    def __init__(self, student: dict, original_index: int = -1, role: str = "staff", parent=None):
        super().__init__(parent)
        self.student = student or {}
        self.original_index = original_index
        self.role = role
        self.setWindowTitle("Student Record")
        self.setMinimumSize(560, 380)

        self.setStyleSheet("""
            QDialog { background: qlineargradient(x1:0 y1:0, x2:1 y2:1, stop:0 #f6f9ff, stop:1 #eef6ff); }
            QLabel.heading { font-size: 14px; font-weight: 700; color: #07204a; }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(10)

        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("QFrame { border-radius: 8px; background: qlineargradient(x1:0 y1:0, x2:1 y2:0, stop:0 #dbeafe, stop:1 #bfdbfe); }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        header_layout.setSpacing(8)

        initials = (self.student.get("first_name", " ")[0:1] + self.student.get("last_name", " ")[0:1]).upper()
        avatar = QLabel(initials)
        avatar.setFixedSize(56, 56)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("background-color: #e0efff; color: #0b3b7a; border-radius: 28px; font-weight:700; font-size:16px;")
        header_layout.addWidget(avatar)

        name_block = QVBoxLayout()
        name_lbl = QLabel(f"{self.student.get('first_name','')} {self.student.get('last_name','')}")
        name_lbl.setStyleSheet("font-size:14px; font-weight:800; color: #07204a;")
        name_block.addWidget(name_lbl)
        sid = self.student.get("student_id", "") or self.student.get("id", "")
        id_lbl = QLabel(f"Student ID: {sid}")
        id_lbl.setStyleSheet("color:#0b355e; font-size:11px;")
        name_block.addWidget(id_lbl)
        header_layout.addLayout(name_block)
        header_layout.addStretch()

        status = self.student.get("status", "pending")
        badge = QLabel(status.capitalize())
        badge.setStyleSheet("QLabel { padding:4px 6px; border-radius:8px; font-weight:700; font-size:11px; }")
        if status == "approved":
            badge.setStyleSheet(badge.styleSheet() + " QLabel { background-color:#16a34a; color: white; }")
        elif status == "declined":
            badge.setStyleSheet(badge.styleSheet() + " QLabel { background-color:#ef4444; color: white; }")
        else:
            badge.setStyleSheet(badge.styleSheet() + " QLabel { background-color:#f59e0b; color: white; }")
        header_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        main.addWidget(header)

        card = QFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(8)

        info_grid = QGridLayout()
        info_grid.setHorizontalSpacing(12)
        info_grid.setVerticalSpacing(6)

        info_grid.addWidget(QLabel("Date of birth:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(self.student.get("date_of_birth", "")), 0, 1, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel("Gender:"), 1, 0, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(self.student.get("gender", "")), 1, 1, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel("Email:"), 2, 0, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(self.student.get("email", "")), 2, 1, Qt.AlignmentFlag.AlignLeft)

        info_grid.addWidget(QLabel("Phone:"), 0, 2, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(self.student.get("phone", "")), 0, 3, Qt.AlignmentFlag.AlignLeft)
        g = self.student.get("guardian", {}) or {}
        gname = g.get("name") if g.get("name") not in (None, "") else "N/A"
        grel = g.get("relation") if g.get("relation") not in (None, "") else "N/A"
        info_grid.addWidget(QLabel("Guardian:"), 1, 2, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(f"{gname} ({grel})"), 1, 3, Qt.AlignmentFlag.AlignLeft)
        a = self.student.get("academic", {}) or {}
        prev_school = a.get("previous_school") if a.get("previous_school") not in (None, "") else "N/A"
        info_grid.addWidget(QLabel("Previous School:"), 2, 2, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(prev_school), 2, 3, Qt.AlignmentFlag.AlignLeft)

        card_layout.addLayout(info_grid)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        if self.role == "admin":
            self.admin_status = QComboBox()
            self.admin_status.addItems(["pending", "approved", "declined"])
            try:
                self.admin_status.setCurrentText(self.student.get("status", "pending"))
            except Exception:
                pass
            self.admin_status.setFixedWidth(130)
            self.admin_status.setStyleSheet("padding:4px; font-size:11px; border-radius:6px;")
            save_btn = QPushButton("Save")
            save_btn.setStyleSheet("QPushButton { background-color:#0ea5a4; color: white; padding:6px 10px; border-radius:8px; }")
            save_btn.clicked.connect(self._save_and_close)
            btn_row.addWidget(self.admin_status)
            btn_row.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("QPushButton { background-color:#e5e7eb; padding:6px 10px; border-radius:8px; }")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        card_layout.addLayout(btn_row)
        main.addWidget(card)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 16))
        card.setGraphicsEffect(shadow)

    def _save_and_close(self):
        if not hasattr(self, "admin_status"):
            self.accept()
            return
        new_status = self.admin_status.currentText()
        data = load_students_from_file()
        if 0 <= self.original_index < len(data):
            data[self.original_index]["status"] = new_status
            save_students_to_file(data)
            QMessageBox.information(self, "Saved", "Student status updated.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Could not locate student to save.")
            self.reject()

class StudentsTable(QWidget):
    def __init__(self, role="staff", parent=None):
        super().__init__(parent)
        self.role = role
        self.filter_text = ""
        self.filter_status = "All"
        self.current_entries = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setStyleSheet("QFrame { background-color: white; border-radius: 10px; border: 1px solid #e8eef8; padding: 10px; }")
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(8); shadow.setOffset(0, 3); shadow.setColor(QColor(0, 0, 0, 12))
        container.setGraphicsEffect(shadow)

        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(6, 6, 6, 6)
        container_layout.setSpacing(10)

        left_col = QVBoxLayout()
        top_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by name, ID, email or phone...")
        self.search_edit.setStyleSheet("padding:4px; border:1px solid #d0d7de; border-radius:6px;")
        self.search_edit.textChanged.connect(self._on_search_changed)
        top_row.addWidget(QLabel("Search:"))
        top_row.addWidget(self.search_edit, 1)
        left_col.addLayout(top_row)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["All", "pending", "approved", "declined"])
        self.status_filter_combo.setCurrentIndex(0)
        self.status_filter_combo.currentTextChanged.connect(self._on_status_filter_changed)
        self.status_filter_combo.setStyleSheet("padding:4px; border:1px solid #d0d7de; border-radius:6px;")
        filter_row.addWidget(self.status_filter_combo)
        filter_row.addStretch()
        left_col.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setWordWrap(False)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("QTableWidget { border: none; }")
        left_col.addWidget(self.table, 1)

        container_layout.addLayout(left_col, 1)

        self.detail_widget = QFrame()
        self.detail_widget.setStyleSheet("QFrame { background-color: #f8fbff; border-radius: 8px; padding: 10px; } QLabel { font-size: 11px; }")
        self.detail_widget.setMinimumWidth(420)
        detail_v = QVBoxLayout(self.detail_widget)
        detail_v.setContentsMargins(6, 6, 6, 6)
        detail_v.setSpacing(6)

        hdr = QHBoxLayout()
        self.lbl_avatar = QLabel("")
        self.lbl_avatar.setFixedSize(44, 44)
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_avatar.setStyleSheet("background-color: #e6f0ff; color: #1e40af; border-radius: 22px; font-weight:700; font-size:14px;")
        hdr.addWidget(self.lbl_avatar)
        hdr.addStretch()

        if self.role == "admin":
            self.admin_status_combo = QComboBox()
            self.admin_status_combo.addItems(["pending", "approved", "declined"])
            self.admin_status_combo.setFixedWidth(130)
            self.admin_status_combo.setStyleSheet("padding:4px; border-radius:6px; font-size:11px;")
            hdr.addWidget(self.admin_status_combo)
        else:
            self.detail_status_badge = QLabel("")
            self.detail_status_badge.setFixedHeight(24)
            self.detail_status_badge.setStyleSheet("padding:3px 6px; border-radius:8px; font-weight:700; font-size:11px;")
            hdr.addWidget(self.detail_status_badge)

        detail_v.addLayout(hdr)

        self.lbl_name = QLabel("Select a student")
        self.lbl_name.setStyleSheet("font-weight:700; font-size:12px;")
        self.lbl_name.setWordWrap(True)
        detail_v.addWidget(self.lbl_name)

        self.lbl_student_id = QLabel("")
        self.lbl_student_id.setStyleSheet("color:#0b355e; font-size:11px;")
        detail_v.addWidget(self.lbl_student_id)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(6)

        self.grid_labels = {
            'dob': QLabel(""), 'gender': QLabel(""), 'email': QLabel(""),
            'phone': QLabel(""), 'guardian': QLabel(""), 'strand': QLabel(""),
            'semester': QLabel(""), 'school_year': QLabel(""), 'submitted_by': QLabel("")
        }
        for lbl in self.grid_labels.values():
            lbl.setStyleSheet("font-size:11px; color:#0b1726;")

        keys = [
            ("Date of birth:", 'dob'),
            ("Gender:", 'gender'),
            ("Email:", 'email'),
            ("Phone:", 'phone'),
            ("Guardian:", 'guardian'),
            ("Strand:", 'strand'),
            ("Semester:", 'semester'),
            ("School Year:", 'school_year'),
            ("Submitted by:", 'submitted_by')
        ]
        for idx, (ktext, key) in enumerate(keys):
            row = idx // 2
            col_base = (idx % 2) * 2
            lbl_k = QLabel(ktext)
            lbl_k.setStyleSheet("font-size:11px; color:#556675;")
            self.grid.addWidget(lbl_k, row, col_base, Qt.AlignmentFlag.AlignLeft)
            self.grid.addWidget(self.grid_labels[key], row, col_base + 1, Qt.AlignmentFlag.AlignLeft)

        detail_v.addLayout(self.grid)

        action_row = QHBoxLayout()
        action_row.addStretch()
        if self.role == "admin":
            self.save_status_btn = QPushButton("Save Status")
            self.save_status_btn.setStyleSheet("QPushButton { background-color:#10b981; color: white; padding:6px 10px; border-radius:8px; }")
            self.save_status_btn.clicked.connect(self._admin_save_status)
            action_row.addWidget(self.save_status_btn)
        detail_v.addLayout(action_row)

        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setWidget(self.detail_widget)

        container_layout.addWidget(self.detail_scroll, 2)

        outer.addWidget(container)
        self.refresh_table()

    def set_status_filter(self, status: str):
        self.status_filter_combo.setCurrentText(status or "All")

    def _on_status_filter_changed(self, text):
        self.filter_status = text
        self.refresh_table()

    def _on_search_changed(self, text):
        self.filter_text = text.strip()
        self.refresh_table()

    def _matches_filter(self, s: dict):
        if self.filter_status != "All" and s.get("status", "pending") != self.filter_status:
            return False
        if not self.filter_text:
            return True
        q = self.filter_text.lower()
        fullname = (s.get("first_name", "") + " " + s.get("last_name", "")).lower()
        if q in fullname or q in s.get("email", "").lower() or q in s.get("phone", "").lower():
            return True
        if q in (s.get("student_id") or "").lower():
            return True
        g = s.get("guardian", {}) or {}
        if q in (g.get("name") or "").lower():
            return True
        return False

    def refresh_table(self):
        data = load_students_from_file()
        filtered = [s for s in data if self._matches_filter(s)]
        self.current_entries = filtered

        columns = ["Name", "Student ID", "Status"]
        self.table.clear()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(filtered))
        self.table.setColumnWidth(0, 180)

        for r, s in enumerate(filtered):
            original_index = self._find_original_index(s)
            name = f"{s.get('first_name','')} {s.get('last_name','')}"
            student_id = s.get("student_id") or s.get("id") or (f"SID-{original_index+1:04d}" if original_index >= 0 else f"SID-{r+1:04d}")
            item_name = QTableWidgetItem(name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_name.setToolTip(name)
            item_name.setData(Qt.ItemDataRole.UserRole, original_index)
            item_id = QTableWidgetItem(student_id)
            item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_status = QTableWidgetItem(s.get("status", "pending"))
            item_status.setFlags(item_status.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.table.setItem(r, 0, item_name)
            self.table.setItem(r, 1, item_id)
            self.table.setItem(r, 2, item_status)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.resizeRowsToContents()
        header.setSectionsMovable(False)
        header.setStretchLastSection(False)

        self._clear_detail()

    def _find_original_index(self, student_dict):
        data = load_students_from_file()
        for i, s in enumerate(data):
            if (s.get('first_name') == student_dict.get('first_name') and
                s.get('last_name') == student_dict.get('last_name') and
                s.get('email') == student_dict.get('email') and
                s.get('phone') == student_dict.get('phone') and
                s.get('date_of_birth') == student_dict.get('date_of_birth')):
                return i
        for i, s in enumerate(data):
            if s.get('email') == student_dict.get('email'):
                return i
        return -1

    def _on_selection_changed(self):
        sel = self.table.selectedIndexes()
        if not sel:
            self._clear_detail()
            return
        row = sel[0].row()
        if 0 <= row < len(self.current_entries):
            student = self.current_entries[row]
            orig_index = self._find_original_index(student)
            self._populate_detail(student, orig_index)
        else:
            self._clear_detail()

    def _populate_detail(self, s: dict, orig_index: int):
        initials = (s.get("first_name", " ")[0:1] + s.get("last_name", " ")[0:1]).upper()
        self.lbl_avatar.setText(initials)
        name = f"{s.get('first_name','')} {s.get('last_name','')}"
        self.lbl_name.setText(name)
        student_id = s.get("student_id") or s.get("id") or (f"SID-{orig_index+1:04d}" if orig_index >= 0 else "")
        self.lbl_student_id.setText(f"ID: {student_id}")

        self.grid_labels['dob'].setText(s.get("date_of_birth", "") or "N/A")
        self.grid_labels['gender'].setText(s.get("gender", "") or "N/A")
        self.grid_labels['email'].setText(s.get("email", "") or "N/A")
        self.grid_labels['phone'].setText(s.get("phone", "") or "N/A")
        g = s.get("guardian", {}) or {}
        gname = g.get("name") if g.get("name") not in (None, "") else "N/A"
        grel = g.get("relation") if g.get("relation") not in (None, "") else "N/A"
        self.grid_labels['guardian'].setText(f"{gname} ({grel})")
        a = s.get("academic", {}) or {}
        self.grid_labels['strand'].setText(a.get("strand", "") or "N/A")
        self.grid_labels['semester'].setText(a.get("semester", "") or "N/A")
        self.grid_labels['school_year'].setText(a.get("school_year", "") or "N/A")
        submitted = f"{s.get('submitted_by','')} ({s.get('submitted_role','')})" if s.get('submitted_by') else "N/A"
        self.grid_labels['submitted_by'].setText(submitted)

        status_text = s.get("status", "pending").capitalize()

        if self.role == "admin":
            try:
                self.admin_status_combo.setCurrentText(s.get("status", "pending"))
            except Exception:
                pass
        else:
            st = s.get("status", "pending")
            if st == "approved":
                self.detail_status_badge.setStyleSheet("padding:3px 6px; border-radius:8px; font-weight:700; font-size:11px; background-color:#16a34a; color:white;")
            elif st == "declined":
                self.detail_status_badge.setStyleSheet("padding:3px 6px; border-radius:8px; font-weight:700; font-size:11px; background-color:#ef4444; color:white;")
            else:
                self.detail_status_badge.setStyleSheet("padding:3px 6px; border-radius:8px; font-weight:700; font-size:11px; background-color:#f59e0b; color:white;")
            self.detail_status_badge.setText(status_text)

    def _clear_detail(self):
        self.lbl_avatar.setText("")
        self.lbl_name.setText("Select a student")
        self.lbl_student_id.setText("")
        for k in self.grid_labels:
            try:
                self.grid_labels[k].setText("")
            except Exception:
                pass
        if self.role == "admin":
            try:
                self.admin_status_combo.setCurrentIndex(0)
            except Exception:
                pass
        else:
            try:
                self.detail_status_badge.setText("")
                self.detail_status_badge.setStyleSheet("padding:3px 6px; border-radius:8px; font-weight:700; font-size:11px;")
            except Exception:
                pass

    def _open_selected_record(self):
        sel = self.table.selectedIndexes()
        if not sel:
            return
        row = sel[0].row()
        if 0 <= row < len(self.current_entries):
            s = self.current_entries[row]
            orig_index = self._find_original_index(s)
            dlg = RecordDialog(s, original_index=orig_index, role=self.role, parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.refresh_table()

    def _admin_save_status(self):
        sel = self.table.selectedIndexes()
        if not sel:
            QMessageBox.warning(self, "No selection", "Please select a student.")
            return
        row = sel[0].row()
        if 0 <= row < len(self.current_entries):
            s = self.current_entries[row]
            new_status = self.admin_status_combo.currentText()
            data = load_students_from_file()
            orig_index = self._find_original_index(s)
            if 0 <= orig_index < len(data):
                data[orig_index]["status"] = new_status
                save_students_to_file(data)
                QMessageBox.information(self, "Saved", "Student status updated.")
                self.refresh_table()
            else:
                QMessageBox.warning(self, "Error", "Could not locate student to save.")

class DashboardWidget(QWidget):
    def __init__(self, role="staff", parent=None):
        super().__init__(parent)
        self.role = role
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        self.top_frame = QFrame()
        self.top_grid = QGridLayout(self.top_frame)
        self.top_grid.setContentsMargins(0, 0, 0, 0)
        self.top_grid.setHorizontalSpacing(6)
        self.top_grid.setVerticalSpacing(6)
        main_layout.addWidget(self.top_frame)

        self.metrics_frame = QFrame()
        self.metrics_grid = QGridLayout(self.metrics_frame)
        self.metrics_grid.setContentsMargins(0, 0, 0, 0)
        self.metrics_grid.setHorizontalSpacing(6)
        self.metrics_grid.setVerticalSpacing(6)
        main_layout.addWidget(self.metrics_frame)

        self.last_updated = QLabel()
        self.last_updated.setStyleSheet("color:#5b6b7a; font-weight:800;")
        main_layout.addWidget(self.last_updated, alignment=Qt.AlignmentFlag.AlignLeft)

        self.status_colors = ["#2563eb", "#f59e0b", "#16a34a", "#ef4444"]
        self.status_labels = ["Total", "Pending", "Approved", "Declined"]

        self._chip_widgets = []
        self._metric_cards = []

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        self.refresh()

    def _clear_layout_and_delete(self, layout: QLayout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if not item:
                continue
            w = item.widget()
            if w is not None:
                try:
                    w.deleteLater()
                except Exception:
                    pass
            else:
                sub = item.layout()
                if sub is not None:
                    self._clear_layout_and_delete(sub)

    def _make_chip(self, title: str, subtitle: str = "", accent="#2563eb", max_width=None, title_font_size=9, subtitle_font_size=8):
        card = QFrame()
        card.setStyleSheet("QFrame { background: #ffffff; border-radius: 6px; border: 1px solid rgba(15, 23, 42, 0.04); }")
        if max_width:
            card.setMaximumWidth(max_width)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(6)

        accent_bar = QFrame()
        accent_bar.setFixedWidth(4)
        accent_bar.setStyleSheet(f"QFrame {{ background: {accent}; border-radius: 2px; }}")
        lay.addWidget(accent_bar)

        text_block = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight:800; color:#0b1726;")
        title_lbl.setFont(QFont("", title_font_size, QFont.Weight.Bold))
        text_block.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet("color:#566674;")
            sub_lbl.setFont(QFont("", subtitle_font_size))
            text_block.addWidget(sub_lbl)
        else:
            text_block.addSpacing(2)

        lay.addLayout(text_block)
        lay.addStretch()

        sh = QGraphicsDropShadowEffect(card)
        sh.setBlurRadius(6)
        sh.setOffset(0, 2)
        sh.setColor(QColor(6, 20, 70, 12))
        card.setGraphicsEffect(sh)
        return card

    def _make_metric_card(self, number: int, label: str, color: str, max_width=None, num_font_size=16, label_font_size=9):
        card = QFrame()
        card.setStyleSheet("QFrame { background: #ffffff; border-radius: 6px; border: 1px solid rgba(10,20,40,0.04); }")
        if max_width:
            card.setMaximumWidth(max_width)
        v = QVBoxLayout(card)
        v.setContentsMargins(8, 4, 8, 4)
        v.setSpacing(4)

        num = QLabel(str(number))
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num.setStyleSheet(f"color:{color}; font-weight:900;")
        num.setFont(QFont("", num_font_size, QFont.Weight.Bold))
        v.addWidget(num)

        txt = QLabel(label)
        txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        txt.setStyleSheet("color:#0b1726; font-weight:800;")
        txt.setFont(QFont("", label_font_size))
        v.addWidget(txt)

        sh = QGraphicsDropShadowEffect(card)
        sh.setBlurRadius(8)
        sh.setOffset(0, 3)
        sh.setColor(QColor(6, 20, 70, 10))
        card.setGraphicsEffect(sh)
        return card

    def refresh(self):
        try:
            data = load_students_from_file()
        except Exception:
            data = []

        total = len(data)
        pending = sum(1 for s in data if s.get("status", "pending") == "pending")
        approved = sum(1 for s in data if s.get("status", "") == "approved")
        declined = sum(1 for s in data if s.get("status", "") == "declined")
        counts = [total, pending, approved, declined]

        strand_counts = {}
        for s in data:
            a = s.get("academic", {}) or {}
            st = a.get("strand", "") or "Unspecified"
            strand_counts[st] = strand_counts.get(st, 0) + 1
        rows = list(strand_counts.items())
        rows.sort(key=lambda x: x[1], reverse=True)

        self._clear_layout_and_delete(self.top_grid)
        self._clear_layout_and_delete(self.metrics_grid)
        self._chip_widgets = []
        self._metric_cards = []

        w = max(900, self.width() or 900)
        per_col = max(140, (w - 36) // 3)

        for i, (strand, cnt) in enumerate(rows):
            subtitle = f"{cnt} student{'s' if cnt != 1 else ''}"
            accents = ["#2563eb", "#7c3aed", "#06b6d4", "#f97316", "#10b981", "#ef4444"]
            accent = accents[i % len(accents)]
            chip = self._make_chip(strand, subtitle, accent=accent, max_width=per_col, title_font_size=9, subtitle_font_size=8)
            self._chip_widgets.append(chip)
            r = i // 3
            c = i % 3
            self.top_grid.addWidget(chip, r, c)

        if not rows:
            hint = self._make_chip("No strands yet", "Submit students to populate strands", accent="#94a3b8", max_width=per_col, title_font_size=9, subtitle_font_size=8)
            self._chip_widgets.append(hint)
            self.top_grid.addWidget(hint, 0, 0)

        for i, (label, color, val) in enumerate(zip(self.status_labels, self.status_colors, counts)):
            card = self._make_metric_card(val, label, color, max_width=per_col, num_font_size=16, label_font_size=9)
            self._metric_cards.append(card)
            r = i // 3
            c = i % 3
            self.metrics_grid.addWidget(card, r, c)

        self.last_updated.setText(f"Last updated: {total} submissions • Pending {pending}, Approved {approved}, Declined {declined}")

class StudentForm(QWidget):
    def __init__(self, submit_callback=None, parent=None):
        super().__init__(parent)
        self.submit_callback = submit_callback
        outer = QVBoxLayout(self)
        outer.setSpacing(8)
        outer.setContentsMargins(0, 0, 0, 0)

        gb_style = ("QGroupBox { background-color: #ffffff; border: 1px solid #dcdcdc; "
                    "border-radius: 6px; padding: 6px; } QGroupBox::title { left: 6px; }")

        self.gb_personal = QGroupBox("Personal Information"); self.gb_personal.setStyleSheet(gb_style)
        p_layout = QVBoxLayout()
        row1 = QHBoxLayout()
        self.first_name = QLineEdit(); self.first_name.setPlaceholderText("First name")
        self.middle_name = QLineEdit(); self.middle_name.setPlaceholderText("Middle name")
        self.last_name = QLineEdit(); self.last_name.setPlaceholderText("Last name")
        for w in (self.first_name, self.middle_name, self.last_name):
            w.setStyleSheet("background-color: white; padding:4px; border:1px solid #ccc; border-radius:6px;")
        row1.addWidget(self.first_name); row1.addWidget(self.middle_name); row1.addWidget(self.last_name)

        row2 = QHBoxLayout()
        self.dob = QLineEdit(); self.dob.setPlaceholderText("Date of birth")
        self.dob.setStyleSheet("background-color: white; padding:4px; border:1px solid #ccc; border-radius:6px;")
        self.gender = QComboBox()
        self.gender.addItem("Select Gender"); self.gender.addItem("Male"); self.gender.addItem("Female"); self.gender.setCurrentIndex(0)
        self.gender.setStyleSheet("background-color: white; padding:4px; border:1px solid #ccc; border-radius:6px;")
        row2.addWidget(self.dob, 1); row2.addWidget(self.gender, 1)

        p_layout.addLayout(row1); p_layout.addLayout(row2)
        self.gb_personal.setLayout(p_layout); outer.addWidget(self.gb_personal)

        self.gb_contact = QGroupBox("Contact Information"); self.gb_contact.setStyleSheet(gb_style)
        c_layout = QHBoxLayout()
        self.email = QLineEdit(); self.email.setPlaceholderText("Email Address")
        self.phone = QLineEdit(); self.phone.setPlaceholderText("Phone Number")
        for w in (self.email, self.phone):
            w.setStyleSheet("background-color: white; padding:4px; border:1px solid #ccc; border-radius:6px;")
        c_layout.addWidget(self.email); c_layout.addWidget(self.phone)
        self.gb_contact.setLayout(c_layout); outer.addWidget(self.gb_contact)

        self.gb_guardian = QGroupBox("Guardian Information (optional)"); self.gb_guardian.setStyleSheet(gb_style)
        g_layout = QHBoxLayout()
        self.guardian_name = QLineEdit(); self.guardian_name.setPlaceholderText("Guardian Name (optional)")
        self.guardian_phone = QLineEdit(); self.guardian_phone.setPlaceholderText("Guardian Phone Number (optional)")
        self.guardian_relation = QComboBox()
        self.guardian_relation.addItem("Select Relation"); self.guardian_relation.addItems(["Father", "Mother", "Legal Guardian", "Others"])
        self.guardian_relation.setCurrentIndex(0)
        for w in (self.guardian_name, self.guardian_phone, self.guardian_relation):
            try:
                w.setStyleSheet("background-color: white; padding:4px; border:1px solid #ccc; border-radius:6px;")
            except Exception:
                pass
        g_layout.addWidget(self.guardian_name, 1); g_layout.addWidget(self.guardian_phone, 1); g_layout.addWidget(self.guardian_relation, 1)
        self.gb_guardian.setLayout(g_layout); outer.addWidget(self.gb_guardian)

        self.gb_academic = QGroupBox("Academic Information"); self.gb_academic.setStyleSheet(gb_style)
        ac_layout = QHBoxLayout()
        self.prev_school = QLineEdit(); self.prev_school.setPlaceholderText("Previous School (optional)")
        self.prev_school.setStyleSheet("background-color: white; padding:4px; border:1px solid #ccc; border-radius:6px;")
        self.strand = QComboBox(); self.strand.addItem("Select Strand")
        self.strand.addItems(["STEM", "ABM", "GAS", "HUMSS", "TVL", "Arts and Design Track"]); self.strand.setCurrentIndex(0)
        self.semester = QComboBox(); self.semester.addItem("Select Semester"); self.semester.addItems(["1st Semester", "2nd Semester"]); self.semester.setCurrentIndex(0)
        self.school_year = QComboBox(); self.school_year.addItem("Select School Year"); self.school_year.addItems(["2025 - 2026", "2026 - 2027"]); self.school_year.setCurrentIndex(0)
        for w in (self.strand, self.semester, self.school_year):
            w.setStyleSheet("background-color: white; padding:4px; border:1px solid #ccc; border-radius:6px;")
        ac_layout.addWidget(self.prev_school, 1); ac_layout.addWidget(self.strand, 1); ac_layout.addWidget(self.semester, 1); ac_layout.addWidget(self.school_year, 1)
        self.gb_academic.setLayout(ac_layout); outer.addWidget(self.gb_academic)

        btn_row = QHBoxLayout()
        self.submit_btn = QPushButton("Submit Form (adds as pending)")
        self.submit_btn.setStyleSheet("QPushButton { background-color: #2563eb; color: white; padding: 6px 10px; border-radius: 8px; } QPushButton:hover { background-color: #1d4ed8; }")
        self.submit_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(self.submit_btn, 0, Qt.AlignmentFlag.AlignLeft)
        btn_row.addStretch(); outer.addLayout(btn_row)

    def _on_submit(self):
        fn = self.first_name.text().strip(); ln = self.last_name.text().strip(); dob = self.dob.text().strip()
        email = self.email.text().strip(); phone = self.phone.text().strip()
        gn = self.guardian_name.text().strip(); gp = self.guardian_phone.text().strip()
        prev = self.prev_school.text().strip()
        if not (fn and ln and dob and email and phone):
            QMessageBox.warning(self, "Form incomplete", "Please fill in required fields (name, date of birth, email, phone).")
            return
        if self.gender.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "Please select gender."); return
        if self.strand.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "Please select strand."); return
        if self.semester.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "Please select semester."); return
        if self.school_year.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "Please select school year."); return

        guardian_obj = {
            "name": gn if gn else None,
            "phone": gp if gp else None,
            "relation": self.guardian_relation.currentText() if (self.guardian_relation.currentIndex() != 0) else None
        }
        academic_obj = {
            "previous_school": prev if prev else None,
            "strand": self.strand.currentText(),
            "semester": self.semester.currentText(),
            "school_year": self.school_year.currentText()
        }

        student = {
            "first_name": fn,
            "last_name": ln,
            "date_of_birth": dob,
            "gender": self.gender.currentText(),
            "email": email,
            "phone": phone,
            "guardian": guardian_obj,
            "academic": academic_obj,
            "status": "pending"
        }

        if callable(self.submit_callback):
            self.submit_callback(student)

        QMessageBox.information(self, "Submitted", "Student added with status 'pending'.")
        self._clear()

    def _clear(self):
        for w in (self.first_name, self.middle_name, self.last_name, self.dob, self.email, self.phone, self.guardian_name, self.guardian_phone, self.prev_school):
            try:
                w.clear()
            except Exception:
                pass
        for cb in (self.gender, self.guardian_relation, self.strand, self.semester, self.school_year):
            try:
                cb.setCurrentIndex(0)
            except Exception:
                pass

class MainWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user or {"username": "unknown", "role": "staff"}
        self.setWindowTitle(f"SHS Enrollment System - {self.user.get('role','').capitalize()}")
        self.setStyleSheet("QWidget#mainWindow { background-color: #f3f7ff; }")

        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(12, 12, 12, 12); main_layout.setSpacing(10)

        top_container = QFrame()
        top_container.setStyleSheet("""QFrame { background: qlineargradient(x1:0 y1:0, x2:1 y2:0, stop:0 #e6f0ff, stop:1 #dbeafe); border-radius: 10px; }""")
        top_container.setFixedHeight(72)
        top_shadow = QGraphicsDropShadowEffect(self); top_shadow.setBlurRadius(14); top_shadow.setOffset(0, 3); top_shadow.setColor(QColor(13, 42, 148, 22))
        top_container.setGraphicsEffect(top_shadow)
        top_layout = QHBoxLayout(top_container); top_layout.setContentsMargins(8, 8, 8, 8)

        logo = QLabel()
        pix = QPixmap("logo.png")
        if pix.isNull():
            pix = QPixmap("img.png")
        if not pix.isNull():
            logo.setPixmap(pix.scaled(52, 52, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        top_layout.addWidget(logo)

        title = QLabel("SHS Enrollment System")
        title.setStyleSheet("color: #06205f; font-weight:900; font-size:18px; padding-left:8px;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        user_badge = QLabel(self.user.get("role", "").capitalize())
        user_badge.setStyleSheet("color:#08306b; padding:6px 8px; background: rgba(255,255,255,0.32); border-radius:6px; font-size:12px;")
        top_layout.addWidget(user_badge)

        logout = QPushButton("Logout")
        logout.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                padding:6px 8px;
                border-radius:6px;
                border: 1px solid rgba(15, 46, 100, 0.06);
                font-size:12px;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        logout.clicked.connect(self.logout)
        top_layout.addWidget(logout)

        main_layout.addWidget(top_container)

        foreground = QFrame()
        foreground.setStyleSheet("QFrame { background-color: white; border-radius: 10px; padding: 12px; border:1px solid #e6eef9; }")
        fg_shadow = QGraphicsDropShadowEffect(self); fg_shadow.setBlurRadius(12); fg_shadow.setOffset(0, 4); fg_shadow.setColor(QColor(0, 0, 0, 16))
        foreground.setGraphicsEffect(fg_shadow)
        fg_layout = QVBoxLayout(foreground); fg_layout.setContentsMargins(6, 6, 6, 6); fg_layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_label = QLabel("Staff Portal" if self.user.get("role") == "staff" else "Manage Students")
        header_label.setStyleSheet("font-weight:600; font-size:13px;")
        header_row.addWidget(header_label); header_row.addStretch()

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_submit_page = QPushButton("Submit Student")
        self.btn_view_page = QPushButton("View Students")
        for b in (self.btn_dashboard, self.btn_submit_page, self.btn_view_page):
            b.setStyleSheet("QPushButton { background-color: white; border: 1px solid #d6dbe7; border-radius:6px; padding:5px 8px; font-size:12px; } QPushButton:hover { background-color:#f7fafc; }")
            b.setFixedHeight(28)

        header_row.addWidget(self.btn_dashboard)
        if self.user.get("role") == "staff":
            header_row.addWidget(self.btn_submit_page)
        header_row.addWidget(self.btn_view_page)
        fg_layout.addLayout(header_row)

        self.stack = QStackedWidget()
        fg_layout.addWidget(self.stack)

        self.dashboard = DashboardWidget(role=self.user.get("role"))
        self.dashboard_scroll = QScrollArea()
        self.dashboard_scroll.setWidgetResizable(True)
        self.dashboard_scroll.setWidget(self.dashboard)

        self.form_page = StudentForm(submit_callback=self._staff_submit)
        self.table_page = StudentsTable(role=self.user.get("role"))

        self.stack.addWidget(self.dashboard_scroll)
        self.stack.addWidget(self.form_page)
        self.stack.addWidget(self.table_page)

        self.btn_dashboard.clicked.connect(lambda: self._show_page(self.dashboard_scroll))
        if self.user.get("role") == "staff":
            self.btn_submit_page.clicked.connect(lambda: self._show_page(self.form_page))
        self.btn_view_page.clicked.connect(lambda: self._show_page(self.table_page))

        self._show_page(self.dashboard_scroll)

        main_layout.addWidget(foreground)
        self.setLayout(main_layout)

    def _show_page(self, widget: QWidget):
        try:
            if widget is self.dashboard_scroll:
                self.dashboard.refresh()
            elif widget is self.table_page:
                self.table_page.refresh_table()
        except Exception:
            pass
        self.stack.setCurrentWidget(widget)

    def _staff_submit(self, student):
        student["submitted_by"] = self.user.get("username")
        student["submitted_role"] = self.user.get("role")
        data = load_students_from_file()
        student["student_id"] = generate_student_id()
        data.append(student)
        save_students_to_file(data)
        try:
            self.table_page.refresh_table()
        except Exception:
            pass
        try:
            self.dashboard.refresh()
        except Exception:
            pass

    def logout(self):
        self.close()

def run_app():
    app = QApplication(sys.argv)
    while True:
        login = LoginDialog()
        if login.exec() == QDialog.DialogCode.Accepted and login.user:
            w = MainWindow(login.user)
            w.setWindowTitle(f"SHS Enrollment System - {login.user.get('username')}")
            w.showMaximized()
            app.exec()
            continue
        else:
            break

if __name__ == '__main__':
    run_app()
