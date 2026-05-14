from dataclasses import dataclass, field
from datetime import date


@dataclass
class Responsibility:
    name: str
    task_type: str
    max_points: float
    deadline: date
    task_difficulty: int
    confidence: int
    note: str = ""

    def is_active(self):
        return self.deadline >= date.today()


@dataclass
class Course:
    name: str
    course_difficulty: int
    total_points: float
    responsibilities: list[Responsibility] = field(default_factory=list)

    def add_responsibility(self, responsibility: Responsibility):
        self.responsibilities.append(responsibility)

    def used_points(self):
        return sum(r.max_points for r in self.responsibilities)

    def remaining_points(self):
        return self.total_points - self.used_points()

    def active_responsibilities(self):
        return [
            responsibility
            for responsibility in self.responsibilities
            if responsibility.is_active()
        ]