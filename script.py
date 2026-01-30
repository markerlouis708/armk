# SHS Enrollment System (PyQt6)
# Updated: staff now has a search bar and a single, clean data card for "View Students".
# Both Admin and Staff show compact table: Name | Student ID | Status.
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QGroupBox,
    QComboBox, QFormLayout, QDialogButtonBox, QTextEdit
)
from PyQt6.QtGui import QPixmap, QColor, QBrush
from PyQt6.QtCore import Qt
import sys, os, json, functools

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
            logo_label.setPixmap(pixmap.scaled(120, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
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
        login_btn.setStyleSheet("QPushButton { background-color: #2563eb; color: white; padding: 8px; border-radius: 8px; } QPushButton:hover { background-color: #1d4ed8; }")
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
    def __init__(self, student: dict, original_index: int = -1, role: str = "staff", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Student Record")
        self.setMinimumSize(520, 320)
        self.original_index = original_index
        self.role = role

        self.setStyleSheet("""
            QDialog { background-color: #f6f9fc; }
            QLabel.heading { font-size: 16px; font-weight: 700; }
            QLabel.sub { color: #555; }
            QFrame.card { background-color: white; border-radius: 10px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        header = QFrame()
        header.setStyleSheet("QFrame { background-color: white; border-radius:10px; }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 12, 12, 12)

        initials = (student.get("first_name", " ")[0:1] + student.get("last_name", " ")[0:1]).upper()
        avatar = QLabel(initials)
        avatar.setFixedSize(64, 64)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("background-color: #e6f0ff; color: #1e40af; border-radius: 32px; font-weight:700; font-size:20px;")
        header_layout.addWidget(avatar)

        meta = QVBoxLayout()
        name_lbl = QLabel(f"{student.get('first_name','')} {student.get('last_name','')}")
        name_lbl.setStyleSheet("font-size:16px; font-weight:700;")
        meta.addWidget(name_lbl)
        meta.addWidget(QLabel(f"Student ID: {student.get('student_id', '')}"))
        meta.addWidget(QLabel(f"Submitted by: {student.get('submitted_by','')} {('(' + student.get('submitted_role','') + ')') if student.get('submitted_role') else ''}"))
        header_layout.addLayout(meta)
        header_layout.addStretch()

        status_box = QVBoxLayout()
        status_box.addStretch()
        if role == "admin":
            self.status_combo = QComboBox()
            self.status_combo.addItems(["pending", "approved", "declined"])
            try:
                self.status_combo.setCurrentIndex(["pending", "approved", "declined"].index(student.get("status", "pending")))
            except Exception:
                self.status_combo.setCurrentIndex(0)
            status_box.addWidget(self.status_combo)
        else:
            st = QLabel(student.get("status", "pending"))
            st.setStyleSheet("font-weight:600; color:#333;")
            status_box.addWidget(st)
        status_box.addStretch()
        header_layout.addLayout(status_box)

        layout.addWidget(header)

        body = QFrame()
        body.setStyleSheet("QFrame { background-color: white; border-radius:10px; }")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 12, 12)
        left_col = QFormLayout()
        left_col.addRow("Date of birth:", QLabel(student.get("date_of_birth", "")))
        left_col.addRow("Gender:", QLabel(student.get("gender", "")))
        left_col.addRow("Email:", QLabel(student.get("email", "")))
        body_layout.addLayout(left_col)
        right_col = QFormLayout()
        right_col.addRow("Phone:", QLabel(student.get("phone", "")))
        g = student.get("guardian", {})
        right_col.addRow("Guardian:", QLabel(f"{g.get('name','')} ({g.get('relation','')})"))
        a = student.get("academic", {})
        right_col.addRow("Strand:", QLabel(a.get("strand", "")))
        body_layout.addLayout(right_col)
        layout.addWidget(body)

        buttons = QHBoxLayout()
        buttons.addStretch()
        if role == "admin":
            save_btn = QPushButton("Save")
            save_btn.setStyleSheet("QPushButton { background-color:#10b981; color: white; padding:8px 14px; border-radius:8px; } QPushButton:hover { background-color:#059669; }")
            save_btn.clicked.connect(self._save_and_close)
            buttons.addWidget(save_btn)
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("QPushButton { background-color:#e5e7eb; padding:8px 14px; border-radius:8px; } QPushButton:hover { background-color:#d1d5db; }")
        close_btn.clicked.connect(self.reject)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def _save_and_close(self):
        if not hasattr(self, "status_combo"):
            self.accept()
            return
        new_status = self.status_combo.currentText()
        data = load_students_from_file()
        if 0 <= self.original_index < len(data):
            data[self.original_index]["status"] = new_status
            save_students_to_file(data)
            QMessageBox.information(self, "Saved", "Student status updated.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Could not locate student to save.")
            self.reject()


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


class StudentsTable(QWidget):
    """
    Single clean card with search and compact table (Name | Student ID | Status).
    Search is available for both staff and admin and filters by name, id, email, phone, guardian.
    """
    def __init__(self, role="staff", parent=None):
        super().__init__(parent)
        self.role = role
        self.filter_text = ""
        self.filter_status = "All"
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Single card container (search + table)
        container = QFrame()
        container.setStyleSheet("QFrame { background-color: white; border-radius: 12px; border: 1px solid #e8eef8; padding: 12px; }")
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(10); shadow.setOffset(0, 3); shadow.setColor(QColor(0, 0, 0, 20))
        container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(8)

        # Search: now shown for both staff and admin (same behavior)
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by name, student ID, email or phone...")
        self.search_edit.setStyleSheet("padding:6px; border:1px solid #d0d7de; border-radius:6px;")
        self.search_edit.textChanged.connect(self._on_search_changed)
        search_row.addWidget(QLabel("Search:"))
        search_row.addWidget(self.search_edit, 1)
        container_layout.addLayout(search_row)

        # Compact table
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setWordWrap(False)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        container_layout.addWidget(self.table)

        outer.addWidget(container)
        self.refresh_table()

    def set_status_filter(self, status: str):
        self.filter_status = status or "All"
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

        columns = ["Name", "Student ID", "Status"]
        self.table.clear()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(filtered))

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

    def _on_cell_double_clicked(self, row, column):
        data = load_students_from_file()
        filtered = [s for s in data if self._matches_filter(s)]
        if 0 <= row < len(filtered):
            orig_index = self._find_original_index(filtered[row])
            dlg = RecordDialog(filtered[row], original_index=orig_index, role=self.role, parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.refresh_table()


class MainWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user or {"username": "unknown", "role": "staff"}
        self.setWindowTitle(f"SHS Enrollment System - {self.user['username']} ({self.user['role']})")
        self.setMinimumSize(1000, 640)

        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        top = QHBoxLayout(); top.setContentsMargins(0, 0, 0, 0)
        logo = QLabel(); pix = QPixmap("logo.png")
        if pix.isNull(): pix = QPixmap("img.png")
        if not pix.isNull(): logo.setPixmap(pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        top.addWidget(logo)
        title = QLabel("SHS Enrollment System"); title.setStyleSheet("font-weight:700; font-size:18px; padding-left:10px;"); top.addWidget(title)
        top.addStretch()
        user_label = QLabel(f"{self.user['username']} ({self.user['role']})"); user_label.setStyleSheet("padding-right:8px; color:#333;")
        top.addWidget(user_label)
        logout = QPushButton("Logout"); logout.setStyleSheet("QPushButton { background-color:#ef4444; color:white; padding:6px 10px; border-radius:6px; }"); logout.clicked.connect(self.logout)
        top.addWidget(logout)
        main_layout.addLayout(top)

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
            app.exec()
            continue
        else:
            break


if __name__ == '__main__':
    run_app()