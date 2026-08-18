from datetime import date, timedelta

try:
    import model_predikcija
except Exception:
    model_predikcija = None

PREFERRED_DAILY   = 3.0   # max sati po obavezi po danu
FOCUS_WINDOW      = 7     # dana prije roka = ekskluzivno učenje
POST_EXAM_BREAK   = 3     # dana odmora nakon kolokvija/ispita
MIN_PARALLEL_GAP  = 7     # min dana razlike da seminar ide paralelno s kolokvijima
PROJECT_WINDOW    = 45    # koliko dana unaprijed početi seminar/projekt
REVIEW_HOURS = {          # sati ponavljanja dan prije roka
    "kolokvij":  2.0,
    "ispit":     3.0,
    "usmeni":    2.0,
    "mini test": 1.0,
}


def calculate_importance_percentage(course, responsibility):
    return (responsibility.max_points / course.total_points) * 100


def calculate_priority(course, responsibility):
    today = date.today()
    days_left = (responsibility.deadline - today).days
    urgency_score = 50 if days_left <= 0 else 30 / days_left
    type_scores = {
        "ispit": 10, "kolokvij": 8, "projekt": 9,
        "seminar": 6, "usmeni": 8, "mini test": 5
    }
    return round(
        course.course_difficulty * 2
        + responsibility.task_difficulty * 2
        + calculate_importance_percentage(course, responsibility) * 0.5
        + urgency_score
        + type_scores.get(responsibility.task_type.lower(), 5)
        + (10 - responsibility.confidence), 2)


def estimate_study_hours(course, responsibility):
    """Procjena sati učenja. Primarno koristi model strojnog učenja;
    ako model nije dostupan, koristi rezervnu formulu (uz upozorenje)."""
    if model_predikcija is not None:
        procjena = model_predikcija.predict_hours(course, responsibility)
        if procjena is not None:
            return procjena
    # Rezerva: formula (upozorenje ispisuje sam modul pri neuspjelom učitavanju)
    return _estimate_formula(course, responsibility)


def _estimate_formula(course, responsibility):
    """Rezervna procjena temeljena na pravilima (kad model nije dostupan)."""
    type_hours = {
        "ispit": 8, "kolokvij": 4, "projekt": 10,
        "seminar": 6, "usmeni": 4, "mini test": 2
    }
    base = type_hours.get(responsibility.task_type.lower(), 4)
    imp  = calculate_importance_percentage(course, responsibility)
    return round(
        base
        + (course.course_difficulty - 1) / 9 * 5
        + (responsibility.task_difficulty - 1) / 9 * 4
        + (10 - responsibility.confidence) / 9 * 4
        + imp * 0.02
        + (course.ects - 6) * 0.3, 1)  # ECTS: neutralno na 6, +0.3h po bodu iznad/ispod


def get_available_hours_for_date(d, availability, exceptions):
    if d in exceptions:
        return exceptions[d]["hours"]
    return availability.get(d.strftime("%A").lower(), 0)


def _make_entry(resp_name, task_type, hours, d, exceptions,
                is_review=False, is_defense=False):
    # Zaokruži na najbližih 10 minuta
    total_min = hours * 60
    rounded_min = round(total_min / 10) * 10
    rounded_h = rounded_min / 60

    return {
        "date": d, "task": resp_name,
        "hours": rounded_h,
        "note": exceptions[d]["reason"] if d in exceptions else "",
        "is_review": is_review, "is_defense": is_defense,
    }


def _study_start(total_hours, deadline, is_project, availability, exceptions,
                 today, created_date=None):
    """
    Izračunaj od kojeg dana treba početi učiti, brojeći unazad od roka.
    Može vratiti datum u prošlosti — ali NIKAD ranije od created_date
    (datuma kad je obaveza unesena). Tako simulacija ne pretpostavlja
    učenje za obavezu koja tada još nije postojala.
    """
    needed  = total_hours * 1.1
    counted = 0.0
    end_day = deadline if is_project else deadline - timedelta(days=2)
    check   = end_day - timedelta(days=1)
    # Donja granica: max 90 dana unazad, ali ne prije nego je obaveza nastala
    limit = today - timedelta(days=90)
    if created_date is not None and created_date > limit:
        limit = created_date

    while check >= limit and counted < needed:
        avail    = get_available_hours_for_date(check, availability, exceptions)
        counted += min(avail, PREFERRED_DAILY) if avail > 0 else 0
        if counted < needed:
            check -= timedelta(days=1)

    return max(check, limit)


def generate_full_plan(courses, availability, exceptions):
    today = date.today()

    # Grupiraj obaveze po predmetu, sortiraj po roku
    course_queues = {}
    all_items     = []

    for c in courses:
        active = sorted(c.active_responsibilities(), key=lambda r: r.deadline)
        queue  = []
        for r in active:
            is_proj = r.is_project_type()
            item = {
                "course":      c,
                "resp":        r,
                "total_hours": estimate_study_hours(c, r),
                "remaining":   estimate_study_hours(c, r),
                "is_project":  is_proj,
                "plan":        [],
                "done":        False,
                "review_done": False,
                "start_day":   None,
            }
            queue.append(item)
            all_items.append(item)
        if queue:
            course_queues[c.name] = queue

    if not all_items:
        return {}, []

    # Pre-izračunaj start_dayeve — mogu biti u prošlosti (simulacija),
    # ali nikad ranije od datuma unosa obaveze (created_date)
    for item in all_items:
        item["start_day"] = _study_start(
            item["total_hours"], item["resp"].deadline,
            item["is_project"], availability, exceptions, today,
            created_date=getattr(item["resp"], "created_date", None))

    # Simulacija počinje od najranijeg start_daya (max 90 dana unazad)
    # Prošli dani se ne prikazuju — samo reduciraju remaining
    sim_start = min(item["start_day"] for item in all_items)
    sim_start = max(sim_start, today - timedelta(days=90))

    max_deadline = max(item["resp"].deadline for item in all_items)
    plan_end     = max_deadline + timedelta(days=1)
    all_days: dict = {}
    warnings       = []
    exam_break: dict = {}  # course_name -> break_end

    current_day = sim_start  # kreće od prošlosti, ne samo od danas
    while current_day < plan_end:
        avail_today = get_available_hours_for_date(current_day, availability, exceptions)
        free_today  = avail_today

        if free_today <= 0:
            current_day += timedelta(days=1)
            continue

        # ── Označi završene obaveze i postavi post-exam break ─────────────────
        for item in all_items:
            r = item["resp"]
            if not item["done"] and current_day >= r.deadline:
                item["done"] = True
                if not item["is_project"]:
                    cn = item["course"].name
                    be = r.deadline + timedelta(days=POST_EXAM_BREAK)
                    if cn not in exam_break or exam_break[cn] < be:
                        exam_break[cn] = be

        # ── Odredi aktivne obaveze ───────────────────────────────────────────
        # Kolokviji/ispiti: sekvencijalni (jedan po jedan po predmetu)
        # Projekti/seminari: neovisni — planiraju se kad nema kolokvijskog blokatora
        active_per_course = {}   # samo kolokviji/ispiti
        active_projects   = []   # svi aktivni projekti/seminari

        for cn, queue in course_queues.items():
            for item in queue:
                if item["done"]:
                    continue

                if not item["is_project"]:
                    # Kolokvij/ispit: sekvencijalno — uzmi SAMO prvog nedovršenog
                    # i dalje ne gledaj ostale kolokvije ovog predmeta
                    if cn not in active_per_course:
                        active_per_course[cn] = item
                    # Nastavi petlju da nađemo projekte iza ovog kolokvija
                else:
                    # Projekt/seminar: dodaj u zasebnu listu ako rok nije prošao
                    r = item["resp"]
                    if current_day < r.deadline:
                        active_projects.append(item)

        # ── Ponavljanje dan prije roka ────────────────────────────────────────
        for item in all_items:  # svi, ne samo active_per_course
            r = item["resp"]
            # Review se planira čak i ako je remaining = 0 (sve naučeno)
            # ali ne ako je rok već prošao ili je projekt
            if item["is_project"] or item["review_done"]:
                continue
            if current_day >= r.deadline:
                continue
            review_day = r.deadline - timedelta(days=1)
            if current_day == review_day and free_today > 0:
                t_type    = r.task_type.lower()
                rev_fixed = REVIEW_HOURS.get(t_type, 2.0)
                # Ne uzimaj više od rev_fixed sati, ali ostavi barem 1h slobodnih
                max_for_review = max(0, min(free_today - 1.0, rev_fixed))
                rev_h = round(max_for_review, 1)
                if rev_h > 0:
                    item["plan"].append(_make_entry(
                        f"{r.name}  —  ponavljanje", r.task_type,
                        rev_h, current_day, exceptions, is_review=True))
                    item["review_done"] = True
                    free_today -= rev_h

        if free_today <= 0:
            current_day += timedelta(days=1)
            continue

        # ── Kolokviji/ispiti — kandidati ──────────────────────────────────────
        exam_candidates = []
        for cn, item in active_per_course.items():
            r = item["resp"]
            # Simulacija ne ide ranije od datuma unosa obaveze
            cd = getattr(r, "created_date", None)
            if cd is not None and current_day < cd:
                continue
            if cn in exam_break and current_day < exam_break[cn]:
                continue
            if item["start_day"] and current_day < item["start_day"]:
                continue
            last_study = r.deadline - timedelta(days=2)
            if current_day > last_study:
                continue
            exam_candidates.append(item)

        # ── Projekti/seminari — kandidati ─────────────────────────────────────
        project_candidates = []
        for item in active_projects:
            r  = item["resp"]
            cn = item["course"].name

            # Simulacija ne ide ranije od datuma unosa obaveze
            cd = getattr(r, "created_date", None)
            if cd is not None and current_day < cd:
                continue

            # Post-exam break za ovaj predmet?
            if cn in exam_break and current_day < exam_break[cn]:
                continue

            last_study = r.deadline - timedelta(days=1)
            if current_day > last_study:
                continue

            # Izračunaj slobodne sate do roka
            free_left = 0.0
            chk = current_day
            while chk < r.deadline:
                a = get_available_hours_for_date(chk, availability, exceptions)
                free_left += min(a, PREFERRED_DAILY) if a > 0 else 0
                chk += timedelta(days=1)

            in_stiska = item["remaining"] > free_left * 0.8

            # Normalan start: 30 dana prije roka
            # Slobodan dan: ako nema NIJEDNOG exam_candidatea danas, iskoristi ga
            # Stiska: počni odmah bez obzira na prozor
            proj_start_normal = r.deadline - timedelta(days=PROJECT_WINDOW)

            no_exams_today = len(exam_candidates) == 0
            if in_stiska:
                # Stiska: počni što ranije (start_day je min potreban)
                actual_start = item["start_day"] or today
            elif no_exams_today:
                # Slobodan dan bez kolokvija: iskoristi ga,
                # ali ne počinjemo prije 30 dana od roka osim ako je stiska
                actual_start = max(proj_start_normal, today)
            else:
                actual_start = max(proj_start_normal, item["start_day"] or today)

            if current_day < actual_start:
                continue

            # Provjeri blokatore:
            # 1. Kolokvij DRUGOG predmeta s bliskim rokom (vanjski blokator)
            # 2. Kolokvij ISTOG predmeta koji je već aktivan (interni blokator)
            external_blocking = [
                ex for ex in exam_candidates
                if ex["course"].name != cn
                and abs((r.deadline - ex["resp"].deadline).days) <= MIN_PARALLEL_GAP
            ]
            # Interni blokator: bilo koji kolokvij istog predmeta koji je aktivan
            # (tj. dostigao start_day ILI je u exam_candidates)
            internal_blocking = any(
                ex["course"].name == cn
                for ex in exam_candidates
            )
            blocked = external_blocking or internal_blocking
            # Dozvoli ako: nije blokiran ILI je stiska
            if not blocked or in_stiska:
                project_candidates.append(item)

        all_candidates = exam_candidates + project_candidates

        if not all_candidates:
            current_day += timedelta(days=1)
            continue

        # ── Rasporedi sate proporcionalno ─────────────────────────────────────
        total_rem = sum(i["remaining"] for i in all_candidates)
        alloc     = {}

        for item in all_candidates:
            r     = item["resp"]
            share = (item["remaining"] / total_rem) * free_today
            days_left = max(1, (r.deadline - current_day).days
                            - (0 if item["is_project"] else 1))
            needed_per_day = item["remaining"] / days_left
            cap   = max(PREFERRED_DAILY, needed_per_day)
            alloc[id(item)] = min(share, cap, item["remaining"])

        total_alloc = sum(alloc.values())
        if total_alloc > free_today:
            scale = free_today / total_alloc
            for k in alloc:
                alloc[k] *= scale

        for item in all_candidates:
            hours = round(alloc[id(item)], 1)
            if hours >= 0.1:
                r = item["resp"]
                item["plan"].append(
                    _make_entry(r.name, r.task_type, hours,
                                current_day, exceptions))
                item["remaining"] -= hours
                if item["remaining"] <= 0.05:
                    item["done"] = True

        current_day += timedelta(days=1)

    # ── Složi all_days ────────────────────────────────────────────────────────
    for item in all_items:
        c = item["course"]
        r = item["resp"]

        for entry in item["plan"]:
            d = entry["date"]
            if d < today:
                continue  # prošli dani: utjecali su na remaining, ne prikazuju se
            if d not in all_days:
                all_days[d] = []

            is_rev = entry["is_review"]
            is_def = entry["is_defense"]

            merged = False
            for existing in all_days[d]:
                if (existing["course"] == c.name
                        and not existing["is_defense"]
                        and not existing.get("is_deadline")):
                    existing["hours"] = round(existing["hours"] + entry["hours"], 1)
                    if is_rev:
                        existing["has_review"] = True
                    if r.name not in existing.get("resp_names", []):
                        existing.setdefault("resp_names", []).append(r.name)
                    merged = True
                    break

            if not merged:
                all_days[d].append({
                    "course":      c.name,
                    "task":        entry["task"],
                    "hours":       entry["hours"],
                    "note":        entry.get("note", ""),
                    "is_review":   is_rev,
                    "is_defense":  is_def,
                    "task_type":   r.task_type,
                    "is_deadline": False,
                    "resp_names":  [r.name],
                    "has_review":  is_rev,
                })

        # Upozorenje — samo ako obaveza nije bila u planu (remaining > 0)
        # i rok joj nije prošao zbog toga što je "done" flagged ranim rokom
        # Provjeri: je li rok prošao BEZ da je isplanirano dovoljno sati
        resp_planned = sum(e["hours"] for e in item["plan"] if not e.get("is_review"))
        if item["remaining"] > 0.1 and resp_planned < item["total_hours"] * 0.5:
            warnings.append({
                "course": c.name,
                "task":   r.name,
                "hours":  round(item["remaining"], 1),
            })

        # Deadline marker
        dl = r.deadline
        if dl >= today:
            if dl not in all_days:
                all_days[dl] = []
            label = (f"Predaja do ponoći  —  {r.name}" if item["is_project"]
                     else f"{c.name}  —  {r.name}")
            all_days[dl].append({
                "course": c.name, "task": label, "hours": 0, "note": "",
                "is_review": False, "is_defense": False,
                "task_type": r.task_type, "is_deadline": True,
            })

        # Obrana marker + priprema dan prije
        if r.has_defense() and r.defense_date >= today:
            dd = r.defense_date

            # Dan prije obrane: "Priprema obrane / prezentacija" 1h
            prep_day = dd - timedelta(days=1)
            if prep_day >= today:
                if prep_day not in all_days:
                    all_days[prep_day] = []
                all_days[prep_day].append({
                    "course": c.name,
                    "task": f"{r.name}  —  priprema obrane",
                    "hours": 1.0, "note": "",
                    "is_review": True, "is_defense": False,
                    "task_type": r.task_type, "is_deadline": False,
                    "resp_names": [r.name], "has_review": True,
                })

            # Sam dan obrane
            if dd not in all_days:
                all_days[dd] = []
            all_days[dd] = [e for e in all_days[dd] if not e.get("is_defense")]
            all_days[dd].append({
                "course": c.name, "task": f"Obrana  —  {r.name}",
                "hours": 0, "note": "", "is_review": False, "is_defense": True,
                "task_type": r.task_type, "is_deadline": False,
            })

    return all_days, warnings


def generate_daily_plan(course, responsibility, availability, exceptions,
                        used_per_day=None):
    all_days, _ = generate_full_plan([course], availability, exceptions)
    result = []
    for entries in all_days.values():
        for e in entries:
            if not e.get("is_deadline") and not e.get("is_defense"):
                result.append(e)
    return sorted(result,
                  key=lambda x: x["date"] if isinstance(x["date"], date) else date.max)