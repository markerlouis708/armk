# SHS Enrollment System (PyQt6)
# Adjustments:
# - Restored the original grouped StudentForm (no layout redesign).
# - If form is incomplete it shows a single QMessageBox with text: "please fill in all requirements"
# - Removed "Sample accounts" label from login dialog.
# - Logout button is now red.
# - Top user badge shows only the role (admin or staff), not "username (role)".
# - Removed the left compact status text in the right detail pane; status is only shown on the right (badge or admin combo).

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QGroupBox,
    QComboBox, QFormLayout, QTextEdit, QScrollArea, QGridLayout
)
from PyQt6.QtGui import QPixmap, QColor, QFont
from PyQt6.QtCore import Qt
import sys, os, json

USERS_FILE = "users.json"
STUDENTS_FILE = "students.json"


def load_students_from_file():
    if os.path.exists(STUDENTS_FILE):
        try:
            with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def save_students_to_file(data):
    with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def generate_student_id(data):
    maxn = 0
    for s in data:
        sid = s.get("student_id") or s.get("id") or ""
        if isinstance(sid, str) and sid.startswith("SID-"):
            try:
                n = int(sid.split("-")[1])
                if n > maxn:
                    maxn = n
            except Exception:
                pass
    return f"SID-{maxn + 1:04d}"


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setMinimumSize(420, 360)
        self.user = None
        self.setStyleSheet("background-color: #eef7ff;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        logo_label = QLabel()
        pixmap = QPixmap("logo.png")
        if pixmap.isNull():
            pixmap = QPixmap("img.png")
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(120, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        container = QFrame()
        container.setStyleSheet("QFrame { background-color: white; border-radius: 10px; }")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(14, 14, 14, 14)
        container_layout.setSpacing(8)

        container_layout.addWidget(QLabel("Username"))
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username")
        self.username_edit.setMinimumHeight(32)
        self.username_edit.setStyleSheet("padding:6px; border:1px solid #d0d7de; border-radius:6px;")
        container_layout.addWidget(self.username_edit)

        container_layout.addWidget(QLabel("Password"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")
        self.password_edit.setMinimumHeight(32)
        self.password_edit.setStyleSheet("padding:6px; border:1px solid #d0d7de; border-radius:6px;")
        container_layout.addWidget(self.password_edit)

        login_btn = QPushButton("Login")
        login_btn.setMinimumHeight(36)
        login_btn.setStyleSheet(
            "QPushButton { background-color: #2563eb; color: white; padding: 8px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #1d4ed8; }"
        )
        login_btn.clicked.connect(self.attempt_login)
        container_layout.addWidget(login_btn)

        layout.addWidget(container)

        # sample accounts label removed

        self._ensure_users_file()
        self.username_edit.returnPressed.connect(lambda: self.password_edit.setFocus())
        self.password_edit.returnPressed.connect(login_btn.click)

    def _ensure_users_file(self):
        if not os.path.exists(USERS_FILE):
            default_users = [
                {"username": "admin", "password": "admin123", "role": "admin"},
                {"username": "staff", "password": "staff123", "role": "staff"}
            ]
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(default_users, f, indent=4)

    def attempt_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Login failed", "Please enter username and password.")
            return
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
        except Exception:
            users = []
        for u in users:
            if u.get("username") == username and u.get("password") == password:
                self.user = {"username": u.get("username"), "role": u.get("role", "staff")}
                self.accept()
                return
        QMessageBox.warning(self, "Login failed", "Invalid username or password.")


class RecordDialog(QDialog):
    def __init__(self, student: dict, original_index: int = -1, role: str = "staff", parent=None):
        super().__init__(parent)
        self.student = student or {}
        self.original_index = original_index
        self.role = role
        self.setWindowTitle("Student Record")
        self.setMinimumSize(640, 420)

        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0 y1:0, x2:1 y2:1,
                                            stop:0 #f6f9ff, stop:1 #eef6ff);
            }
            QLabel.heading { font-size: 16px; font-weight: 700; color: #07204a; }
            QLabel.sub { color: #44556a; }
            QFrame.record-card { background: white; border-radius: 12px; }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(12)

        header = QFrame()
        header.setFixedHeight(96)
        header.setStyleSheet("""
            QFrame { 
                border-radius: 10px;
                background: qlineargradient(x1:0 y1:0, x2:1 y2:0,
                                           stop:0 #dbeafe, stop:1 #bfdbfe);
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        initials = (self.student.get("first_name", " ")[0:1] + self.student.get("last_name", " ")[0:1]).upper()
        avatar = QLabel(initials)
        avatar.setFixedSize(72, 72)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("background-color: #e0efff; color: #0b3b7a; border-radius: 36px; font-weight:800; font-size:20px;")
        header_layout.addWidget(avatar)

        name_block = QVBoxLayout()
        name_lbl = QLabel(f"{self.student.get('first_name','')} {self.student.get('last_name','')}")
        name_lbl.setStyleSheet("font-size:16px; font-weight:800; color: #07204a;")
        name_block.addWidget(name_lbl)
        sid = self.student.get("student_id", "") or self.student.get("id", "")
        id_lbl = QLabel(f"Student ID: {sid}")
        id_lbl.setStyleSheet("color:#0b355e;")
        name_block.addWidget(id_lbl)
        header_layout.addLayout(name_block)
        header_layout.addStretch()

        # keep only the colored badge on the right (remove any left status)
        status = self.student.get("status", "pending")
        badge = QLabel(status.capitalize())
        badge.setProperty("class", "badge")
        badge.setStyleSheet("QLabel { padding:6px 8px; border-radius:10px; font-weight:700; font-size:12px; }")
        if status == "approved":
            badge.setStyleSheet(badge.styleSheet() + " QLabel { background-color:#16a34a; color: white; }")
        elif status == "declined":
            badge.setStyleSheet(badge.styleSheet() + " QLabel { background-color:#ef4444; color: white; }")
        else:
            badge.setStyleSheet(badge.styleSheet() + " QLabel { background-color:#f59e0b; color: white; }")
        header_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        main.addWidget(header)

        card = QFrame()
        card.setObjectName("record_card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(12)

        info_grid = QGridLayout()
        info_grid.setHorizontalSpacing(16)
        info_grid.setVerticalSpacing(8)

        info_grid.addWidget(QLabel("Date of birth:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(self.student.get("date_of_birth", "")), 0, 1, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel("Gender:"), 1, 0, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(self.student.get("gender", "")), 1, 1, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel("Email:"), 2, 0, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(self.student.get("email", "")), 2, 1, Qt.AlignmentFlag.AlignLeft)

        info_grid.addWidget(QLabel("Phone:"), 0, 2, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(self.student.get("phone", "")), 0, 3, Qt.AlignmentFlag.AlignLeft)
        g = self.student.get("guardian", {})
        info_grid.addWidget(QLabel("Guardian:"), 1, 2, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(f"{g.get('name','')} ({g.get('relation','')})"), 1, 3, Qt.AlignmentFlag.AlignLeft)
        a = self.student.get("academic", {})
        info_grid.addWidget(QLabel("Previous School:"), 2, 2, Qt.AlignmentFlag.AlignLeft)
        info_grid.addWidget(QLabel(a.get("previous_school", "")), 2, 3, Qt.AlignmentFlag.AlignLeft)

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
            self.admin_status.setFixedWidth(140)
            self.admin_status.setStyleSheet("padding:4px; font-size:12px; border-radius:6px;")
            save_btn = QPushButton("Save")
            save_btn.setStyleSheet("QPushButton { background-color:#0ea5a4; color: white; padding:8px 12px; border-radius:8px; }")
            save_btn.clicked.connect(self._save_and_close)
            btn_row.addWidget(self.admin_status)
            btn_row.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("QPushButton { background-color:#e5e7eb; padding:8px 12px; border-radius:8px; }")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        card_layout.addLayout(btn_row)

        main.addWidget(card)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 20))
        card.setGraphicsEffect(shadow)

        self._center_to_parent()

    def _center_to_parent(self):
        parent = self.parent()
        if parent and parent.isVisible():
            pw = parent.frameGeometry().width()
            ph = parent.frameGeometry().height()
            px = parent.frameGeometry().x()
            py = parent.frameGeometry().y()
            max_w = max(300, int(pw * 0.95))
            max_h = max(300, int(ph * 0.95))
            new_w = min(self.width(), max_w)
            new_h = min(self.height(), max_h)
            self.resize(new_w, new_h)
            x = px + (pw - self.width()) // 2
            y = py + (ph - self.height()) // 2
            self.move(max(0, x), max(0, y))
        else:
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    sg = screen.availableGeometry()
                    max_w = int(sg.width() * 0.9)
                    max_h = int(sg.height() * 0.9)
                    new_w = min(self.width(), max_w)
                    new_h = min(self.height(), max_h)
                    self.resize(new_w, new_h)
                    x = sg.x() + (sg.width() - self.width()) // 2
                    y = sg.y() + (sg.height() - self.height()) // 2
                    self.move(max(0, x), max(0, y))

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
        container.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: 1px solid #e8eef8; padding: 12px; }")
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(10); shadow.setOffset(0, 3); shadow.setColor(QColor(0, 0, 0, 20))
        container.setGraphicsEffect(shadow)

        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(12)

        # Left (table area)
        left_col = QVBoxLayout()
        top_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by name, student ID, email or phone...")
        self.search_edit.setStyleSheet("padding:6px; border:1px solid #d0d7de; border-radius:6px;")
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
        self.status_filter_combo.setStyleSheet("padding:6px; border:1px solid #d0d7de; border-radius:6px;")
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

        container_layout.addLayout(left_col, 1)  # give table less weight

        # Right (detail pane) wrapped in a scroll area and arranged as grid for compactness
        self.detail_widget = QFrame()
        self.detail_widget.setStyleSheet("QFrame { background-color: #f8fbff; border-radius: 10px; padding: 12px; } QLabel { font-size: 12px; }")
        self.detail_widget.setMinimumWidth(520)  # suited for 1366 width
        detail_v = QVBoxLayout(self.detail_widget)
        detail_v.setContentsMargins(8, 8, 8, 8)
        detail_v.setSpacing(8)

        # header: avatar on left; only right side shows status (badge or admin combo)
        hdr = QHBoxLayout()
        self.lbl_avatar = QLabel("")
        self.lbl_avatar.setFixedSize(56, 56)
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_avatar.setStyleSheet("background-color: #e6f0ff; color: #1e40af; border-radius: 28px; font-weight:700; font-size:16px;")
        hdr.addWidget(self.lbl_avatar)
        hdr.addStretch()

        if self.role == "admin":
            self.admin_status_combo = QComboBox()
            self.admin_status_combo.addItems(["pending", "approved", "declined"])
            self.admin_status_combo.setFixedWidth(150)
            self.admin_status_combo.setStyleSheet("padding:4px; border-radius:6px; font-size:12px;")
            hdr.addWidget(self.admin_status_combo)
        else:
            self.detail_status_badge = QLabel("")
            self.detail_status_badge.setFixedHeight(26)
            self.detail_status_badge.setStyleSheet("padding:4px 8px; border-radius:10px; font-weight:700; font-size:11px;")
            hdr.addWidget(self.detail_status_badge)

        detail_v.addLayout(hdr)

        # name + id
        self.lbl_name = QLabel("Select a student")
        self.lbl_name.setStyleSheet("font-weight:700; font-size:13px;")
        self.lbl_name.setWordWrap(True)
        detail_v.addWidget(self.lbl_name)

        self.lbl_student_id = QLabel("")
        self.lbl_student_id.setStyleSheet("color:#0b355e; font-size:12px;")
        detail_v.addWidget(self.lbl_student_id)

        # compact grid for details (two columns of key/value pairs)
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(8)

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
            self.grid.addWidget(QLabel(ktext), row, col_base, Qt.AlignmentFlag.AlignLeft)
            self.grid.addWidget(self.grid_labels[key], row, col_base + 1, Qt.AlignmentFlag.AlignLeft)

        detail_v.addLayout(self.grid)

        # action row
        action_row = QHBoxLayout()
        action_row.addStretch()
        if self.role == "admin":
            self.save_status_btn = QPushButton("Save Status")
            self.save_status_btn.setStyleSheet("QPushButton { background-color:#10b981; color: white; padding:8px 12px; border-radius:8px; }")
            self.save_status_btn.clicked.connect(self._admin_save_status)
            action_row.addWidget(self.save_status_btn)
        detail_v.addLayout(action_row)

        # wrap the detail widget in a scroll area to avoid overflow
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setWidget(self.detail_widget)

        container_layout.addWidget(self.detail_scroll, 2)  # right column wider

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
        g = s.get("guardian", {})
        if q in g.get("name", "").lower():
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
        self.table.setColumnWidth(0, 240)

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

        self.grid_labels['dob'].setText(s.get("date_of_birth", ""))
        self.grid_labels['gender'].setText(s.get("gender", ""))
        self.grid_labels['email'].setText(s.get("email", ""))
        self.grid_labels['phone'].setText(s.get("phone", ""))
        g = s.get("guardian", {})
        self.grid_labels['guardian'].setText(f"{g.get('name','')} ({g.get('relation','')})")
        a = s.get("academic", {})
        self.grid_labels['strand'].setText(a.get("strand", ""))
        self.grid_labels['semester'].setText(a.get("semester", ""))
        self.grid_labels['school_year'].setText(a.get("school_year", ""))
        self.grid_labels['submitted_by'].setText(f"{s.get('submitted_by','')} ({s.get('submitted_role','')})")

        status_text = s.get("status", "pending").capitalize()

        if self.role == "admin":
            try:
                self.admin_status_combo.setCurrentText(s.get("status", "pending"))
            except Exception:
                pass
        else:
            st = s.get("status", "pending")
            if st == "approved":
                self.detail_status_badge.setStyleSheet("padding:4px 8px; border-radius:10px; font-weight:700; font-size:11px; background-color:#16a34a; color:white;")
            elif st == "declined":
                self.detail_status_badge.setStyleSheet("padding:4px 8px; border-radius:10px; font-weight:700; font-size:11px; background-color:#ef4444; color:white;")
            else:
                self.detail_status_badge.setStyleSheet("padding:4px 8px; border-radius:10px; font-weight:700; font-size:11px; background-color:#f59e0b; color:white;")
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
                self.detail_status_badge.setStyleSheet("padding:4px 8px; border-radius:10px; font-weight:700; font-size:11px;")
            except Exception:
                pass

    def _on_cell_double_clicked(self, row, column):
        return

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


class StudentForm(QWidget):
    def __init__(self, submit_callback=None, parent=None):
        super().__init__(parent)
        self.submit_callback = submit_callback
        outer = QVBoxLayout(self)
        outer.setSpacing(10)
        outer.setContentsMargins(0, 0, 0, 0)

        gb_style = ("QGroupBox { background-color: #ffffff; border: 1px solid #dcdcdc; "
                    "border-radius: 8px; padding: 8px; } QGroupBox::title { left: 8px; }")

        self.gb_personal = QGroupBox("Personal Information"); self.gb_personal.setStyleSheet(gb_style)
        p_layout = QVBoxLayout()
        row1 = QHBoxLayout()
        self.first_name = QLineEdit(); self.first_name.setPlaceholderText("First name")
        self.middle_name = QLineEdit(); self.middle_name.setPlaceholderText("Middle name")
        self.last_name = QLineEdit(); self.last_name.setPlaceholderText("Last name")
        for w in (self.first_name, self.middle_name, self.last_name):
            w.setStyleSheet("background-color: white; padding:6px; border:1px solid #ccc; border-radius:6px;")
        row1.addWidget(self.first_name); row1.addWidget(self.middle_name); row1.addWidget(self.last_name)

        row2 = QHBoxLayout()
        self.dob = QLineEdit(); self.dob.setPlaceholderText("Date of birth")
        self.dob.setStyleSheet("background-color: white; padding:6px; border:1px solid #ccc; border-radius:6px;")
        self.gender = QComboBox()
        self.gender.addItem("Select Gender"); self.gender.addItem("Male"); self.gender.addItem("Female"); self.gender.setCurrentIndex(0)
        self.gender.setStyleSheet("background-color: white; padding:6px; border:1px solid #ccc; border-radius:6px;")
        row2.addWidget(self.dob, 1); row2.addWidget(self.gender, 1)

        p_layout.addLayout(row1); p_layout.addLayout(row2)
        self.gb_personal.setLayout(p_layout); outer.addWidget(self.gb_personal)

        self.gb_contact = QGroupBox("Contact Information"); self.gb_contact.setStyleSheet(gb_style)
        c_layout = QHBoxLayout()
        self.email = QLineEdit(); self.email.setPlaceholderText("Email Address")
        self.phone = QLineEdit(); self.phone.setPlaceholderText("Phone Number")
        for w in (self.email, self.phone):
            w.setStyleSheet("background-color: white; padding:6px; border:1px solid #ccc; border-radius:6px;")
        c_layout.addWidget(self.email); c_layout.addWidget(self.phone)
        self.gb_contact.setLayout(c_layout); outer.addWidget(self.gb_contact)

        self.gb_guardian = QGroupBox("Guardian Information"); self.gb_guardian.setStyleSheet(gb_style)
        g_layout = QHBoxLayout()
        self.guardian_name = QLineEdit(); self.guardian_name.setPlaceholderText("Guardian Name")
        self.guardian_phone = QLineEdit(); self.guardian_phone.setPlaceholderText("Guardian Phone Number")
        self.guardian_relation = QComboBox()
        self.guardian_relation.addItem("Select Relation"); self.guardian_relation.addItems(["Father", "Mother", "Legal Guardian", "Others"])
        self.guardian_relation.setCurrentIndex(0)
        for w in (self.guardian_name, self.guardian_phone, self.guardian_relation):
            try:
                w.setStyleSheet("background-color: white; padding:6px; border:1px solid #ccc; border-radius:6px;")
            except Exception:
                pass
        g_layout.addWidget(self.guardian_name, 1); g_layout.addWidget(self.guardian_phone, 1); g_layout.addWidget(self.guardian_relation, 1)
        self.gb_guardian.setLayout(g_layout); outer.addWidget(self.gb_guardian)

        self.gb_academic = QGroupBox("Academic Information"); self.gb_academic.setStyleSheet(gb_style)
        ac_layout = QHBoxLayout()
        self.prev_school = QLineEdit(); self.prev_school.setPlaceholderText("Previous School")
        self.prev_school.setStyleSheet("background-color: white; padding:6px; border:1px solid #ccc; border-radius:6px;")
        self.strand = QComboBox(); self.strand.addItem("Select Strand")
        self.strand.addItems(["STEM", "ABM", "GAS", "HUMSS", "TVL", "Arts and Design Track"]); self.strand.setCurrentIndex(0)
        self.semester = QComboBox(); self.semester.addItem("Select Semester"); self.semester.addItems(["1st Semester", "2nd Semester"]); self.semester.setCurrentIndex(0)
        self.school_year = QComboBox(); self.school_year.addItem("Select School Year"); self.school_year.addItems(["2025 - 2026", "2026 - 2027"]); self.school_year.setCurrentIndex(0)
        for w in (self.strand, self.semester, self.school_year):
            w.setStyleSheet("background-color: white; padding:6px; border:1px solid #ccc; border-radius:6px;")
        ac_layout.addWidget(self.prev_school, 1); ac_layout.addWidget(self.strand, 1); ac_layout.addWidget(self.semester, 1); ac_layout.addWidget(self.school_year, 1)
        self.gb_academic.setLayout(ac_layout); outer.addWidget(self.gb_academic)

        btn_row = QHBoxLayout()
        self.submit_btn = QPushButton("Submit Form (adds as pending)")
        self.submit_btn.setStyleSheet("QPushButton { background-color: #2563eb; color: white; padding: 8px 12px; border-radius: 8px; } QPushButton:hover { background-color: #1d4ed8; }")
        self.submit_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(self.submit_btn, 0, Qt.AlignmentFlag.AlignLeft)
        btn_row.addStretch(); outer.addLayout(btn_row)

    def _on_submit(self):
        fn = self.first_name.text().strip(); ln = self.last_name.text().strip(); dob = self.dob.text().strip()
        email = self.email.text().strip(); phone = self.phone.text().strip()
        gn = self.guardian_name.text().strip(); gp = self.guardian_phone.text().strip()
        prev = self.prev_school.text().strip()
        # single message if incomplete
        if not (fn and ln and dob and email and phone and gn and gp and prev):
            QMessageBox.warning(self, "Form incomplete", "please fill in all requirements")
            return
        if self.gender.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "please fill in all requirements"); return
        if self.guardian_relation.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "please fill in all requirements"); return
        if self.strand.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "please fill in all requirements"); return
        if self.semester.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "please fill in all requirements"); return
        if self.school_year.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "please fill in all requirements"); return

        student = {
            "first_name": fn,
            "last_name": ln,
            "date_of_birth": dob,
            "gender": self.gender.currentText(),
            "email": email,
            "phone": phone,
            "guardian": {"name": gn, "phone": gp, "relation": self.guardian_relation.currentText()},
            "academic": {"previous_school": prev, "strand": self.strand.currentText(), "semester": self.semester.currentText(), "school_year": self.school_year.currentText()},
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
        self.setObjectName("mainWindow")
        self.user = user or {"username": "unknown", "role": "staff"}
        # show only role text (admin or staff)
        self.setWindowTitle(f"SHS Enrollment System - {self.user.get('role','')}")
        self.setStyleSheet("QWidget#mainWindow { background-color: #f3f7ff; }")

        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(18, 18, 18, 18); main_layout.setSpacing(12)

        top_container = QFrame()
        top_container.setStyleSheet("""QFrame { background: qlineargradient(x1:0 y1:0, x2:1 y2:0, stop:0 #e6f0ff, stop:1 #dbeafe); border-radius: 12px; }""")
        top_container.setFixedHeight(84)
        top_shadow = QGraphicsDropShadowEffect(self); top_shadow.setBlurRadius(20); top_shadow.setOffset(0, 4); top_shadow.setColor(QColor(13, 42, 148, 30))
        top_container.setGraphicsEffect(top_shadow)
        top_layout = QHBoxLayout(top_container); top_layout.setContentsMargins(12, 10, 12, 10)

        logo = QLabel()
        pix = QPixmap("logo.png")
        if pix.isNull():
            pix = QPixmap("img.png")
        if not pix.isNull():
            logo.setPixmap(pix.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        top_layout.addWidget(logo)

        title = QLabel("SHS Enrollment System")
        title.setStyleSheet("color: #06205f; font-weight:800; font-size:18px; padding-left:10px;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        # show only role (admin or staff)
        user_badge = QLabel(self.user.get("role", ""))
        user_badge.setStyleSheet("color:#08306b; padding:6px 8px; background: rgba(255,255,255,0.35); border-radius:8px;")
        top_layout.addWidget(user_badge)

        # logout as red button
        logout = QPushButton("Logout")
        logout.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                padding:6px 10px;
                border-radius:8px;
                border: 1px solid rgba(15, 46, 100, 0.08);
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        logout.clicked.connect(self.logout)
        top_layout.addWidget(logout)

        main_layout.addWidget(top_container)

        foreground = QFrame()
        foreground.setStyleSheet("QFrame { background-color: white; border-radius: 12px; padding: 18px; border:1px solid #e6eef9; }")
        fg_shadow = QGraphicsDropShadowEffect(self); fg_shadow.setBlurRadius(18); fg_shadow.setOffset(0, 6); fg_shadow.setColor(QColor(0, 0, 0, 20))
        foreground.setGraphicsEffect(fg_shadow)
        fg_layout = QVBoxLayout(foreground); fg_layout.setContentsMargins(8, 8, 8, 8); fg_layout.setSpacing(12)

        if self.user.get("role") == "staff":
            header_row = QHBoxLayout()
            header_label = QLabel("Staff Portal"); header_label.setStyleSheet("font-weight:600; font-size:14px;")
            header_row.addWidget(header_label); header_row.addStretch()
            self.btn_submit_page = QPushButton("Submit Student"); self.btn_view_page = QPushButton("View Students")
            for b in (self.btn_submit_page, self.btn_view_page):
                b.setStyleSheet("QPushButton { background-color: white; border: 1px solid #d6dbe7; border-radius:6px; padding:6px 10px; } QPushButton:hover { background-color:#f7fafc; }")
                b.setFixedHeight(30)
            header_row.addWidget(self.btn_submit_page); header_row.addWidget(self.btn_view_page)
            fg_layout.addLayout(header_row)

            self.staff_content = QVBoxLayout()
            self.staff_form = StudentForm(submit_callback=self._staff_submit)
            self.staff_table = StudentsTable(role="staff")
            self.staff_content.addWidget(self.staff_form)
            fg_layout.addLayout(self.staff_content)

            self.btn_submit_page.clicked.connect(self._show_staff_form)
            self.btn_view_page.clicked.connect(self._show_staff_table)
        else:
            label = QLabel("Manage Students"); label.setStyleSheet("font-weight:600; font-size:14px;")
            fg_layout.addWidget(label)
            self.table_widget = StudentsTable(role="admin"); fg_layout.addWidget(self.table_widget)

        main_layout.addWidget(foreground)
        self.setLayout(main_layout)

    def center_on_screen(self):
        app = QApplication.instance()
        if app is None:
            return
        screen = app.primaryScreen()
        if not screen:
            return
        screen_geo = screen.availableGeometry()
        x = screen_geo.x() + (screen_geo.width() - self.width()) // 2
        y = screen_geo.y() + (screen_geo.height() - self.height()) // 2
        self.move(x, y)

    def _show_staff_form(self):
        self._clear_layout(self.staff_content); self.staff_content.addWidget(self.staff_form)

    def _show_staff_table(self):
        self._clear_layout(self.staff_content); self.staff_table.refresh_table(); self.staff_content.addWidget(self.staff_table)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def _set_admin_filter(self, status):
        if hasattr(self, "table_widget") and self.table_widget.role == "admin":
            self.table_widget.set_status_filter(status)

    def _staff_submit(self, student):
        student["submitted_by"] = self.user.get("username")
        student["submitted_role"] = self.user.get("role")
        data = load_students_from_file()
        student["student_id"] = generate_student_id(data)
        data.append(student)
        save_students_to_file(data)
        try:
            if hasattr(self, "staff_table"):
                self.staff_table.refresh_table()
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
            w.showMaximized()
            app.exec()
            continue
        else:
            break


if __name__ == '__main__':
    run_app()
