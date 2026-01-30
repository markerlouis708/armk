# SHS Enrollment System (PyQt6)
# Changes:
# - Redesigned RecordDialog: modern header, colored background, status badge, notes area, documents placeholder
# - Dialog centers itself over parent when opened
# - Keeps admin double-click disabled (admin won't open record by double-click) but RecordDialog is used when staff opens a record

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QGroupBox,
    QComboBox, QFormLayout, QTextEdit
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

        hint = QLabel("Sample accounts: admin / admin123  ·  staff / staff123")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(hint)

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
    """
    Redesigned student record dialog:
    - gradient header with avatar, name, id, status badge
    - two-column body with personal/contact and academic/guardian info
    - notes (read-only) and documents placeholder
    - admin gets a status combobox + Save, staff sees read-only status
    - dialog background is a cool soft color
    - dialog centers over parent when shown
    """
    def __init__(self, student: dict, original_index: int = -1, role: str = "staff", parent=None):
        super().__init__(parent)
        self.student = student or {}
        self.original_index = original_index
        self.role = role
        self.setWindowTitle("Student Record")
        self.setMinimumSize(640, 420)

        # Soft blue background for the dialog
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0 y1:0, x2:1 y2:1,
                                            stop:0 #f6f9ff, stop:1 #eef6ff);
            }
            QLabel.heading { font-size: 16px; font-weight: 700; color: #07204a; }
            QLabel.sub { color: #44556a; }
            QFrame.record-card { background: white; border-radius: 12px; }
            QLabel.badge {
                border-radius: 10px;
                padding: 6px 10px;
                color: white;
                font-weight: 700;
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(12)

        # Header - gradient strip with avatar, name, id, and status badge
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

        # Name + id
        name_block = QVBoxLayout()
        name_lbl = QLabel(f"{self.student.get('first_name','')} {self.student.get('last_name','')}")
        name_lbl.setObjectName("name_lbl")
        name_lbl.setProperty("class", "heading")
        name_lbl.setStyleSheet("font-size:16px; font-weight:800; color: #07204a;")
        name_block.addWidget(name_lbl)
        sid = self.student.get("student_id", "") or self.student.get("id", "")
        id_lbl = QLabel(f"Student ID: {sid}")
        id_lbl.setStyleSheet("color:#0b355e;")
        name_block.addWidget(id_lbl)
        header_layout.addLayout(name_block)
        header_layout.addStretch()

        # Status badge (colored)
        status = self.student.get("status", "pending")
        badge = QLabel(status.capitalize())
        badge.setProperty("class", "badge")
        if status == "approved":
            badge.setStyleSheet("background-color:#16a34a; color: white; border-radius:10px; padding:6px 10px; font-weight:700;")
        elif status == "declined":
            badge.setStyleSheet("background-color:#ef4444; color: white; border-radius:10px; padding:6px 10px; font-weight:700;")
        else:
            badge.setStyleSheet("background-color:#f59e0b; color: white; border-radius:10px; padding:6px 10px; font-weight:700;")
        header_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        main.addWidget(header)

        # Record card (white) with padding
        card = QFrame()
        card.setObjectName("record_card")
        card.setProperty("class", "record-card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(12)

        # Two column body
        body_row = QHBoxLayout()

        # Left column: personal/contact
        left = QFormLayout()
        left.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        left.addRow("Date of birth:", QLabel(self.student.get("date_of_birth", "")))
        left.addRow("Gender:", QLabel(self.student.get("gender", "")))
        left.addRow("Email:", QLabel(self.student.get("email", "")))
        left.addRow("Phone:", QLabel(self.student.get("phone", "")))
        g = self.student.get("guardian", {})
        left.addRow("Guardian:", QLabel(f"{g.get('name','')} ({g.get('relation','')})"))
        body_row.addLayout(left, 1)

        # Right column: academic & submission info
        right = QFormLayout()
        a = self.student.get("academic", {})
        right.addRow("Previous School:", QLabel(a.get("previous_school", "")))
        right.addRow("Strand:", QLabel(a.get("strand", "")))
        right.addRow("Semester:", QLabel(a.get("semester", "")))
        right.addRow("School Year:", QLabel(a.get("school_year", "")))
        right.addRow("Submitted by:", QLabel(f"{self.student.get('submitted_by','')} ({self.student.get('submitted_role','')})"))
        body_row.addLayout(right, 1)

        card_layout.addLayout(body_row)

        # Notes and documents area
        lower_row = QHBoxLayout()

        notes_box = QVBoxLayout()
        notes_box.addWidget(QLabel("Notes:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setReadOnly(True)
        self.notes_edit.setPlaceholderText("No notes available.")
        # if a 'notes' field exists show it
        self.notes_edit.setText(self.student.get("notes", ""))
        self.notes_edit.setMinimumHeight(80)
        notes_box.addWidget(self.notes_edit)
        lower_row.addLayout(notes_box, 2)

        docs_box = QVBoxLayout()
        docs_box.addWidget(QLabel("Documents:"))
        docs_placeholder = QLabel("No documents uploaded.")
        docs_placeholder.setStyleSheet("color:#6b7280; padding:12px; border:1px dashed #d1d5db; border-radius:8px;")
        docs_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        docs_box.addWidget(docs_placeholder)
        lower_row.addLayout(docs_box, 1)

        card_layout.addLayout(lower_row)

        # Buttons area
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        if self.role == "admin":
            # admin can change status here too (in addition to main table controls)
            self.admin_status = QComboBox()
            self.admin_status.addItems(["pending", "approved", "declined"])
            try:
                self.admin_status.setCurrentText(self.student.get("status", "pending"))
            except Exception:
                pass
            self.admin_status.setStyleSheet("padding:6px; border:1px solid #d0d7de; border-radius:6px;")
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

        # subtle shadow for dialog's main card
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 20))
        card.setGraphicsEffect(shadow)

        # center relative to parent
        self._center_to_parent()

    def _center_to_parent(self):
        # center dialog relative to parent (if available) otherwise center on primary screen
        parent = self.parent()
        if parent and parent.isVisible():
            pw = parent.frameGeometry().width()
            ph = parent.frameGeometry().height()
            px = parent.frameGeometry().x()
            py = parent.frameGeometry().y()
            x = px + (pw - self.width()) // 2
            y = py + (ph - self.height()) // 2
            self.move(max(0, x), max(0, y))
        else:
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    sg = screen.availableGeometry()
                    x = sg.x() + (sg.width() - self.width()) // 2
                    y = sg.y() + (sg.height() - self.height()) // 2
                    self.move(max(0, x), max(0, y))

    def _save_and_close(self):
        # Only for admin: save new status
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
    """
    Redesigned: left = search/filter/table; right = details card with role-based actions.
    """
    def __init__(self, role="staff", parent=None):
        super().__init__(parent)
        self.role = role
        self.filter_text = ""
        self.filter_status = "All"
        self.current_entries = []  # filtered entries in current table order

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Single card container (search + table + detail)
        container = QFrame()
        container.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: 1px solid #e8eef8; padding: 12px; }")
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(10); shadow.setOffset(0, 3); shadow.setColor(QColor(0, 0, 0, 20))
        container.setGraphicsEffect(shadow)

        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(12)

        # Left column: search + status filter + table
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
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("QTableWidget { border: none; }")
        left_col.addWidget(self.table, 1)

        container_layout.addLayout(left_col, 2)  # left column larger

        # Right column: detail card
        detail_card = QFrame()
        detail_card.setStyleSheet("QFrame { background-color: #f8fbff; border-radius: 10px; padding: 12px; }")
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(8, 8, 8, 8)
        detail_layout.setSpacing(8)

        # Avatar + name + id
        self.lbl_avatar = QLabel("")
        self.lbl_avatar.setFixedSize(64, 64)
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_avatar.setStyleSheet("background-color: #e6f0ff; color: #1e40af; border-radius: 32px; font-weight:700; font-size:18px;")
        detail_layout.addWidget(self.lbl_avatar, 0, Qt.AlignmentFlag.AlignHCenter)

        self.lbl_name = QLabel("Select a student")
        self.lbl_name.setStyleSheet("font-weight:700; font-size:14px;")
        self.lbl_name.setWordWrap(True)
        detail_layout.addWidget(self.lbl_name, 0, Qt.AlignmentFlag.AlignHCenter)

        self.lbl_student_id = QLabel("")
        detail_layout.addWidget(self.lbl_student_id, 0, Qt.AlignmentFlag.AlignHCenter)

        # Info fields
        self.info_layout = QFormLayout()
        self.info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.info_labels = {
            "dob": QLabel(""),
            "gender": QLabel(""),
            "email": QLabel(""),
            "phone": QLabel(""),
            "guardian": QLabel(""),
            "strand": QLabel(""),
            "status": QLabel("")
        }
        self.info_layout.addRow("Date of birth:", self.info_labels["dob"])
        self.info_layout.addRow("Gender:", self.info_labels["gender"])
        self.info_layout.addRow("Email:", self.info_labels["email"])
        self.info_layout.addRow("Phone:", self.info_labels["phone"])
        self.info_layout.addRow("Guardian:", self.info_labels["guardian"])
        self.info_layout.addRow("Strand:", self.info_labels["strand"])
        self.info_layout.addRow("Status:", self.info_labels["status"])
        detail_layout.addLayout(self.info_layout)

        detail_layout.addStretch()

        # Role-specific actions
        action_row = QHBoxLayout()
        action_row.addStretch()
        if self.role == "admin":
            self.admin_status_combo = QComboBox()
            self.admin_status_combo.addItems(["pending", "approved", "declined"])
            self.admin_status_combo.setStyleSheet("padding:6px; border:1px solid #d0d7de; border-radius:6px;")
            self.save_status_btn = QPushButton("Save Status")
            self.save_status_btn.setStyleSheet("QPushButton { background-color:#10b981; color: white; padding:8px 12px; border-radius:8px; }")
            self.save_status_btn.clicked.connect(self._admin_save_status)
            action_row.addWidget(self.admin_status_combo)
            action_row.addWidget(self.save_status_btn)
        else:
            self.open_record_btn = QPushButton("Open Record")
            self.open_record_btn.setStyleSheet("QPushButton { background-color: #2563eb; color: white; padding:8px 12px; border-radius:8px; }")
            self.open_record_btn.clicked.connect(self._open_selected_record)
            self.open_record_btn.setEnabled(False)
            action_row.addWidget(self.open_record_btn)

        detail_layout.addLayout(action_row)

        container_layout.addWidget(detail_card, 1)  # right column narrower

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

        # Clear detail view when table refreshes
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

        self.info_labels["dob"].setText(s.get("date_of_birth", ""))
        self.info_labels["gender"].setText(s.get("gender", ""))
        self.info_labels["email"].setText(s.get("email", ""))
        self.info_labels["phone"].setText(s.get("phone", ""))
        g = s.get("guardian", {})
        self.info_labels["guardian"].setText(f"{g.get('name','')} ({g.get('relation','')})")
        a = s.get("academic", {})
        self.info_labels["strand"].setText(a.get("strand", ""))
        self.info_labels["status"].setText(s.get("status", "pending"))

        # Role-based UI state
        if self.role == "admin":
            try:
                self.admin_status_combo.setCurrentText(s.get("status", "pending"))
            except Exception:
                pass
        else:
            self.open_record_btn.setEnabled(True)

    def _clear_detail(self):
        self.lbl_avatar.setText("")
        self.lbl_name.setText("Select a student")
        self.lbl_student_id.setText("")
        for k in self.info_labels:
            self.info_labels[k].setText("")
        if self.role != "admin":
            self.open_record_btn.setEnabled(False)

    def _on_cell_double_clicked(self, row, column):
        # ADMIN: do NOT open the RecordDialog on double-click (preserved behavior)
        if self.role == "admin":
            return

        # STAFF: open record as before
        if 0 <= row < len(self.current_entries):
            s = self.current_entries[row]
            orig_index = self._find_original_index(s)
            dlg = RecordDialog(s, original_index=orig_index, role=self.role, parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.refresh_table()

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
        if not (fn and ln and dob and email and phone and gn and gp and prev):
            QMessageBox.warning(self, "Form incomplete", "Please fill in all required fields.")
            return
        if self.gender.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "Please select a valid Gender."); return
        if self.guardian_relation.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "Please select Guardian Relation."); return
        if self.strand.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "Please select a Strand."); return
        if self.semester.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "Please select a Semester."); return
        if self.school_year.currentIndex() == 0:
            QMessageBox.warning(self, "Form incomplete", "Please select a School Year."); return

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
        self.user = user or {"username": "unknown", "role": "staff"}
        self.setWindowTitle(f"SHS Enrollment System - {self.user['username']} ({self.user['role']})")
        self.setMinimumSize(1000, 640)

        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # Blue top container (cool palette) with rounded corners and subtle shadow
        top_container = QFrame()
        top_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0 y1:0, x2:1 y2:0,
                                            stop:0 #e6f0ff, stop:1 #dbeafe);
                border-radius: 12px;
            }
        """)
        top_container.setFixedHeight(84)
        top_shadow = QGraphicsDropShadowEffect(self); top_shadow.setBlurRadius(20); top_shadow.setOffset(0, 4); top_shadow.setColor(QColor(13, 42, 148, 30))
        top_container.setGraphicsEffect(top_shadow)
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(12, 10, 12, 10)

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

        # user badge inside top container
        user_badge = QLabel(f"{self.user['username']} ({self.user['role']})")
        user_badge.setStyleSheet("color:#08306b; padding:6px 8px; background: rgba(255,255,255,0.35); border-radius:8px;")
        top_layout.addWidget(user_badge)

        # logout as compact white button to contrast against blue
        logout = QPushButton("Logout")
        logout.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #0b3b7a;
                padding:6px 10px;
                border-radius:8px;
                border: 1px solid rgba(15, 46, 100, 0.08);
            }
            QPushButton:hover { background-color: #f2f7ff; }
        """)
        logout.clicked.connect(self.logout)
        top_layout.addWidget(logout)

        main_layout.addWidget(top_container)

        # Foreground card (rest of the UI)
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
            quick_row = QHBoxLayout(); quick_row.addWidget(QLabel("Quick filters:"))
            btn_all = QPushButton("All"); btn_pending = QPushButton("Pending"); btn_approved = QPushButton("Approved"); btn_declined = QPushButton("Declined")
            for b in (btn_all, btn_pending, btn_approved, btn_declined):
                b.setFixedHeight(28); b.setStyleSheet("QPushButton { background-color: white; border:1px solid #d6dbe7; border-radius:6px; padding:6px 10px; } QPushButton:hover { background-color:#f7fafc; }")
            btn_all.clicked.connect(lambda: self._set_admin_filter("All")); btn_pending.clicked.connect(lambda: self._set_admin_filter("pending"))
            btn_approved.clicked.connect(lambda: self._set_admin_filter("approved")); btn_declined.clicked.connect(lambda: self._set_admin_filter("declined"))
            quick_row.addWidget(btn_all); quick_row.addWidget(btn_pending); quick_row.addWidget(btn_approved); quick_row.addWidget(btn_declined); quick_row.addStretch()
            fg_layout.addLayout(quick_row)

            self.table_widget = StudentsTable(role="admin"); fg_layout.addWidget(self.table_widget)

        main_layout.addWidget(foreground)
        self.setLayout(main_layout)

    def center_on_screen(self):
        # Centers the window on the primary screen's available geometry
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
            w.show()
            try:
                w.center_on_screen()
            except Exception:
                pass
            app.exec()
            continue
        else:
            break


if __name__ == '__main__':
    run_app()
