# 📓 Journal de Bord : Session 1
**Date :** 03 Mars 2026  
**Objectif :** Initialisation du projet et Moteur d'Analyse IA  

---

## I- Objectif de la session
Mettre en place l'environnement de travail, créer un jeu de données de test (CSV) et réussir à faire analyser un feedback par l'IA (Sentiment + Thèmes) avec un format de sortie structuré (JSON).

## II- Étapes réalisées

### 1. Configuration de l'environnement
Mise en place de l'arborescence du projet et des fichiers de base :
* `app.py` : Le fichier principal **Streamlit**.
* `requirements.txt` : Dépendances (`streamlit`, `openai`, `pandas`, `python-dotenv`).
* `.env` : Stockage sécurisé de la clé API OpenAI.

### 2. Création des données de test
Génération d'un fichier `test_feedbacks.csv` incluant des cas variés pour tester la robustesse de l'IA :
* Un client ravi (Positif).
* Un client furieux sur la livraison (Négatif).
* Un avis mitigé (Neutre/Mixte).

### 3. Le "Cœur" de l'IA (Le Prompt Système)
Développement de la logique d'extraction de données. L'objectif est de transformer du texte brut en données structurées exploitables par le dashboard.

**Prompt utilisé pour la fonction d'analyse :**
> "Agis en tant qu'expert en analyse de données. Écris une fonction Python `analyze_feedback(text)` qui utilise l'API OpenAI. Pour chaque texte, l'IA doit extraire :
> 1. Le sentiment global (Positif, Neutre, Négatif).
> 2. Une liste de thèmes (ex: 'Livraison', 'Prix', 'Qualité Produit').
> 3. Pour chaque thème, un sentiment spécifique.
> 
> **Contrainte :** La réponse doit être un JSON strict pour insertion dans un DataFrame Pandas."

---

## III- Problèmes rencontrés & Solutions

| Problème | Solution |
| :--- | :--- |
| **Pollution du JSON** : L'IA ajoutait du texte inutile ("Voici l'analyse...") avant le bloc JSON, faisant crasher Python. | Utilisation du paramètre `response_format={ "type": "json_object" }` dans l'appel API pour forcer un format pur. |
| **Coût et Latence** : L'analyse individuelle (1 par 1) est lente pour de gros volumes de données. | **Piste future** : Implémenter un traitement par "batch" (paquets de 10 feedbacks) pour optimiser les appels. |

---

## IV-  Ce que j'ai appris
La puissance des **Structured Outputs**. En forçant l'IA à répondre dans un format informatique (JSON) plutôt qu'en langage naturel, on transforme un outil de chat en un véritable moteur de base de données fiable et prévisible.

---
**Prochaine étape :** Création de l'interface Streamlit et affichage des premiers graphiques (Session 2).

---

# 📓 Journal de Bord : Session 2
**Date :** 17 Mars 2026  
**Objectif :** Créer le MVP du dashboard Streamlit avec persistance et vues agrégées.

## I- Objectif de la session
Transformer le moteur d'analyse IA en application exploitable : import de feedbacks, analyse en lot, sauvegarde persistante, visualisation des tendances clés.

## II- Étapes réalisées

### 1. Interface Streamlit (MVP)
Création de `app.py` avec :
* Import de feedbacks via CSV.
* Saisie manuelle de feedbacks (1 ligne = 1 avis).
* Bouton unique `Analyser et ajouter`.

### 2. Persistance des données
Ajout d'un stockage local `analyses_store.csv` :
* Conservation des analyses entre les sessions.
* Colonnes stockées : date, client, feedback, sentiment global, thèmes, JSON complet, date d'analyse.

### 3. Vues analytiques livrées
Le dashboard affiche maintenant :
* Répartition des sentiments (bar chart).
* Répartition des thèmes.
* Sentiment par thème (tableau agrégé).
* Top 3 feedbacks positifs et top 3 négatifs.
* Historique complet des analyses.

### 4. Robustesse du moteur d'analyse
Amélioration de `analyzer.py` :
* Validation/sanitation des sorties JSON.
* Gestion des textes très courts et des cas simples (ex: emojis) via fallback local.
* Analyse en lot via `analyze_feedbacks_dataframe(df)`.

## III- Livrables de la session
* `app.py`
* `requirements.txt`
* `.gitignore`
* `analyzer.py` (version robuste)

## IV- Prochaine étape
Ajouter la vue d'évolution temporelle (sentiment par semaine) et les alertes de pic négatif par thème.
