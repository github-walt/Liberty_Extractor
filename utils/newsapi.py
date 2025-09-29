import streamlit as st
import requests

NEWSAPI_KEY = st.secrets["newsapi"]["api_key"]
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

def fetch_medtech_articles(query="MedTech", max_results=10):
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": max_results,
        "apiKey": NEWSAPI_KEY
    }
    try:
        response = requests.get(NEWSAPI_ENDPOINT, params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return [{"title": a["title"], "description": a["description"], "content": a.get("content", ""), "url": a["url"]} for a in articles]
    except Exception as e:
        st.error("Failed to fetch articles from NewsAPI.")
        st.code(str(e))
        return []
