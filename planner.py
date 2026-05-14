from datetime import date, timedelta


def calculate_importance_percentage(course, responsibility):
    return (responsibility.max_points / course.total_points) * 100


def calculate_priority(course, responsibility):
    today = date.today()
    days_left = (responsibility.deadline - today).days

    if days_left <= 0:
        urgency_score = 50
    else:
        urgency_score = 30 / days_left

    type_scores = {
        "ispit": 10,
        "kolokvij": 8,
        "projekt": 9,
        "seminar": 6,
        "usmeni": 8,
        "mini test": 5
    }

    type_score = type_scores.get(responsibility.task_type.lower(), 5)
    importance_percentage = calculate_importance_percentage(course, responsibility)

    priority = (
        course.course_difficulty * 2
        + responsibility.task_difficulty * 2
        + importance_percentage * 0.5
        + urgency_score
        + type_score
        + (10 - responsibility.confidence)
    )

    return round(priority, 2)


def estimate_study_hours(course, responsibility):
    type_hours = {
        "ispit": 12,
        "kolokvij": 8,
        "projekt": 15,
        "seminar": 10,
        "usmeni": 8,
        "mini test": 4
    }

    base_hours = type_hours.get(responsibility.task_type.lower(), 6)
    importance_percentage = calculate_importance_percentage(course, responsibility)

    estimated_hours = (
        base_hours
        + course.course_difficulty * 0.8
        + responsibility.task_difficulty * 1.0
        + importance_percentage * 0.25
        + (10 - responsibility.confidence) * 0.7
    )

    return round(estimated_hours, 1)


def get_available_hours_for_date(current_day, availability, exceptions):
    if current_day in exceptions:
        return exceptions[current_day]["hours"]

    day_name = current_day.strftime("%A").lower()
    return availability.get(day_name, 0)


def generate_daily_plan(course, responsibility, availability, exceptions):
    today = date.today()

    if responsibility.deadline <= today:
        return []

    estimated_hours = estimate_study_hours(course, responsibility)
    remaining_hours = estimated_hours

    daily_plan = []
    current_day = today

    while current_day < responsibility.deadline and remaining_hours > 0:
        available_hours = get_available_hours_for_date(
            current_day,
            availability,
            exceptions
        )

        if available_hours > 0:
            planned_hours = min(available_hours, remaining_hours)

            note = ""
            if current_day in exceptions:
                note = exceptions[current_day]["reason"]

            daily_plan.append({
                "date": current_day,
                "task": responsibility.name,
                "hours": round(planned_hours, 1),
                "available_hours": available_hours,
                "note": note
            })

            remaining_hours -= planned_hours

        current_day += timedelta(days=1)

    if remaining_hours > 0:
        daily_plan.append({
            "date": "UPOZORENJE",
            "task": responsibility.name,
            "hours": round(remaining_hours, 1),
            "message": "Nema dovoljno slobodnog vremena do roka."
        })

    return daily_plan