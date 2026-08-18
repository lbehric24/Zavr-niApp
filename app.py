import sys
import json
import os
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QScrollArea,
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox,
    QMessageBox, QSizePolicy, QGridLayout, QProgressBar,
    QDialog, QDialogButtonBox, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, QSize
from PyQt6.QtGui import QFont

from models import Course, Responsibility
from planner import (
    calculate_priority,
    estimate_study_hours,
    calculate_importance_percentage,
    generate_daily_plan,
    generate_full_plan,
)

DATA_FILE = "study_data.json"

# ── Paleta ────────────────────────────────────────────────────────────────────
BG_DARK    = "#161B25"
BG_CARD    = "#161B25"
BG_INPUT   = "#1E2435"
ACCENT     = "#8A4AD9A1"
ACCENT2    = "#AC7EF7"
ACCENT_DIM = "#2A4A6B"
TEXT_PRI   = "#E2E8F0"
TEXT_SEC   = "#64748B"
BORDER     = "#1E2D45"

# Fiksne boje za specijalne tipove
COLOR_DEFENSE  = "#F0A030"   # narančasta — obrana
COLOR_REVIEW   = "#7EB8F7"   # periwinkle — ponavljanje
DEADLINE_RED   = "#E85555"   # crvena — dan roka

# Paleta boja po predmetu (rotira se automatski)
COURSE_PALETTE = [
    "#E879A0",   # ružičasta
    "#4A90D9",   # čelično-plava
    "#A78BFA",   # lavanda
    "#34D399",   # mint zelena
    "#FB923C",   # koraljna narančasta
    "#60A5FA",   # sky plava
    "#F472B6",   # roze
    "#818CF8",   # indigo
]
_course_color_cache: dict = {}

def get_course_color(course_name: str) -> str:
    """Svaki predmet dobiva svoju boju iz palete, konzistentno kroz cijelu sesiju."""
    if course_name not in _course_color_cache:
        idx = len(_course_color_cache) % len(COURSE_PALETTE)
        _course_color_cache[course_name] = COURSE_PALETTE[idx]
    return _course_color_cache[course_name]

# Unicode ikonice
ICO_HOME    = "⊞"
ICO_COURSES = "▤"
ICO_PLAN    = "▦"
ICO_AVAIL   = "◷"
ICO_BOOK    = "◈"
ICO_ADD     = "+"
ICO_DEL     = "×"
ICO_EDIT    = "✎"
ICO_WARN    = "!"
ICO_DOT     = "●"
ICO_ARROW_L = "‹"
ICO_ARROW_R = "›"

STYLE = f"""
QMainWindow, QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRI};
    font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
}}
QFrame#card {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QFrame#cardToday {{
    background-color: {ACCENT_DIM};
    border: 1px solid {ACCENT};
    border-radius: 10px;
}}
QLabel#heading {{
    font-size: 21px;
    font-weight: 700;
    color: {TEXT_PRI};
}}
QLabel#subheading {{
    font-size: 13px;
    color: {TEXT_SEC};
}}
QLabel#sectionTitle {{
    font-size: 11px;
    font-weight: 700;
    color: {ACCENT2};
    letter-spacing: 1px;
}}
QLabel#hint {{
    font-size: 11px;
    color: {TEXT_SEC};
    font-style: italic;
}}
QPushButton#primary {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 7px;
    padding: 9px 20px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background-color: {ACCENT2};
    color: {BG_DARK};
}}
QPushButton#secondary {{
    background-color: transparent;
    color: {TEXT_SEC};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 9px 20px;
    font-size: 13px;
}}
QPushButton#secondary:hover {{
    border-color: {ACCENT};
    color: {TEXT_PRI};
}}
QPushButton#ghost {{
    background-color: transparent;
    color: {TEXT_SEC};
    border: none;
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 13px;
}}
QPushButton#ghost:hover {{
    background-color: {BG_INPUT};
    color: {TEXT_PRI};
}}
QPushButton#nav {{
    background-color: transparent;
    color: {TEXT_SEC};
    border: none;
    border-radius: 7px;
    padding: 11px 14px;
    font-size: 13px;
    text-align: left;
}}
QPushButton#nav:hover {{
    background-color: {BG_INPUT};
    color: {TEXT_PRI};
}}
QPushButton#navActive {{
    background-color: {BG_INPUT};
    color: {ACCENT2};
    border: none;
    border-left: 3px solid {ACCENT};
    border-radius: 7px;
    padding: 11px 14px;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
}}
QPushButton#arrowBtn {{
    background-color: {BG_INPUT};
    color: {ACCENT2};
    border: 2px solid {BORDER};
    border-radius: 12px;
    padding: 14px 32px;
    font-size: 22px;
    font-weight: 700;
    min-width: 70px;
    min-height: 52px;
}}
QPushButton#arrowBtn:hover {{
    background-color: {ACCENT_DIM};
    border-color: {ACCENT};
    border-width: 2px;
    color: white;
}}
QPushButton#arrowBtn:pressed {{
    background-color: {ACCENT};
    color: white;
}}
QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRI};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 8px 11px;
    font-size: 13px;
}}
QSpinBox, QDoubleSpinBox {{
    padding-right: 11px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    width: 0;
    height: 0;
    border: none;
}}
QPushButton#stepperBtn {{
    background-color: {BG_INPUT};
    color: {TEXT_PRI};
    border: 1px solid {BORDER};
    border-radius: 7px;
    font-size: 18px;
    font-weight: 600;
    padding: 0;
}}
QPushButton#stepperBtn:hover {{
    background-color: {ACCENT};
    border-color: {ACCENT};
    color: white;
}}
QPushButton#stepperBtn:pressed {{
    background-color: {ACCENT_DIM};
}}
QCheckBox {{
    font-size: 13px;
    color: {TEXT_PRI};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: {BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: {BG_INPUT};
    color: {TEXT_PRI};
    selection-background-color: {ACCENT};
    border: 1px solid {BORDER};
}}
QScrollBar:vertical {{
    background: {BG_DARK};
    width: 5px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QProgressBar {{
    background-color: {BG_INPUT};
    border: none;
    border-radius: 3px;
    height: 5px;
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 3px;
}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def fmt_hours(h: float) -> str:
    """Pretvori decimalne sate u čitljiv format: 1.5 -> '1h 30min', 0.5 -> '30min'"""
    total_min = round(h * 60)
    hours = total_min // 60
    mins  = total_min % 60
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}min"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}min"


def round_to_10min(h: float) -> float:
    """Zaokruži sate na najbližih 10 minuta."""
    total_min = h * 60
    rounded   = round(total_min / 10) * 10
    return rounded / 60


def make_label(text, role="normal", parent=None):
    lbl = QLabel(text, parent)
    lbl.setObjectName(role)
    return lbl

def make_card(today=False, parent=None):
    f = QFrame(parent)
    f.setObjectName("cardToday" if today else "card")
    return f


class StepperSpinBox(QWidget):
    """Polje za broj s [-] i [+] gumbima sa strane: [-] [ broj ] [+].
    Ponaša se kao QSpinBox: ima value(), setValue(), setRange(), setSingleStep().
    Radi jednako na svim sustavima (ne ovisi o Qt strelicama)."""

    def __init__(self, minimum=0, maximum=100, step=1, value=0,
                 decimals=0, suffix="", wrap=False, field_width=70, parent=None):
        super().__init__(parent)
        self._min   = minimum
        self._max   = maximum
        self._step  = step
        self._dec   = decimals
        self._suf   = suffix
        self._wrap  = wrap
        self._val   = value

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        self.btn_minus = QPushButton("\u2212")   # pravi minus znak
        self.btn_minus.setObjectName("stepperBtn")
        self.btn_minus.setFixedSize(QSize(34, 36))
        self.btn_minus.clicked.connect(self._dec_val)

        self.field = QLineEdit()
        self.field.setFixedWidth(field_width)
        self.field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.field.setReadOnly(True)   # vrijednost se mijenja gumbima

        self.btn_plus = QPushButton("+")
        self.btn_plus.setObjectName("stepperBtn")
        self.btn_plus.setFixedSize(QSize(34, 36))
        self.btn_plus.clicked.connect(self._inc_val)

        lay.addWidget(self.btn_minus)
        lay.addWidget(self.field)
        lay.addWidget(self.btn_plus)
        self._refresh()

    def _fmt(self, v):
        txt = f"{v:.{self._dec}f}" if self._dec else f"{int(round(v))}"
        return txt + self._suf

    def _refresh(self):
        self.field.setText(self._fmt(self._val))

    def _inc_val(self):
        v = self._val + self._step
        if v > self._max:
            v = self._min if self._wrap else self._max
        self._val = round(v, self._dec)
        self._refresh()

    def _dec_val(self):
        v = self._val - self._step
        if v < self._min:
            v = self._max if self._wrap else self._min
        self._val = round(v, self._dec)
        self._refresh()

    # API kompatibilan sa QSpinBox
    def value(self):
        return self._val

    def setValue(self, v):
        self._val = max(self._min, min(self._max, round(v, self._dec)))
        self._refresh()

    def setRange(self, lo, hi):
        self._min, self._max = lo, hi

    def setSingleStep(self, s):
        self._step = s

def entry_color(course_name, is_review, is_defense):
    """Boja kartice — po predmetu, osim za specijalne tipove."""
    if is_defense:
        return COLOR_DEFENSE
    if is_review:
        return get_course_color(course_name)
    return get_course_color(course_name)

def save_data(courses, availability, exceptions):
    data = {
        "availability": availability,
        "exceptions": {str(k): v for k, v in exceptions.items()},
        "courses": []
    }
    for c in courses:
        cd = {
            "name": c.name,
            "course_difficulty": c.course_difficulty,
            "total_points": c.total_points,
            "ects": c.ects,
            "responsibilities": []
        }
        for r in c.responsibilities:
            rd = {
                "name": r.name,
                "task_type": r.task_type,
                "max_points": r.max_points,
                "deadline": str(r.deadline),
                "task_difficulty": r.task_difficulty,
                "confidence": r.confidence,
                "note": r.note,
            }
            if r.defense_date:
                rd["defense_date"] = str(r.defense_date)
            if r.created_date:
                rd["created_date"] = str(r.created_date)
            cd["responsibilities"].append(rd)
        data["courses"].append(cd)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    if not os.path.exists(DATA_FILE):
        return [], {}, {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    availability = data.get("availability", {})
    exceptions = {}
    for k, v in data.get("exceptions", {}).items():
        exceptions[date.fromisoformat(k)] = v
    courses = []
    for cd in data.get("courses", []):
        c = Course(cd["name"], cd["course_difficulty"], cd["total_points"],
                   ects=cd.get("ects", 6))
        for rd in cd["responsibilities"]:
            defense = date.fromisoformat(rd["defense_date"]) if rd.get("defense_date") else None
            deadline_d = date.fromisoformat(rd["deadline"])
            # created_date: ako postoji u datoteci, koristi ga;
            # za stare zapise bez polja pretpostavi da je obaveza postojala
            # odavno (deadline - 90 dana) → simulacija radi kao i prije
            if rd.get("created_date"):
                created = date.fromisoformat(rd["created_date"])
            else:
                created = deadline_d - timedelta(days=90)
            r = Responsibility(
                name=rd["name"],
                task_type=rd["task_type"],
                max_points=rd["max_points"],
                deadline=deadline_d,
                task_difficulty=rd["task_difficulty"],
                confidence=rd["confidence"],
                note=rd.get("note", ""),
                defense_date=defense,
                created_date=created,
            )
            c.add_responsibility(r)
        courses.append(c)
    return courses, availability, exceptions

def week_start(d):
    return d - timedelta(days=d.weekday())

# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

class DashboardPage(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        layout.addWidget(make_label("Pregled", "heading"))
        layout.addWidget(make_label("Sve aktivne obaveze na jednom mjestu.", "subheading"))

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        self.stat_courses = self._stat_card("0", "Kolegija")
        self.stat_tasks   = self._stat_card("0", "Aktivnih obaveza")
        self.stat_hours   = self._stat_card("0h", "Ukupno sati učenja")
        self.stat_urgent  = self._stat_card("0", "Hitnih  ≤ 7 dana")
        for w in [self.stat_courses, self.stat_tasks, self.stat_hours, self.stat_urgent]:
            stats_row.addWidget(w)
        layout.addLayout(stats_row)

        layout.addWidget(make_label("OBAVEZE PO PRIORITETU", "sectionTitle"))
        self.priority_container = QVBoxLayout()
        self.priority_container.setSpacing(8)
        layout.addLayout(self.priority_container)
        layout.addStretch()

    def _stat_card(self, value, label):
        card = make_card()
        vl = QVBoxLayout(card)
        vl.setContentsMargins(18, 14, 18, 14)
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {ACCENT2};")
        l_lbl = QLabel(label)
        l_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_SEC};")
        vl.addWidget(v_lbl)
        vl.addWidget(l_lbl)
        card._val = v_lbl
        return card

    def refresh(self):
        courses = self.app_state["courses"]
        active_all, total_h, urgent = [], 0, 0
        for c in courses:
            for r in c.active_responsibilities():
                h = estimate_study_hours(c, r)
                total_h += h
                if (r.deadline - date.today()).days <= 7:
                    urgent += 1
                active_all.append((c, r, calculate_priority(c, r), h))
        active_all.sort(key=lambda x: x[2], reverse=True)

        self.stat_courses._val.setText(str(len(courses)))
        self.stat_tasks._val.setText(str(len(active_all)))
        self.stat_hours._val.setText(fmt_hours(total_h))
        self.stat_urgent._val.setText(str(urgent))
        col = ACCENT2 if urgent == 0 else DEADLINE_RED
        self.stat_urgent._val.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {col};")

        while self.priority_container.count():
            item = self.priority_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not active_all:
            self.priority_container.addWidget(
                make_label("Nema aktivnih obaveza. Dodaj kolegij!", "subheading"))
            return
        for c, r, pri, hrs in active_all[:10]:
            self.priority_container.addWidget(self._task_row(c, r, pri, hrs))

    def _task_row(self, course, resp, priority, hours):
        card = make_card()
        hl = QHBoxLayout(card)
        hl.setContentsMargins(16, 12, 16, 12)
        hl.setSpacing(14)

        days_left = (resp.deadline - date.today()).days
        dot_col = TEXT_PRI if days_left <= 3 else (ACCENT2 if days_left <= 7 else TEXT_SEC)

        dot = QLabel(ICO_DOT)
        dot.setStyleSheet(f"color: {dot_col}; font-size: 10px;")
        dot.setFixedWidth(16)

        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = QLabel(
            f"{resp.name}"
            f"  <span style='color:{TEXT_SEC}; font-size:11px;'>{resp.task_type}</span>"
        )
        name_lbl.setTextFormat(Qt.TextFormat.RichText)
        name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {TEXT_PRI};")
        deadline_txt = f"rok: {resp.deadline}"
        if resp.has_defense():
            deadline_txt += f"  ·  obrana: {resp.defense_date}"
        course_lbl = QLabel(f"{course.name}  ·  {deadline_txt}  ·  {days_left} d")
        course_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_SEC};")
        info.addWidget(name_lbl)
        info.addWidget(course_lbl)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pri_lbl = QLabel(f"prioritet  {priority:.0f}")
        pri_lbl.setStyleSheet(f"font-size: 11px; color: {ACCENT2}; font-weight: 600;")
        hrs_lbl = QLabel(f"~ {fmt_hours(hours)}")
        hrs_lbl.setStyleSheet(f"font-size: 12px; color: {TEXT_SEC};")
        right.addWidget(pri_lbl)
        right.addWidget(hrs_lbl)

        hl.addWidget(dot)
        hl.addLayout(info, 1)
        hl.addLayout(right)
        return card

# ─────────────────────────────────────────────────────────────────────────────
# Kolegiji
# ─────────────────────────────────────────────────────────────────────────────

class CoursesPage(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        container = QWidget()
        scroll.setWidget(container)
        self.layout_main = QVBoxLayout(container)
        self.layout_main.setContentsMargins(32, 28, 32, 28)
        self.layout_main.setSpacing(18)

        row = QHBoxLayout()
        row.addWidget(make_label("Kolegiji", "heading"))
        row.addStretch()
        btn = QPushButton(f"{ICO_ADD}  Dodaj kolegij")
        btn.setObjectName("primary")
        btn.setFixedWidth(160)
        btn.clicked.connect(self._open_add_course)
        row.addWidget(btn)
        self.layout_main.addLayout(row)

        self.courses_container = QVBoxLayout()
        self.courses_container.setSpacing(12)
        self.layout_main.addLayout(self.courses_container)
        self.layout_main.addStretch()

    def refresh(self):
        while self.courses_container.count():
            item = self.courses_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        courses = self.app_state["courses"]
        if not courses:
            self.courses_container.addWidget(
                make_label("Još nemaš dodanih kolegija.", "subheading"))
            return
        for course in courses:
            self.courses_container.addWidget(self._course_card(course))

    def _course_card(self, course):
        card = make_card()
        vl = QVBoxLayout(card)
        vl.setContentsMargins(18, 14, 18, 14)
        vl.setSpacing(8)

        header = QHBoxLayout()
        name_lbl = QLabel(course.name)
        name_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {TEXT_PRI};")
        diff_lbl = QLabel(f"težina  {course.course_difficulty}/10")
        diff_lbl.setStyleSheet(f"font-size: 11px; color: {ACCENT2};")

        btn_edit = QPushButton(ICO_EDIT)
        btn_edit.setObjectName("ghost")
        btn_edit.setFixedWidth(34)
        btn_edit.setToolTip("Uredi kolegij")
        btn_edit.clicked.connect(lambda _, c=course: self._open_edit_course(c))

        btn_del = QPushButton(ICO_DEL)
        btn_del.setObjectName("ghost")
        btn_del.setFixedWidth(34)
        btn_del.setToolTip("Ukloni kolegij")
        btn_del.clicked.connect(lambda _, c=course: self._delete_course(c))

        header.addWidget(name_lbl)
        header.addStretch()
        header.addWidget(diff_lbl)
        header.addWidget(btn_edit)
        header.addWidget(btn_del)
        vl.addLayout(header)

        used = course.used_points()
        total = course.total_points
        pct = int(used / total * 100) if total > 0 else 0
        bar = QProgressBar()
        bar.setValue(pct)
        bar.setTextVisible(False)
        bar.setFixedHeight(5)
        vl.addWidget(bar)
        pts_lbl = QLabel(f"{used} / {total} bodova")
        pts_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_SEC};")
        vl.addWidget(pts_lbl)

        if course.responsibilities:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"background-color: {BORDER}; max-height: 1px;")
            vl.addWidget(sep)
            for r in course.responsibilities:
                vl.addWidget(self._resp_row(r, course))

        btn_add_r = QPushButton(f"{ICO_ADD}  Dodaj obavezu")
        btn_add_r.setObjectName("secondary")
        btn_add_r.clicked.connect(lambda _, c=course: self._open_add_resp(c))
        vl.addWidget(btn_add_r)
        return card

    def _resp_row(self, resp, course):
        w = QWidget()
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 3, 0, 3)

        # Obojena točka prema tipu
        col = get_course_color(course.name)
        dot = QLabel(ICO_DOT)
        dot.setStyleSheet(f"color: {col if resp.is_active() else TEXT_SEC}; font-size: 8px;")
        dot.setFixedWidth(16)

        deadline_txt = str(resp.deadline)
        if resp.has_defense():
            deadline_txt += f"  obrana: {resp.defense_date}"

        info = QLabel(
            f"{resp.name}"
            f"  <span style='color:{TEXT_SEC}'>{resp.task_type}  ·  "
            f"{resp.max_points} bod.  ·  rok {deadline_txt}</span>"
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setStyleSheet(f"font-size: 12px; color: {TEXT_PRI};")

        btn_edit = QPushButton(ICO_EDIT)
        btn_edit.setObjectName("ghost")
        btn_edit.setFixedWidth(30)
        btn_edit.setToolTip("Uredi obavezu")
        btn_edit.clicked.connect(lambda _, r=resp, c=course: self._open_edit_resp(r, c))

        btn_del = QPushButton(ICO_DEL)
        btn_del.setObjectName("ghost")
        btn_del.setFixedWidth(30)
        btn_del.setToolTip("Ukloni obavezu")
        btn_del.clicked.connect(lambda _, r=resp, c=course: self._delete_resp(r, c))

        hl.addWidget(dot)
        hl.addWidget(info, 1)
        hl.addWidget(btn_edit)
        hl.addWidget(btn_del)
        return w

    def _delete_course(self, course):
        reply = QMessageBox.question(
            self, "Ukloni kolegij", f"Ukloniti '{course.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.app_state["courses"].remove(course)
            self._save_and_refresh()

    def _delete_resp(self, resp, course):
        reply = QMessageBox.question(
            self, "Ukloni obavezu", f"Ukloniti '{resp.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            course.responsibilities.remove(resp)
            self._save_and_refresh()

    def _save_and_refresh(self):
        save_data(self.app_state["courses"],
                  self.app_state["availability"],
                  self.app_state["exceptions"])
        self.refresh()
        self.app_state["dashboard"].refresh()
        self.app_state["plan"].refresh()

    def _open_add_course(self):
        dlg = CourseDialog(self)
        if dlg.exec():
            self.app_state["courses"].append(dlg.course)
            self._save_and_refresh()

    def _open_edit_course(self, course):
        dlg = CourseDialog(self, course=course)
        if dlg.exec():
            self._save_and_refresh()

    def _open_add_resp(self, course):
        dlg = ResponsibilityDialog(course, self)
        if dlg.exec():
            self._save_and_refresh()

    def _open_edit_resp(self, resp, course):
        dlg = ResponsibilityDialog(course, self, resp=resp)
        if dlg.exec():
            self._save_and_refresh()

# ─────────────────────────────────────────────────────────────────────────────
# Plan — tjedni kalendar
# ─────────────────────────────────────────────────────────────────────────────

DAY_NAMES = ["Pon", "Uto", "Sri", "Čet", "Pet", "Sub", "Ned"]

class PlanPage(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.week_offset = 0
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(16)

        nav_row = QHBoxLayout()
        title = make_label("Tjedni plan", "heading")
        nav_row.addWidget(title)
        nav_row.addStretch()

        self.btn_prev = QPushButton(ICO_ARROW_L)
        self.btn_prev.setObjectName("arrowBtn")
        self.btn_prev.clicked.connect(self._prev_week)

        self.week_lbl = QLabel("")
        self.week_lbl.setStyleSheet(
            f"font-size: 13px; color: {ACCENT2}; font-weight: 600; padding: 0 10px;")
        self.week_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.week_lbl.setMinimumWidth(220)

        self.btn_next = QPushButton(ICO_ARROW_R)
        self.btn_next.setObjectName("arrowBtn")
        self.btn_next.clicked.connect(self._next_week)

        nav_row.addWidget(self.btn_prev)
        nav_row.addWidget(self.week_lbl)
        nav_row.addWidget(self.btn_next)
        outer.addLayout(nav_row)

        # Legenda — posebni tipovi (fiksni)
        legend_row = QHBoxLayout()
        legend_row.setSpacing(16)
        for color, label in [
            (COLOR_REVIEW,  "ponavljanje"),
            (COLOR_DEFENSE, "obrana"),
            (DEADLINE_RED,  "dan roka"),
        ]:
            dot = QLabel(f"● {label}")
            dot.setStyleSheet(f"font-size: 11px; color: {color};")
            legend_row.addWidget(dot)
        legend_row.addStretch()
        # Dinamička legenda predmeta ažurira se pri refreshu
        self.legend_courses_row = QHBoxLayout()
        self.legend_courses_row.setSpacing(12)
        outer.addLayout(legend_row)
        outer.addLayout(self.legend_courses_row)

        self.warn_container = QVBoxLayout()
        self.warn_container.setSpacing(6)
        outer.addLayout(self.warn_container)

        self.grid_widget = QWidget()
        self.grid_layout = QHBoxLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(8)
        outer.addWidget(self.grid_widget, 1)

    def _prev_week(self):
        self.week_offset -= 1
        self.refresh()

    def _next_week(self):
        self.week_offset += 1
        self.refresh()

    def refresh(self):
        today = date.today()
        base = week_start(today) + timedelta(weeks=self.week_offset)
        week_dates = [base + timedelta(days=i) for i in range(7)]

        self.week_lbl.setText(
            f"{week_dates[0].strftime('%d.%m.')}  –  {week_dates[6].strftime('%d.%m.%Y.')}")

        courses    = self.app_state["courses"]
        avail      = self.app_state["availability"]
        exceptions = self.app_state["exceptions"]

        # Obnovi legendu predmeta
        while self.legend_courses_row.count():
            item = self.legend_courses_row.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for c in courses:
            col = get_course_color(c.name)
            lbl = QLabel(f"● {c.name}")
            lbl.setStyleSheet(f"font-size: 11px; color: {col};")
            self.legend_courses_row.addWidget(lbl)
        self.legend_courses_row.addStretch()

        # Koristi generate_full_plan koji dijeli used_per_day između obaveza
        # i osigurava da ukupno ne prelazi dnevnu dostupnost studenta
        all_days, warnings = generate_full_plan(courses, avail, exceptions)

        # Upozorenja
        while self.warn_container.count():
            item = self.warn_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for w in warnings:
            warn_card = QFrame()
            warn_card.setStyleSheet(
                f"background-color: {BG_INPUT}; border: 1px solid {BORDER}; border-radius: 8px;")
            hl = QHBoxLayout(warn_card)
            hl.setContentsMargins(14, 8, 14, 8)
            lbl = QLabel(f"{ICO_WARN}  {w['course']}  ·  {w['task']}  — nedostaje  {w['hours']} h")
            lbl.setStyleSheet(f"font-size: 12px; color: {TEXT_SEC};")
            hl.addWidget(lbl)
            self.warn_container.addWidget(warn_card)

        # Očisti grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for d in week_dates:
            col = self._day_column(d, all_days.get(d, []), d == today, avail, exceptions)
            self.grid_layout.addWidget(col, 1)

    def _day_column(self, d, entries, is_today, avail, exceptions):
        card = make_card(today=is_today)
        vl = QVBoxLayout(card)
        vl.setContentsMargins(10, 10, 10, 10)
        vl.setSpacing(6)
        vl.setAlignment(Qt.AlignmentFlag.AlignTop)

        day_name_lbl = QLabel(DAY_NAMES[d.weekday()])
        day_name_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {'#FFFFFF' if is_today else TEXT_SEC};")
        day_name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        date_lbl = QLabel(d.strftime("%d.%m."))
        date_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: {'700' if is_today else '400'}; "
            f"color: {ACCENT2 if is_today else TEXT_PRI};")
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(day_name_lbl)
        vl.addWidget(date_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {BORDER}; max-height: 1px;")
        vl.addWidget(sep)

        # Dostupnost
        if d in exceptions:
            avail_h = exceptions[d]["hours"]
            reason  = exceptions[d]["reason"]
            avail_lbl = QLabel(f"◷  {fmt_hours(avail_h)}" + (f"\n{reason}" if reason else ""))
        else:
            day_key = d.strftime("%A").lower()
            avail_h = avail.get(day_key, 0)
            avail_lbl = QLabel(f"◷  {fmt_hours(avail_h)}")

        avail_lbl.setStyleSheet(f"font-size: 10px; color: {TEXT_SEC};")
        avail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(avail_lbl)

        if not entries:
            dash = QLabel("—")
            dash.setStyleSheet(f"font-size: 11px; color: {BORDER};")
            dash.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl.addWidget(dash)
        else:
            for e in entries:
                is_review   = e.get("is_review", False)
                is_defense  = e.get("is_defense", False)
                is_deadline = e.get("is_deadline", False)
                task_type   = e.get("task_type", "")
                course_name = e.get("course", "")

                if is_deadline:
                    border_color = DEADLINE_RED
                    border_width = "2px"
                else:
                    border_color = entry_color(course_name, is_review, is_defense)
                    border_width = "1px"

                entry_card = QFrame()
                entry_card.setStyleSheet(
                    f"background-color: {BG_INPUT}; "
                    f"border: {border_width} solid {border_color}; "
                    f"border-radius: 5px;"
                )
                el = QVBoxLayout(entry_card)
                el.setContentsMargins(7, 5, 7, 5)
                el.setSpacing(0)

                # Redoslijed: naziv predmeta (naslov), tip obaveze, sati
                name_color = DEADLINE_RED if is_deadline else border_color

                # Naslov — naziv predmeta (ili posebna oznaka za rok/obranu)
                if is_deadline or is_defense:
                    # Za rok/obranu task već sadrži pun opis
                    title_text = e["task"]
                    subtitle_text = ""
                else:
                    # Normalno učenje: naslov = predmet, podnaslov = nazivi obaveza
                    title_text = course_name
                    resp_names = e.get("resp_names", [])
                    if resp_names:
                        subtitle_text = ",  ".join(resp_names)
                    else:
                        subtitle_text = task_type if task_type else ""

                title_lbl = QLabel(title_text)
                title_lbl.setStyleSheet(
                    f"font-size: 11px; font-weight: 700; color: {name_color}; border: none;")
                title_lbl.setWordWrap(True)
                el.addWidget(title_lbl)

                # Ako kartica sadrži i ponavljanje, dodaj oznaku
                has_review = e.get("has_review", False)
                if has_review and subtitle_text:
                    subtitle_text = subtitle_text + "  +  ponavljanje"
                elif has_review:
                    subtitle_text = "ponavljanje"

                if subtitle_text:
                    sep1 = QFrame()
                    sep1.setFrameShape(QFrame.Shape.HLine)
                    sep1.setStyleSheet(f"background-color: {BORDER}; max-height: 1px; border: none;")
                    el.addWidget(sep1)
                    sub_lbl = QLabel(subtitle_text)
                    sub_lbl.setStyleSheet(
                        f"font-size: 10px; color: {TEXT_SEC}; border: none; padding-top: 1px;")
                    el.addWidget(sub_lbl)

                if not is_defense and not is_deadline and e["hours"] > 0:
                    sep2 = QFrame()
                    sep2.setFrameShape(QFrame.Shape.HLine)
                    sep2.setStyleSheet(f"background-color: {BORDER}; max-height: 1px; border: none;")
                    el.addWidget(sep2)
                    hrs_lbl = QLabel(fmt_hours(e["hours"]))
                    hrs_lbl.setStyleSheet(
                        f"font-size: 10px; color: {TEXT_SEC}; border: none; padding-top: 1px;")
                    el.addWidget(hrs_lbl)

                vl.addWidget(entry_card)

        vl.addStretch()
        return card

# ─────────────────────────────────────────────────────────────────────────────
# Mogućnost učenja
# ─────────────────────────────────────────────────────────────────────────────

class AvailabilityPage(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        layout.addWidget(make_label("Mogućnost učenja", "heading"))
        layout.addWidget(make_label(
            "Postavi koliko sati možeš učiti po danima i dodaj posebne datume.", "subheading"))

        avail_card = make_card()
        avl = QVBoxLayout(avail_card)
        avl.setContentsMargins(20, 16, 20, 20)
        avl.setSpacing(12)
        avl.addWidget(make_label("TJEDNA DOSTUPNOST (SATI)", "sectionTitle"))

        self.day_spins = {}
        days = [
            ("monday", "Ponedjeljak"), ("tuesday", "Utorak"),
            ("wednesday", "Srijeda"),  ("thursday", "Četvrtak"),
            ("friday", "Petak"),       ("saturday", "Subota"),
            ("sunday", "Nedjelja"),
        ]
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)   # prazan prostor desno, widgeti ostaju lijevo
        for i, (key, name) in enumerate(days):
            lbl = QLabel(name)
            lbl.setStyleSheet(f"font-size: 13px; color: {TEXT_PRI};")
            lbl.setFixedWidth(140)
            # Sati + minute (korak 10)
            day_widget = QWidget()
            day_hl = QHBoxLayout(day_widget)
            day_hl.setContentsMargins(0, 0, 0, 0)
            day_hl.setSpacing(8)

            cur_val = self.app_state["availability"].get(key, 0)
            cur_h   = int(cur_val)
            cur_m   = round((cur_val - cur_h) * 60 / 10) * 10
            # Rub: ako se minute zaokruže na 60, prebaci u sljedeći sat
            if cur_m >= 60:
                cur_h += 1
                cur_m = 0

            h_spin = StepperSpinBox(minimum=0, maximum=24, step=1,
                                    value=cur_h, suffix=" h", field_width=64)

            m_spin = StepperSpinBox(minimum=0, maximum=50, step=10,
                                    value=cur_m, suffix=" min", wrap=True,
                                    field_width=72)

            day_hl.addWidget(h_spin)
            day_hl.addWidget(m_spin)
            day_hl.addStretch()        # gura steppere lijevo
            self.day_spins[key] = (h_spin, m_spin)
            grid.addWidget(lbl,        i, 0)
            grid.addWidget(day_widget, i, 1)
        avl.addLayout(grid)

        btn_save = QPushButton("Spremi tjednu dostupnost")
        btn_save.setObjectName("primary")
        btn_save.setFixedWidth(240)
        btn_save.clicked.connect(self._save_availability)
        avl.addWidget(btn_save)
        layout.addWidget(avail_card)

        exc_card = make_card()
        excl = QVBoxLayout(exc_card)
        excl.setContentsMargins(20, 16, 20, 16)
        excl.setSpacing(10)

        exc_hdr = QHBoxLayout()
        exc_hdr.addWidget(make_label("POSEBNI DATUMI", "sectionTitle"))
        exc_hdr.addStretch()
        btn_add_exc = QPushButton(f"{ICO_ADD}  Dodaj datum")
        btn_add_exc.setObjectName("secondary")
        btn_add_exc.setFixedWidth(150)
        btn_add_exc.clicked.connect(self._open_add_exception)
        exc_hdr.addWidget(btn_add_exc)
        excl.addLayout(exc_hdr)
        excl.addWidget(make_label(
            "Datumi kada ne možeš učiti ili možeš drugačije nego inače.", "subheading"))

        self.exc_container = QVBoxLayout()
        self.exc_container.setSpacing(6)
        excl.addLayout(self.exc_container)
        layout.addWidget(exc_card)
        layout.addStretch()
        self._refresh_exceptions()

    def _refresh_exceptions(self):
        while self.exc_container.count():
            item = self.exc_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        exceptions = self.app_state["exceptions"]
        if not exceptions:
            self.exc_container.addWidget(make_label("Nema dodanih posebnih datuma.", "subheading"))
            return

        for d in sorted(exceptions.keys()):
            info = exceptions[d]
            row_w = QWidget()
            hl = QHBoxLayout(row_w)
            hl.setContentsMargins(0, 2, 0, 2)
            lbl = QLabel(
                f"{d.strftime('%d.%m.%Y.')}  —  {info['hours']} h"
                + (f"  ·  {info['reason']}" if info.get('reason') else ""))
            lbl.setStyleSheet(f"font-size: 13px; color: {TEXT_PRI};")
            btn_del = QPushButton(ICO_DEL)
            btn_del.setObjectName("ghost")
            btn_del.setFixedWidth(34)
            btn_del.clicked.connect(lambda _, dd=d: self._delete_exception(dd))
            hl.addWidget(lbl)
            hl.addStretch()
            hl.addWidget(btn_del)
            self.exc_container.addWidget(row_w)

    def _open_add_exception(self):
        dlg = AddExceptionDialog(self)
        if dlg.exec():
            d, hours, reason = dlg.result_data
            self.app_state["exceptions"][d] = {"hours": hours, "reason": reason}
            save_data(self.app_state["courses"],
                      self.app_state["availability"],
                      self.app_state["exceptions"])
            self._refresh_exceptions()
            self.app_state["plan"].refresh()

    def _delete_exception(self, d):
        del self.app_state["exceptions"][d]
        save_data(self.app_state["courses"],
                  self.app_state["availability"],
                  self.app_state["exceptions"])
        self._refresh_exceptions()
        self.app_state["plan"].refresh()

    def _save_availability(self):
        avail = {}
        for k, (h_spin, m_spin) in self.day_spins.items():
            h = h_spin.value()
            m = m_spin.value()
            avail[k] = h + m / 60
        self.app_state["availability"] = avail
        save_data(self.app_state["courses"], avail, self.app_state["exceptions"])
        QMessageBox.information(self, "Spremljeno", "Dostupnost je uspješno spremljena!")
        self.app_state["dashboard"].refresh()
        self.app_state["plan"].refresh()

# ─────────────────────────────────────────────────────────────────────────────
# Dijalozi
# ─────────────────────────────────────────────────────────────────────────────

class CourseDialog(QDialog):
    """Dodaj ili uredi kolegij."""
    def __init__(self, parent=None, course=None):
        super().__init__(parent)
        self.course = course
        self.result_course = None
        self.setWindowTitle("Uredi kolegij" if course else "Dodaj kolegij")
        self.setMinimumWidth(380)
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.addWidget(make_label("Uredi kolegij" if self.course else "Novi kolegij", "heading"))

        layout.addWidget(QLabel("Naziv kolegija"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("npr. Matematika 2")
        if self.course:
            self.name_edit.setText(self.course.name)
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Težina  (1 – 10)"))
        self.diff_spin = StepperSpinBox(
            minimum=1, maximum=10, step=1,
            value=self.course.course_difficulty if self.course else 5)
        layout.addWidget(self.diff_spin)

        layout.addWidget(QLabel("ECTS bodovi"))
        self.ects_spin = StepperSpinBox(
            minimum=1, maximum=30, step=1,
            value=self.course.ects if self.course else 6)
        layout.addWidget(self.ects_spin)

        layout.addWidget(QLabel("Ukupno bodova"))
        self.pts_spin = StepperSpinBox(
            minimum=1, maximum=1000, step=5,
            value=self.course.total_points if self.course else 100)
        layout.addWidget(self.pts_spin)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Greška", "Unesi naziv kolegija.")
            return
        if self.course:
            self.course.name = name
            self.course.course_difficulty = self.diff_spin.value()
            self.course.ects = self.ects_spin.value()
            self.course.total_points = self.pts_spin.value()
        else:
            self.course = Course(name, self.diff_spin.value(), self.pts_spin.value(),
                                 ects=self.ects_spin.value())
        self.accept()


class ResponsibilityDialog(QDialog):
    """Dodaj ili uredi obavezu. Prikazuje polje za obranu samo za projekt/seminar."""
    def __init__(self, course, parent=None, resp=None):
        super().__init__(parent)
        self.course = course
        self.resp = resp  # None = dodaj novo, inače uredi
        self.setWindowTitle(
            f"Uredi obavezu  —  {course.name}" if resp
            else f"Dodaj obavezu  —  {course.name}")
        self.setMinimumWidth(440)
        self.setStyleSheet(STYLE)
        self._build()
        # Ograniči visinu dijaloga na visinu ekrana da gumbi ostanu vidljivi
        try:
            scr = self.screen().availableGeometry().height()
            self.setMaximumHeight(min(scr - 60, 900))
        except Exception:
            self.setMaximumHeight(820)

    def _build(self):
        # Vanjski layout drži scroll (sadržaj) + fiksne gumbe na dnu
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.addWidget(make_label(
            "Uredi obavezu" if self.resp else "Nova obaveza", "heading"))

        layout.addWidget(QLabel("Naziv obaveze"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("npr. Kolokvij 1")
        if self.resp:
            self.name_edit.setText(self.resp.name)
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Tip obaveze"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["kolokvij", "ispit", "projekt", "seminar", "usmeni", "mini test"])
        if self.resp:
            idx = self.type_combo.findText(self.resp.task_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        layout.addWidget(self.type_combo)

        remaining = self.course.remaining_points()
        if self.resp:
            # Vraćamo bodove od ove obaveze natrag da bi se moglo urediti
            remaining += self.resp.max_points
        layout.addWidget(QLabel(f"Bodovi  (preostalo: {round(remaining, 1)})"))
        self.pts_spin = StepperSpinBox(
            minimum=0, maximum=remaining if remaining > 0 else 1000,
            step=0.5, decimals=1, field_width=80,
            value=self.resp.max_points if self.resp else min(10, remaining))
        layout.addWidget(self.pts_spin)

        layout.addWidget(QLabel("Rok predaje  (datum)"))
        self.deadline_edit = QDateEdit()
        self.deadline_edit.setCalendarPopup(True)
        if self.resp:
            d = self.resp.deadline
            self.deadline_edit.setDate(QDate(d.year, d.month, d.day))
        else:
            self.deadline_edit.setDate(QDate.currentDate().addDays(14))
        layout.addWidget(self.deadline_edit)

        layout.addWidget(QLabel("Težina obaveze  (1 – 10)"))
        self.diff_spin = StepperSpinBox(
            minimum=1, maximum=10, step=1,
            value=self.resp.task_difficulty if self.resp else 5)
        layout.addWidget(self.diff_spin)

        # Samopouzdanje s pojašnjenjem
        layout.addWidget(QLabel("Samopouzdanje  (1 – 10)"))
        self.conf_spin = StepperSpinBox(
            minimum=1, maximum=10, step=1,
            value=self.resp.confidence if self.resp else 5)
        layout.addWidget(self.conf_spin)
        hint = make_label(
            "1 = osjećam se izgubljeno, 10 = gradivo znam izvrsno.\n"
            "Niže samopouzdanje → planer predviđa više sati učenja.", "hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addWidget(QLabel("Napomena  (neobavezno)"))
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("npr. gradivo od 1. do 5. poglavlja")
        if self.resp:
            self.note_edit.setText(self.resp.note)
        layout.addWidget(self.note_edit)

        # Obrana — vidljiva samo za projekt/seminar
        self.defense_widget = QWidget()
        dfl = QVBoxLayout(self.defense_widget)
        dfl.setContentsMargins(0, 0, 0, 0)
        dfl.setSpacing(6)

        self.defense_check = QCheckBox("Imam i datum obrane")
        has_defense = self.resp is not None and self.resp.has_defense()
        self.defense_check.setChecked(has_defense)
        self.defense_check.toggled.connect(self._on_defense_toggled)
        dfl.addWidget(self.defense_check)

        self.defense_date_label = QLabel("Datum obrane")
        self.defense_date_edit = QDateEdit()
        self.defense_date_edit.setCalendarPopup(True)
        if self.resp and self.resp.defense_date:
            dd = self.resp.defense_date
            self.defense_date_edit.setDate(QDate(dd.year, dd.month, dd.day))
        else:
            self.defense_date_edit.setDate(QDate.currentDate().addDays(21))
        dfl.addWidget(self.defense_date_label)
        dfl.addWidget(self.defense_date_edit)
        layout.addWidget(self.defense_widget)

        # Gumbi idu u VANJSKI layout (izvan scrolla) -> uvijek vidljivi na dnu
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        btn_wrap = QWidget()
        bwl = QVBoxLayout(btn_wrap)
        bwl.setContentsMargins(24, 10, 24, 16)
        bwl.addWidget(btns)
        self.layout().addWidget(btn_wrap, 0)

        # Inicijalno postavi vidljivost
        self._on_type_changed(self.type_combo.currentText())
        self._on_defense_toggled(has_defense)

    def _on_type_changed(self, task_type):
        is_project = task_type.lower() in ("projekt", "seminar")
        self.defense_widget.setVisible(is_project)

    def _on_defense_toggled(self, checked):
        self.defense_date_label.setVisible(checked)
        self.defense_date_edit.setVisible(checked)

    def _accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Greška", "Unesi naziv obaveze.")
            return
        qd = self.deadline_edit.date()
        deadline = date(qd.year(), qd.month(), qd.day())

        task_type = self.type_combo.currentText()
        is_project = task_type.lower() in ("projekt", "seminar")

        defense_date = None
        if is_project and self.defense_check.isChecked():
            qdd = self.defense_date_edit.date()
            defense_date = date(qdd.year(), qdd.month(), qdd.day())
            if defense_date <= deadline:
                QMessageBox.warning(self, "Greška",
                    "Datum obrane mora biti nakon datuma predaje.")
                return

        if self.resp:
            # Uredi postojeću
            self.resp.name          = name
            self.resp.task_type     = task_type
            self.resp.max_points    = self.pts_spin.value()
            self.resp.deadline      = deadline
            self.resp.task_difficulty = self.diff_spin.value()
            self.resp.confidence    = self.conf_spin.value()
            self.resp.note          = self.note_edit.text().strip()
            self.resp.defense_date  = defense_date
        else:
            r = Responsibility(
                name=name,
                task_type=task_type,
                max_points=self.pts_spin.value(),
                deadline=deadline,
                task_difficulty=self.diff_spin.value(),
                confidence=self.conf_spin.value(),
                note=self.note_edit.text().strip(),
                defense_date=defense_date,
            )
            self.course.add_responsibility(r)
        self.accept()


class AddExceptionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_data = None
        self.setWindowTitle("Posebni datum")
        self.setMinimumWidth(360)
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.addWidget(make_label("Posebni datum", "heading"))
        layout.addWidget(make_label(
            "Unesi datum kada ne možeš (ili možeš drugačije) učiti.", "subheading"))

        layout.addWidget(QLabel("Datum"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addDays(1))
        layout.addWidget(self.date_edit)

        layout.addWidget(QLabel("Sati učenja taj dan  (0 = ne mogu učiti)"))
        exc_time_w = QWidget()
        exc_hl = QHBoxLayout(exc_time_w)
        exc_hl.setContentsMargins(0, 0, 0, 0)
        exc_hl.setSpacing(4)
        self.exc_h_spin = StepperSpinBox(minimum=0, maximum=24, step=1,
                                         value=0, suffix=" h", field_width=64)
        self.exc_m_spin = StepperSpinBox(minimum=0, maximum=50, step=10,
                                         value=0, suffix=" min", wrap=True,
                                         field_width=72)
        exc_hl.addWidget(self.exc_h_spin)
        exc_hl.addWidget(self.exc_m_spin)
        layout.addWidget(exc_time_w)

        layout.addWidget(QLabel("Razlog  (neobavezno)"))
        self.reason_edit = QLineEdit()
        self.reason_edit.setPlaceholderText("npr. svadba, ispit iz drugog predmeta...")
        layout.addWidget(self.reason_edit)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _accept(self):
        qd = self.date_edit.date()
        d = date(qd.year(), qd.month(), qd.day())
        exc_hours = self.exc_h_spin.value() + self.exc_m_spin.value() / 60
        self.result_data = (d, exc_hours, self.reason_edit.text().strip())
        self.accept()

# ─────────────────────────────────────────────────────────────────────────────
# Glavni prozor
# ─────────────────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Study Planner")
        self.setMinimumSize(QSize(1000, 660))
        self.resize(1200, 740)

        courses, availability, exceptions = load_data()
        self.app_state = {
            "courses":      courses,
            "availability": availability,
            "exceptions":   exceptions,
            "dashboard":    None,
            "plan":         None,
        }
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet(
            f"background-color: {BG_CARD}; border-right: 1px solid {BORDER};")
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(10, 22, 10, 22)
        sl.setSpacing(3)

        logo = QLabel(f"{ICO_BOOK}  Study Planner")
        logo.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {TEXT_PRI}; "
            f"padding: 6px 4px 22px 4px;")
        sl.addWidget(logo)

        self.pages = QStackedWidget()

        dashboard_page    = DashboardPage(self.app_state)
        courses_page      = CoursesPage(self.app_state)
        plan_page         = PlanPage(self.app_state)
        availability_page = AvailabilityPage(self.app_state)

        self.app_state["dashboard"] = dashboard_page
        self.app_state["plan"]      = plan_page

        self.pages.addWidget(dashboard_page)
        self.pages.addWidget(courses_page)
        self.pages.addWidget(plan_page)
        self.pages.addWidget(availability_page)

        nav_items = [
            (f"{ICO_HOME}   Pregled",           0),
            (f"{ICO_COURSES}   Kolegiji",        1),
            (f"{ICO_PLAN}   Plan",               2),
            (f"{ICO_AVAIL}   Mogućnost učenja",  3),
        ]

        self.nav_buttons = []
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("navActive" if idx == 0 else "nav")
            btn.clicked.connect(lambda _, i=idx: self._switch_page(i))
            sl.addWidget(btn)
            self.nav_buttons.append(btn)

        sl.addStretch()
        ver = QLabel("v1.1")
        ver.setStyleSheet(f"font-size: 10px; color: {TEXT_SEC}; padding: 2px 4px;")
        sl.addWidget(ver)

        root.addWidget(sidebar)
        root.addWidget(self.pages, 1)

        dashboard_page.refresh()
        courses_page.refresh()
        plan_page.refresh()

    def _switch_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setObjectName("navActive" if i == index else "nav")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        page = self.pages.currentWidget()
        if hasattr(page, "refresh"):
            page.refresh()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()