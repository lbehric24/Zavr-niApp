# -*- coding: utf-8 -*-
"""
Učitavanje istreniranog modela strojnog učenja i procjena sati učenja za obvezu.

Model je istreniran u bilježnici i spremljen u 'model.pkl'. Ovaj modul ga učitava
jednom pri pokretanju i nudi funkciju predict_hours(course, responsibility) koja
iz podataka obveze složi značajke u isti oblik kao pri treniranju i vrati procjenu.
"""
import os
import numpy as np

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

# Mapiranje tipova obveza iz aplikacije na one-hot stupce modela.
# Ključ je task_type iz aplikacije (mala slova), vrijednost je naziv tip_* stupca.
_TIP_MAP = {
    "ispit":        "tip_Ispit",
    "kolokvij":     "tip_Kolokvij",
    "labos":        "tip_Labos",
    "mini test":    "tip_Mini test",
    "projekt":      "tip_Projekt",
    "seminar":      "tip_Seminar",
    "usmeni":       "tip_Usmeni ispit",
    "usmeni ispit": "tip_Usmeni ispit",
    "zadaće":       "tip_Zadaće",
    "zadace":       "tip_Zadaće",
}

_paket = None          # učitani paket {model, znacajke, log_cilj}
_ucitavanje_pokusano = False


def _ucitaj_model():
    """Učita model.pkl jednom. Vrati paket ili None ako nije dostupan."""
    global _paket, _ucitavanje_pokusano
    if _ucitavanje_pokusano:
        return _paket
    _ucitavanje_pokusano = True
    try:
        import joblib
        _paket = joblib.load(_MODEL_PATH)
    except Exception as e:
        print(f"[UPOZORENJE] Model nije učitan ({e}). "
              f"Koristi se rezervna formula za procjenu sati.")
        _paket = None
    return _paket


def model_dostupan():
    """True ako je model uspješno učitan."""
    return _ucitaj_model() is not None


def predict_hours(course, responsibility):
    """
    Procijeni sate učenja za obvezu pomoću modela.
    Vrati float (sati) ili None ako model nije dostupan (pozivatelj tada
    koristi rezervnu formulu).
    """
    paket = _ucitaj_model()
    if paket is None:
        return None

    model     = paket["model"]
    znacajke  = paket["znacajke"]
    log_cilj  = paket.get("log_cilj", True)

    # --- Složi značajke u isti redoslijed kao pri treniranju ---
    vrijednosti = {z: 0.0 for z in znacajke}

    # Numeričke značajke
    vrijednosti["ects_kolegija"]   = float(getattr(course, "ects", 6) or 6)
    vrijednosti["tezina_kolegija"] = float(course.course_difficulty)
    vrijednosti["tezina_obveze"]   = float(responsibility.task_difficulty)
    vrijednosti["sigurnost_prije"] = float(responsibility.confidence)

    # Postotak ocjene = bodovi obveze / ukupni bodovi kolegija * 100
    if course.total_points and course.total_points > 0:
        vrijednosti["postotak_ocjene"] = (
            responsibility.max_points / course.total_points * 100.0)
    else:
        vrijednosti["postotak_ocjene"] = 0.0

    # Vrsta obveze -> odgovarajući one-hot stupac (ostali ostaju 0)
    tip_stupac = _TIP_MAP.get(responsibility.task_type.lower().strip(), "tip_Ostalo")
    if tip_stupac in vrijednosti:
        vrijednosti[tip_stupac] = 1.0

    # Vektor u točnom redoslijedu značajki (DataFrame s imenima -> bez upozorenja)
    try:
        import pandas as pd
        x = pd.DataFrame([[vrijednosti[z] for z in znacajke]], columns=znacajke)
    except Exception:
        x = np.array([[vrijednosti[z] for z in znacajke]], dtype=float)

    # Predikcija (model radi u log-prostoru -> vrati na sate)
    pred = model.predict(x)[0]
    if log_cilj:
        pred = np.expm1(pred)

    # Zaštita: bez negativnih/besmislenih vrijednosti
    pred = max(0.5, float(pred))
    return round(pred, 1)
