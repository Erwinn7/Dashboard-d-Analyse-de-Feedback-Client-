import os
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()
client = None

POSITIVE_WORDS = {
    "excellent", "génial", "genial", "parfait", "top", "rapide", "super", "bon",
    "bonne", "ravi", "satisfait", "incroyable", "merci"
}

NEGATIVE_WORDS = {
    "lent", "lente", "bug", "bugs", "retard", "mauvais", "médiocre", "mediocre",
    "furieux", "problème", "probleme", "plante", "écrasé", "ecrase", "cher", "élevé", "eleve"
}

THEME_KEYWORDS = {
    "Livraison": ["livraison", "colis", "retard", "expédition", "expedition", "emballage"],
    "Prix": ["prix", "cher", "élevé", "eleve", "coût", "cout"],
    "Qualité": ["qualité", "qualite", "produit", "emballage", "cassé", "casse"],
    "Service Client": ["service client", "support", "répondu", "repondu", "question"],
    "Application": ["application", "app", "mise à jour", "mise a jour", "bug", "plante", "lent"],
}


def _get_client():
    global client
    if client is not None:
        return client

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    client = OpenAI(api_key=api_key)
    return client


def _normalize_text(text):
    if text is None:
        return ""
    cleaned = str(text).strip().replace("\n", " ")
    return " ".join(cleaned.split())


def _extract_themes_rule_based(text):
    lowered = text.lower()
    themes = []
    for theme, keywords in THEME_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            themes.append(theme)
    return themes[:3]


def _sentiment_from_text(text):
    lowered = text.lower()
    positive_hits = sum(1 for word in POSITIVE_WORDS if word in lowered)
    negative_hits = sum(1 for word in NEGATIVE_WORDS if word in lowered)

    if positive_hits > negative_hits:
        return "Positif"
    if negative_hits > positive_hits:
        return "Négatif"
    return "Neutre"


def _fallback_analysis(text):
    normalized_text = _normalize_text(text)
    if len(normalized_text) < 4:
        return {
            "sentiment_global": "Neutre",
            "analyses": [{"theme": "Général", "sentiment": "Neutre"}]
        }

    themes = _extract_themes_rule_based(normalized_text)
    if not themes:
        themes = ["Général"]

    sentiment_global = _sentiment_from_text(normalized_text)
    analyses = [{"theme": theme, "sentiment": sentiment_global} for theme in themes]

    return {
        "sentiment_global": sentiment_global,
        "analyses": analyses,
    }


def _sanitize_result(result):
    sentiment_global = result.get("sentiment_global", "Neutre")
    if sentiment_global not in {"Positif", "Neutre", "Négatif"}:
        sentiment_global = "Neutre"

    analyses = result.get("analyses", [])
    if not isinstance(analyses, list):
        analyses = []

    sanitized_analyses = []
    for item in analyses:
        if not isinstance(item, dict):
            continue
        theme = str(item.get("theme", "Général")).strip() or "Général"
        sentiment = item.get("sentiment", sentiment_global)
        if sentiment not in {"Positif", "Neutre", "Négatif"}:
            sentiment = sentiment_global
        sanitized_analyses.append({"theme": theme, "sentiment": sentiment})

    if not sanitized_analyses:
        sanitized_analyses = [{"theme": "Général", "sentiment": sentiment_global}]

    return {
        "sentiment_global": sentiment_global,
        "analyses": sanitized_analyses,
    }

def analyze_feedback(text):
    """
    Analyse un feedback client pour extraire le sentiment global, 
    les thèmes abordés et le sentiment par thème.
    """
    
    normalized_text = _normalize_text(text)
    if not normalized_text:
        return {
            "sentiment_global": "Neutre",
            "analyses": [{"theme": "Général", "sentiment": "Neutre"}],
        }

    prompt = f"""
    Analyse le feedback client suivant : "{text}"
    
    Tu dois extraire :
    1. Le sentiment global (Positif, Neutre ou Négatif).
    2. Les thèmes abordés (ex: Livraison, Prix, Qualité, Service Client, Application).
    3. Pour chaque thème, précise si le sentiment est Positif, Neutre ou Négatif.

    Réponds UNIQUEMENT sous forme de JSON avec cette structure :
    {{
        "sentiment_global": "...",
        "analyses": [
            {{"theme": "...", "sentiment": "..."}},
            {{"theme": "...", "sentiment": "..."}}
        ]
    }}
    """

    openai_client = _get_client()
    if openai_client is None:
        return _fallback_analysis(normalized_text)

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini", # Modèle rapide et économique pour un MVP
            messages=[
                {"role": "system", "content": "Tu es un analyste de données expert en satisfaction client."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" } # Force la sortie en JSON
        )

        result = json.loads(response.choices[0].message.content)
        return _sanitize_result(result)
    except Exception as e:
        print(f"Erreur lors de l'analyse : {e}")
        return _fallback_analysis(normalized_text)


def analyze_feedbacks_dataframe(df):
    """
    Analyse un DataFrame contenant la colonne `feedback` et retourne
    les résultats enrichis (sentiment global + thèmes détectés).
    """
    if "feedback" not in df.columns:
        raise ValueError("Le DataFrame doit contenir une colonne 'feedback'.")

    records = []
    for _, row in df.iterrows():
        feedback_text = row.get("feedback", "")
        analysis = analyze_feedback(feedback_text)
        analyses = analysis.get("analyses", [])
        themes = [item.get("theme", "Général") for item in analyses]

        record = row.to_dict()
        record["sentiment_global"] = analysis.get("sentiment_global", "Neutre")
        record["themes"] = ", ".join(themes)
        record["analysis_json"] = json.dumps(analysis, ensure_ascii=False)
        record["analyzed_at"] = datetime.utcnow().isoformat()
        records.append(record)

    return pd.DataFrame(records)

# --- TEST RAPIDE ---
if __name__ == "__main__":
    test_text = "Le produit est génial mais l'application plante souvent."
    result = analyze_feedback(test_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))