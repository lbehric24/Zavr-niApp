from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Responsibility:
    name: str
    task_type: str
    max_points: float
    deadline: date
    task_difficulty: int
    confidence: int
    note: str = ""
    # Samo za projekt/seminar: datum obrane (opcionalno)
    defense_date: Optional[date] = None
    # Datum kad je obaveza unesena — simulacija prošlosti ne ide ranije od ovog
    created_date: Optional[date] = None

    def __post_init__(self):
        # Ako nije zadan, smatra se da je obaveza nastala danas
        if self.created_date is None:
            self.created_date = date.today()

    def is_active(self):
        return self.deadline >= date.today()

    def has_defense(self):
        return self.defense_date is not None

    def is_project_type(self):
        return self.task_type.lower() in ("projekt", "seminar")


@dataclass
class Course:
    name: str
    course_difficulty: int
    total_points: float
    ects: int = 6
    responsibilities: list = field(default_factory=list)

    def add_responsibility(self, responsibility: Responsibility):
        self.responsibilities.append(responsibility)

    def used_points(self):
        return sum(r.max_points for r in self.responsibilities)

    def remaining_points(self):
        return self.total_points - self.used_points()

    def active_responsibilities(self):
        return [r for r in self.responsibilities if r.is_active()]