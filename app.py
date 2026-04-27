import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Y-Market Predictor", layout="wide")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #041428, #0b2d4d);
        color: #E6E6E6;
    }

    p, span, div {
        color: #E6E6E6 !important;
        font-size: 15px;
    }

    h1 { color: #FFD700 !important; font-weight: 800 !important; }
    h2, h3 { color: #00FA9A !important; }

    label {
        color: #F1F1F1 !important;
        font-weight: 500;
    }

    [data-testid="stMetricValue"] {
        color: #FFD700 !important;
        font-size: 22px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Y-MARKET PREDICTOR : Smart Data Yaoundé")

# =========================
# SUPABASE
# =========================
@st.cache_resource
def init_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )

supabase = init_supabase()

# =========================
# DATA
# =========================
@st.cache_data
def load_data():
    res = supabase.table("prix_marche").select("*").execute()
    df = pd.DataFrame(res.data)

    df["prix"] = pd.to_numeric(df["prix"], errors="coerce")
    df["pluie"] = pd.to_numeric(df["pluie"], errors="coerce")

    return df.dropna()

df = load_data()

# =========================
# ML MODEL
# =========================
@st.cache_resource
def train_model(df):
    X = df[["marche", "produit", "saison", "pluie"]]
    y = df["prix"]

    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["marche", "produit", "saison"]),
        ("num", "passthrough", ["pluie"])
    ])

    model = Pipeline([
        ("prep", preprocessor),
        ("reg", LinearRegression())
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)

    return model, score

model, score = train_model(df)

# =========================
# INTERPRETATION
# =========================
def interpretation(df, col):
    grouped = df.groupby(col)["prix"].mean()

    if grouped.empty:
        return "📊 Données insuffisantes."

    return f"""
    🧠 **Analyse automatique :**

    - 🔺 Plus élevé : **{grouped.idxmax()}**
    - 🔻 Plus bas : **{grouped.idxmin()}**

    👉 Forte variation selon {col}.
    """

# =========================
# TABS
# =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏠 Accueil",
    "📊 Analyse",
    "📈 Vue Globale",
    "🤖 Modèle",
    "🔮 Prédiction",
    "➕ Collecte",
    "🗂 Données"
])

with tab1:
    st.markdown("""
### 📌 Présentation

Cette application vous permet de **collecter et analyser les données des marchés** afin de les transformer en informations exploitables.  
Elle aide à mieux comprendre l’évolution des prix et à anticiper les tendances du marché local.

L’objectif est de faciliter la **prise de décision basée sur les données**, aussi bien pour l’analyse économique que pour la compréhension des dynamiques des marchés.
""")

    st.metric("Données disponibles", len(df))
    st.metric("Marchés analysés", df["marche"].nunique())
    st.metric("Prix moyen", f"{df['prix'].mean():.0f} FCFA")
# TAB 2 - ANALYSE
# =========================
with tab2:
    prod = st.selectbox("Produit", df["produit"].unique(), key="an_prod")

    dff = df[df["produit"] == prod]

    fig = px.bar(
        dff.groupby("marche")["prix"].mean().reset_index(),
        x="marche",
        y="prix"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(interpretation(dff, "marche"))

# =========================
# TAB 3 - GLOBAL
# =========================
with tab3:
    fig1 = px.bar(
        df.groupby("marche")["prix"].mean().reset_index(),
        x="prix",
        y="marche",
        orientation="h"
    )

    st.plotly_chart(fig1, use_container_width=True)
    st.markdown(interpretation(df, "marche"))

    fig2 = px.bar(
        df.groupby("produit")["prix"].mean().reset_index(),
        x="prix",
        y="produit",
        orientation="h"
    )

    st.plotly_chart(fig2, use_container_width=True)
    st.markdown(interpretation(df, "produit"))

# =========================
# TAB 4 - MODELE
# =========================
with tab4:
    st.metric("Score R²", f"{score:.2f}")
    st.info("Le score mesure la performance du modèle de régression.")

# =========================
# TAB 5 - PREDICTION
# =========================
with tab5:
    m = st.selectbox("Marché", df["marche"].unique(), key="p_m")
    p = st.selectbox("Produit", df["produit"].unique(), key="p_p")
    s = st.selectbox("Saison", df["saison"].unique(), key="p_s")
    pl = st.radio("Pluie", [0, 1], format_func=lambda x: "Oui" if x else "Non", key="p_pl")

    if st.button("Prédire"):
        pred = model.predict(pd.DataFrame([{
            "marche": m,
            "produit": p,
            "saison": s,
            "pluie": pl
        }]))[0]

        st.success(f"💰 Prix estimé : {pred:.0f} FCFA")

# =========================
# TAB 6 - FORMULAIRE
# =========================
with tab6:
    st.subheader("➕ Ajouter une donnée")

    with st.form("form"):
        marche = st.text_input("Marché")
        produit = st.text_input("Produit")
        saison = st.selectbox("Saison", ["Sèche", "Pluvieuse"], key="f_s")
        pluie = st.radio("Pluie", [0, 1], format_func=lambda x: "Oui" if x else "Non", key="f_p")
        prix = st.number_input("Prix", min_value=0)

        submit = st.form_submit_button("Enregistrer")

        if submit:
            supabase.table("prix_marche").insert({
                "marche": marche,
                "produit": produit,
                "saison": saison,
                "pluie": pluie,
                "prix": prix
            }).execute()

            st.success("Donnée ajoutée ✅")
            st.cache_data.clear()

# =========================
# TAB 7 - DATA
# =========================
with tab7:
    st.subheader("🗂 Données")

    st.dataframe(df, use_container_width=True)

    st.download_button(
        "📥 Télécharger",
        df.to_csv(index=False),
        "data.csv",
        "text/csv"
    )

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown("""
<div style="
    text-align: right;
    color: #FFD700;
    font-style: italic;
    font-size: 14px;
    opacity: 0.85;
    margin-top: 20px;
">
    Projet réalisé par <b>DONGMO TCHUDZO CHRISTELLE NIQUOIZE</b><br>
    dans le cadre de l’UE INF232 EC2
</div>
""", unsafe_allow_html=True)