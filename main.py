from datetime import datetime, date
from models import Course, Responsibility
from planner import (
    calculate_priority,
    estimate_study_hours,
    calculate_importance_percentage,
    generate_daily_plan
)


def input_int_in_range(message, min_value, max_value):
    while True:
        try:
            value = int(input(message))
            if min_value <= value <= max_value:
                return value
            print(f"Unos mora biti između {min_value} i {max_value}.")
        except ValueError:
            print("Moraš unijeti cijeli broj.")


def input_float_in_range(message, min_value, max_value):
    while True:
        try:
            value = float(input(message))
            if min_value <= value <= max_value:
                return value
            print(f"Unos mora biti između {min_value} i {max_value}.")
        except ValueError:
            print("Moraš unijeti broj.")


def input_date(message):
    while True:
        try:
            deadline_text = input(message)
            return datetime.strptime(deadline_text, "%Y-%m-%d").date()
        except ValueError:
            print("Datum mora biti u formatu YYYY-MM-DD.")


def enter_availability():
    print("\n--- Unos tjedne dostupnosti ---")
    print("Unesi koliko sati možeš učiti po danima.")
    print("Ako neki dan ne možeš učiti, unesi 0.")

    availability = {}

    days = {
        "monday": "Ponedjeljak",
        "tuesday": "Utorak",
        "wednesday": "Srijeda",
        "thursday": "Četvrtak",
        "friday": "Petak",
        "saturday": "Subota",
        "sunday": "Nedjelja"
    }

    for key, name in days.items():
        hours = input_float_in_range(f"{name}: ", 0, 24)
        availability[key] = hours

    return availability


def enter_date_exceptions():
    exceptions = {}

    number_of_exceptions = input_int_in_range(
        "\nKoliko posebnih datuma želiš unijeti? ",
        0,
        100
    )

    for i in range(number_of_exceptions):
        print(f"\nPoseban datum {i + 1}")

        exception_date = input_date("Unesi datum, format YYYY-MM-DD: ")

        hours = input_float_in_range(
            "Koliko sati možeš učiti taj dan? ",
            0,
            24
        )

        reason = input("Razlog/opis, npr. svadba, posao, faks: ")

        exceptions[exception_date] = {
            "hours": hours,
            "reason": reason
        }

    return exceptions


def enter_course():
    course_name = input("\nUnesi naziv kolegija: ")

    course_difficulty = input_int_in_range(
        "Unesi težinu kolegija 1-10: ",
        1,
        10
    )

    total_points = input_float_in_range(
        "Unesi ukupan broj bodova za kolegij: ",
        1,
        1000
    )

    course = Course(course_name, course_difficulty, total_points)

    number_of_responsibilities = input_int_in_range(
        "Koliko obaveza ima kolegij? ",
        1,
        30
    )

    for i in range(number_of_responsibilities):
        print(f"\nObaveza {i + 1}")

        name = input("Naziv obaveze: ")
        task_type = input("Tip obaveze (kolokvij/ispit/projekt/seminar/usmeni/mini test): ")

        remaining_points = course.remaining_points()
        print(f"Preostali bodovi za ovaj kolegij: {remaining_points}")

        max_points = input_float_in_range(
            "Koliko bodova nosi ova obaveza: ",
            0,
            remaining_points
        )

        deadline = input_date("Rok, format YYYY-MM-DD: ")

        if deadline < date.today():
            print("Upozorenje: ova obaveza je već prošla i neće ulaziti u planiranje.")

        task_difficulty = input_int_in_range(
            "Težina obaveze 1-10: ",
            1,
            10
        )

        confidence = input_int_in_range(
            "Samopouzdanje 1-10: ",
            1,
            10
        )

        note = input("Napomena za obavezu, može ostati prazno: ")

        responsibility = Responsibility(
            name=name,
            task_type=task_type,
            max_points=max_points,
            deadline=deadline,
            task_difficulty=task_difficulty,
            confidence=confidence,
            note=note
        )

        course.add_responsibility(responsibility)

    return course


availability = enter_availability()
exceptions = enter_date_exceptions()
course = enter_course()

print("\n--- Uneseni kolegij ---")
print(f"Naziv: {course.name}")
print(f"Težina: {course.course_difficulty}/10")
print(f"Ukupno bodova: {course.total_points}")
print(f"Uneseno bodova: {course.used_points()}")

if course.used_points() < course.total_points:
    print(f"Upozorenje: nije uneseno svih {course.total_points} bodova.")
elif course.used_points() == course.total_points:
    print("Zbroj bodova je točan.")

active_responsibilities = course.active_responsibilities()

sorted_responsibilities = sorted(
    active_responsibilities,
    key=lambda responsibility: calculate_priority(course, responsibility),
    reverse=True
)

print("\n--- Obaveze po prioritetu ---")

if len(sorted_responsibilities) == 0:
    print("Nema aktivnih obaveza za planiranje.")
else:
    for responsibility in sorted_responsibilities:
        priority = calculate_priority(course, responsibility)
        hours = estimate_study_hours(course, responsibility)
        importance = calculate_importance_percentage(course, responsibility)

        print(
            f"{responsibility.name} ({responsibility.task_type}) "
            f"- bodovi: {responsibility.max_points}, "
            f"važnost: {importance:.1f}%, "
            f"prioritet: {priority}, "
            f"predviđeni sati rada: {hours}h"
        )

print("\n--- Sve unesene obaveze ---")

for responsibility in course.responsibilities:
    priority = calculate_priority(course, responsibility)
    hours = estimate_study_hours(course, responsibility)
    importance = calculate_importance_percentage(course, responsibility)

    status = "aktivna"

    if not responsibility.is_active():
        status = "prošla"

    print(
        f"- {responsibility.name}, "
        f"{responsibility.task_type}, "
        f"{responsibility.max_points} bodova, "
        f"važnost: {importance:.1f}%, "
        f"rok: {responsibility.deadline}, "
        f"težina: {responsibility.task_difficulty}/10, "
        f"samopouzdanje: {responsibility.confidence}/10, "
        f"status: {status}, "
        f"prioritet: {priority}, "
        f"sati: {hours}h, "
        f"napomena: {responsibility.note}"
    )

print("\n--- DNEVNI PLAN ---")
print(f"{'Datum':<12} {'Obaveza':<25} {'Sati':<8} {'Napomena'}")
print("-" * 70)

for responsibility in sorted_responsibilities:
    plan = generate_daily_plan(
        course,
        responsibility,
        availability,
        exceptions
    )

    for day in plan:
        if day["date"] == "UPOZORENJE":
            print(
                f"{'UPOZORENJE':<12} "
                f"{day['task']:<25} "
                f"{day['hours']:<8} "
                f"{day['message']}"
            )
        else:
            print(
                f"{str(day['date']):<12} "
                f"{day['task']:<25} "
                f"{day['hours']:<8} "
                f"{day['note']}"
            )