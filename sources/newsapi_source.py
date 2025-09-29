import streamlit as st
import requests

NEWSAPI_KEY = st.secrets["newsapi"]["api_key"]
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

def fetch_newsapi_articles(query="MedTech", max_results=10):
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
        return [
            {
                "title": a["title"],
                "summary": a["description"],
                "source": "NewsAPI",
                "url": a["url"],
                "raw_text": a.get("content", ""),
                "timestamp": a.get("publishedAt", "")
            }
            for a in articles
        ]
    except Exception as e:
        st.error("NewsAPI failed.")
        st.code(str(e))
        return []
