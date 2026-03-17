import os
import io
import pandas as pd
import streamlit as st
import plotly.express as px

from analyzer import analyze_feedbacks_dataframe

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


def build_sentiment_trend(df):
    score_map = {"Positif": 1, "Neutre": 0, "Négatif": -1}
    trend_df = df.copy()
    trend_df["date"] = pd.to_datetime(trend_df["date"], errors="coerce")
    trend_df = trend_df.dropna(subset=["date"])
    trend_df["sentiment_score"] = trend_df["sentiment_global"].map(score_map).fillna(0)
    trend_df = (
        trend_df.groupby("date", as_index=False)["sentiment_score"]
        .mean()
        .sort_values("date")
    )
    return trend_df


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


def build_sample_csv():
    sample_df = pd.DataFrame(
        [
            {"date": "2026-03-01", "client_name": "Alice", "feedback": "Livraison rapide et produit excellent."},
            {"date": "2026-03-02", "client_name": "Bob", "feedback": "Application correcte, mais quelques lenteurs."},
            {"date": "2026-03-03", "client_name": "Charlie", "feedback": "Service client lent et colis abîmé."},
        ]
    )
    buffer = io.StringIO()
    sample_df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def build_pie_figure(dataframe, names_col, values_col, title, hole=0.38):
    pulls = []
    total = float(dataframe[values_col].sum()) if len(dataframe) else 0.0
    for value in dataframe[values_col].tolist():
        ratio = (float(value) / total) if total > 0 else 0
        pulls.append(0.05 if ratio >= 0.2 else 0.03)

    fig = px.pie(
        dataframe,
        names=names_col,
        values=values_col,
        title=title,
        hole=hole,
    )
    fig.update_traces(
        sort=False,
        pull=pulls,
        marker=dict(line=dict(color="#ffffff", width=2)),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=55, l=10, r=10, b=10),
    )
    return fig


st.set_page_config(page_title="Dashboard Feedback Client", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f6f8fb;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e7ebf3;
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }
    .kpi-label {
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 4px;
    }
    .kpi-value {
        color: #0f172a;
        font-size: 1.65rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .section-title {
        color: #0f172a;
        font-weight: 600;
        margin-top: 0.3rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Dashboard d'analyse de feedback client")
st.caption("Interface claire • camemberts • courbe d'évolution")

store_df = load_store()
new_df = pd.DataFrame()

with st.sidebar:
    st.header("Import des données")
    st.caption("Charge un fichier CSV au format: date, client_name, feedback")

    st.download_button(
        label="Télécharger un template CSV",
        data=build_sample_csv(),
        file_name="template_feedbacks.csv",
        mime="text/csv",
        use_container_width=True,
    )

    uploaded_file = st.file_uploader(
        "Glisse-dépose ton CSV",
        type=["csv"],
        help="Colonnes obligatoires: date, client_name, feedback",
    )

    if uploaded_file is not None:
        try:
            csv_df = pd.read_csv(uploaded_file)
            new_df = csv_df.copy()
            st.success(f"{len(csv_df)} ligne(s) détectée(s).")
            st.caption("Aperçu (5 premières lignes)")
            st.dataframe(csv_df.head(5), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"CSV invalide: {exc}")

    with st.expander("Ou saisie manuelle"):
        manual_feedbacks = st.text_area(
            "1 ligne = 1 feedback",
            height=140,
            placeholder="Exemple:\nLivraison trop lente 😕\nProduit top, merci !",
        )
        if manual_feedbacks.strip() and uploaded_file is None:
            new_df = parse_manual_input(manual_feedbacks)
            st.info(f"{len(new_df)} feedback(s) prêt(s) à analyser.")

    run_analysis = st.button("Analyser et ajouter", type="primary", use_container_width=True)

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

total_feedbacks = len(store_df)
total_positive = int((store_df["sentiment_global"] == "Positif").sum()) if not store_df.empty else 0
total_negative = int((store_df["sentiment_global"] == "Négatif").sum()) if not store_df.empty else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Nombre de feedbacks</div>
            <div class="kpi-value">{total_feedbacks}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Positifs</div>
            <div class="kpi-value">{total_positive}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Négatifs</div>
            <div class="kpi-value">{total_negative}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if not store_df.empty:
    theme_distribution, sentiment_by_theme = get_theme_stats(store_df)

    with st.spinner("Chargement des graphiques..."):
        sentiment_counts = store_df["sentiment_global"].value_counts().rename_axis("sentiment").reset_index(name="count")
        theme_counts = theme_distribution.rename_axis("theme").reset_index(name="count")
        trend_data = build_sentiment_trend(store_df)

        fig_trend = px.line(
            trend_data,
            x="date",
            y="sentiment_score",
            markers=True,
            title="Évolution du sentiment moyen par jour",
        )
        fig_trend.update_yaxes(range=[-1, 1])

    st.markdown('<div class="section-title">Vue globale</div>', unsafe_allow_html=True)
    col_left, col_right = st.columns(2)
    with col_left:
        fig_sentiment = build_pie_figure(
            sentiment_counts,
            names_col="sentiment",
            values_col="count",
            title="Répartition des sentiments",
        )
        st.plotly_chart(fig_sentiment, use_container_width=True)
    with col_right:
        fig_themes = build_pie_figure(
            theme_counts,
            names_col="theme",
            values_col="count",
            title="Répartition des thèmes",
        )
        st.plotly_chart(fig_themes, use_container_width=True)

    st.markdown('<div class="section-title">Tendance temporelle</div>', unsafe_allow_html=True)
    st.plotly_chart(fig_trend, use_container_width=True)

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
