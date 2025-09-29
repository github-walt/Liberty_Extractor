from sources.newsapi_source import fetch_newsapi_articles
from sources.medtechdive_scraper import fetch_medtechdive_articles
from sources.clinical_trials_rss import fetch_clinical_trials_rss
from sources.openfda_source import fetch_openfda_data, get_openfda_query_categories, get_queries_for_category
import streamlit as st

def aggregate_articles(query="MedTech", max_results=10, sources=("newsapi", "fiercebiotech"), openfda_params=None):
    articles = []

    # News sources
    if "newsapi" in sources:
        news_articles = fetch_newsapi_articles(query=query, max_results=max_results)
        articles.extend(news_articles)

    if "clinical_trials" in sources:
        clinical_articles = fetch_clinical_trials_rss(max_results=max_results)
        articles.extend(clinical_articles)

    if "medtechdive" in sources:
        medtech_articles = fetch_medtechdive_articles(max_results=max_results)
        articles.extend(medtech_articles)

    # OpenFDA integration
    if "openfda" in sources and openfda_params:
        openfda_articles = fetch_openfda_data(
            query_type=openfda_params.get("query_type"),
            query_name=openfda_params.get("query_name"),
            parameters=openfda_params.get("parameters", {}),
            max_results=max_results
        )
        articles.extend(openfda_articles)

    # Deduplicate by title
    seen = set()
    deduped = []
    for a in articles:
        if a["title"] not in seen:
            deduped.append(a)
            seen.add(a["title"])

    # Sort by timestamp if available
    deduped.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return deduped