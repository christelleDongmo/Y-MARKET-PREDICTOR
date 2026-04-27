import random
from datetime import datetime, timedelta
from supabase import create_client, Client

# =========================
# CONNEXION SUPABASE
# =========================
url = "https://jpezxmzlulouipntyfhs.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpwZXp4bXpsdWxvdWlwbnR5ZmhzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxMzc2OTQsImV4cCI6MjA5MjcxMzY5NH0.LBo_WtDCCct16RV6xeMo07cj-MEvqh1tgcFPjgvQquQ"
supabase: Client = create_client(url, key)

# =========================
# DONNEES DE BASE
# =========================

marches = {
    "Central": 120,
    "Etoudi": 100,
    "Mfoundi": 70,
    "Mokolo": 40,
    "Mvogbi": 30
}

produits = {
    "tomate": 100,
    "piment": 120,
    "oignon": 150,
    "riz": 200,
    "poisson": 250
}

# =========================
# LOGIQUE METIER
# =========================

def effet_saison(produit, saison):
    if saison == "pluie":
        if produit in ["tomate", "piment"]:
            return -30
        else:
            return 40
    else:
        if produit in ["tomate", "piment"]:
            return 30
        else:
            return -20

def effet_pluie_marche(marche, pluie):
    if pluie == 1:
        if marche in ["Central", "Mfoundi", "Mvogbi"]:
            return 25
        else:
            return 10
    return 0

# =========================
# GENERATION DONNEES
# =========================

data = []

start_date = datetime(2026, 4, 1)

for i in range(60):

    date = start_date + timedelta(days=i % 20)

    marche = random.choice(list(marches.keys()))
    produit = random.choice(list(produits.keys()))

    saison = random.choice(["pluie", "sèche"])
    pluie = 1 if saison == "pluie" else 0

    prix_base = marches[marche] + produits[produit]

    prix = (
        prix_base
        + effet_saison(produit, saison)
        + effet_pluie_marche(marche, pluie)
        + random.randint(-40, 60)
    )

    if prix < 50:
        prix = 50

    data.append({
        "date": str(date.date()),
        "marche": marche,
        "produit": produit,
        "prix": round(prix),
        "saison": saison,
        "pluie": pluie
    })

# =========================
# INSERTION SUPABASE
# =========================

for row in data:
    supabase.table("prix_marche").insert(row).execute()

print("✅ 60 enregistrements insérés avec succès")