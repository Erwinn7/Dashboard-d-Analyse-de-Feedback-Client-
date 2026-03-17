import io
import os
import pandas as pd
import streamlit as st

from analyzer import analyze_feedback, analyze_feedbacks_dataframe

DATA_PATH = "analyses_store.csv"
REQUIRED_COLUMNS = ["date", "client_name", "feedback"]


def load_store(path=DATA_PATH):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=REQUIRED_COLUMNS + ["sentiment_global", "themes", "analysis_json", "analyzed_at"])


def save_store(df, path=DATA_PATH):
    df.to_csv(path, index=False)


def normalize_input_df(df):
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes: {', '.join(missing)}")

    clean_df = df[REQUIRED_COLUMNS].copy()
    clean_df["date"] = pd.to_datetime(clean_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    clean_df["client_name"] = clean_df["client_name"].fillna("Inconnu").astype(str).str.strip()
    clean_df["feedback"] = clean_df["feedback"].fillna("").astype(str).str.strip()
    clean_df = clean_df[clean_df["feedback"] != ""]
    return clean_df


def get_theme_stats(df):
    exploded = (
        df.assign(theme=df["themes"].fillna("").str.split(",\s*"))
        .explode("theme")
    )
    exploded["theme"] = exploded["theme"].fillna("Général").replace("", "Général")

    theme_distribution = exploded.groupby("theme").size().sort_values(ascending=False)
    sentiment_by_theme = (
        exploded.groupby(["theme", "sentiment_global"]) 
        .size()
        .unstack(fill_value=0)
    )
    return theme_distribution, sentiment_by_theme


def top_examples(df, sentiment, top_n=3):
    subset = df[df["sentiment_global"] == sentiment].copy()
    if subset.empty:
        return subset
    subset["feedback_len"] = subset["feedback"].str.len()
    subset = subset.sort_values(by="feedback_len", ascending=False).head(top_n)
    return subset[["date", "client_name", "feedback", "themes"]]


def parse_manual_input(raw_text):
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    records = []
    for idx, line in enumerate(lines, start=1):
        records.append(
            {
                "date": pd.Timestamp.today().strftime("%Y-%m-%d"),
                "client_name": f"Client_{idx}",
                "feedback": line,
            }
        )
    return pd.DataFrame(records)


st.set_page_config(page_title="Dashboard Feedback Client", layout="wide")
st.title("Dashboard d'analyse de feedback client")
st.caption("MVP: import, analyse IA, persistance et vues agrégées")

store_df = load_store()

with st.sidebar:
    st.header("Import")
    uploaded_file = st.file_uploader("Importer un CSV", type=["csv"])
    manual_feedbacks = st.text_area(
        "Ou coller des feedbacks (1 ligne = 1 feedback)",
        height=180,
        placeholder="Exemple:\nLivraison trop lente 😕\nProduit top, merci !",
    )

    run_analysis = st.button("Analyser et ajouter")

new_df = pd.DataFrame()
if uploaded_file is not None:
    new_df = pd.read_csv(uploaded_file)
elif manual_feedbacks.strip():
    new_df = parse_manual_input(manual_feedbacks)

if run_analysis:
    if new_df.empty:
        st.warning("Ajoute un CSV ou du texte avant de lancer l'analyse.")
    else:
        try:
            normalized = normalize_input_df(new_df)
            with st.spinner("Analyse des feedbacks en cours..."):
                analyzed_df = analyze_feedbacks_dataframe(normalized)

            merged = pd.concat([store_df, analyzed_df], ignore_index=True)
            save_store(merged)
            store_df = merged
            st.success(f"{len(analyzed_df)} feedback(s) analysé(s) et sauvegardé(s).")
        except Exception as exc:
            st.error(f"Erreur: {exc}")

col1, col2, col3 = st.columns(3)
col1.metric("Nombre de feedbacks", len(store_df))
col2.metric("Positifs", int((store_df["sentiment_global"] == "Positif").sum()) if not store_df.empty else 0)
col3.metric("Négatifs", int((store_df["sentiment_global"] == "Négatif").sum()) if not store_df.empty else 0)

if not store_df.empty:
    st.subheader("Répartition des sentiments")
    sentiment_counts = store_df["sentiment_global"].value_counts()
    st.bar_chart(sentiment_counts)

    st.subheader("Répartition des thèmes")
    theme_distribution, sentiment_by_theme = get_theme_stats(store_df)
    st.bar_chart(theme_distribution)

    st.subheader("Sentiment par thème")
    st.dataframe(sentiment_by_theme)

    st.subheader("Top 3 positifs")
    top_pos = top_examples(store_df, "Positif", top_n=3)
    if top_pos.empty:
        st.info("Pas encore de feedback positif.")
    else:
        st.dataframe(top_pos, use_container_width=True)

    st.subheader("Top 3 négatifs")
    top_neg = top_examples(store_df, "Négatif", top_n=3)
    if top_neg.empty:
        st.info("Pas encore de feedback négatif.")
    else:
        st.dataframe(top_neg, use_container_width=True)

    st.subheader("Historique des analyses")
    st.dataframe(store_df.sort_values(by="date", ascending=False), use_container_width=True)
else:
    st.info("Aucune donnée persistée pour le moment. Importe un CSV ou colle des feedbacks puis clique sur 'Analyser et ajouter'.")

st.divider()
st.caption("Astuce: si la clé OPENAI_API_KEY est absente, une analyse locale de secours est utilisée pour rester opérationnel.")
