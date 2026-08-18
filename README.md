# SmartPlanner — inteligentni sustav za planiranje učenja

SmartPlanner je stolna (desktop) aplikacija koja studentima automatski generira
personalizirani raspored učenja. Na temelju unesenih kolegija, obveza i tjedne
dostupnosti aplikacija procjenjuje potrebno vrijeme učenja za svaku obvezu i
raspoređuje ga kroz dostupne dane, poštujući rokove i dnevno opterećenje.

Procjena vremena temelji se na **modelu strojnog učenja** naučenom na podacima o
stvarnom vremenu učenja prikupljenima anketom među studentima. Umjesto da od
korisnika traži procjenu trajanja, aplikacija je sama predviđa.

Aplikacija je izrađena kao završni rad na Fakultetu organizacije i informatike
(smjer Informatički i poslovni sustavi).

## Značajke

- Unos kolegija i obveza (kolokviji, ispiti, projekti, seminari, mini testovi i dr.)
- Automatska procjena potrebnog vremena učenja pomoću modela strojnog učenja
- Generiranje tjednog rasporeda uz poštivanje rokova i dnevne dostupnosti
- Razlikovanje sekvencijalnih (kolokviji, ispiti) i paralelnih (projekti, seminari) obveza
- Postavljanje tjedne dostupnosti i iznimaka za pojedine datume
- Pregled obveza poredanih po prioritetu
- Lokalna pohrana podataka (bez interneta i vanjskog poslužitelja)

## Tehnologije

- **Python 3**
- **PyQt6** — grafičko korisničko sučelje
- **scikit-learn** — model strojnog učenja (Gradient Boosting)
- **pandas**, **numpy** — priprema i obrada podataka
- **joblib** — učitavanje spremljenog modela

## Struktura projekta

```
├── app.py                  # glavna aplikacija i korisničko sučelje (PyQt6)
├── models.py               # razredi Course i Responsibility
├── planner.py              # logika procjene vremena i raspoređivanja
├── model_predikcija.py     # učitavanje modela i predviđanje sati
├── model.pkl               # istrenirani model strojnog učenja
├── Analiza_podataka.ipynb  # priprema i analiza podataka
├── Model.ipynb             # izrada i vrednovanje modela
└── anketa_long.csv         # prikupljeni podaci (anketa)
```

## Pokretanje

### 1. Preduvjeti

Potreban je Python 3 (preporučeno 3.10 ili noviji).

### 2. Instalacija potrebnih biblioteka

```bash
pip install PyQt6 scikit-learn pandas numpy joblib
```

### 3. Pokretanje aplikacije

```bash
python app.py
```

Aplikacija pri pokretanju učitava `model.pkl` za procjenu vremena. Ako datoteka
modela nije dostupna, aplikacija koristi rezervnu procjenu temeljenu na pravilima
i o tome ispisuje obavijest u konzoli.

## Model strojnog učenja

Model predviđa broj sati učenja na temelju šest značajki poznatih korisniku pri
unosu obveze: broj ECTS bodova kolegija, težina kolegija, udio bodova obveze,
vrsta obveze, težina obveze i procjena samopouzdanja.

Postupak izrade modela dokumentiran je u bilježnicama:

- `Analiza_podataka.ipynb` — čišćenje, analiza i priprema podataka
- `Model.ipynb` — usporedba modela, optimizacija i vrednovanje

Za pošteno vrednovanje korištena je **grupna unakrsna validacija (GroupKFold)** po
ispitaniku, čime se sprječava curenje informacija jer je svaki ispitanik unio više
obveza.

### Ponovno treniranje modela

Ako se podaci (`anketa_long.csv`) izmijene, model se može ponovno istrenirati
pokretanjem bilježnica redom: najprije `Analiza_podataka.ipynb` (koja priprema
podatke), zatim `Model.ipynb` (koja trenira i sprema novi `model.pkl`). Novi
`model.pkl` potom treba kopirati u mapu aplikacije.

## Napomena

Prikupljanje podataka za model još je u tijeku, osobito za obveze manjeg opsega
(mini testovi, zadaće), pa se točnost procjena za tu skupinu obveza dodatnim
podacima može poboljšati.

## Autorica

Lorena Behrić
