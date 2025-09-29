import streamlit as st
import requests
from bs4 import BeautifulSoup

def fetch_fiercebiotech_articles(max_results=5):
    url = "https://www.fiercebiotech.com/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(response.status_code)  # Should be 200
        print(response.text[:1000])  # Preview HTML
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        article_links = soup.select("h2.teaser-title a")[:max_results]

        results = []
        for a in article_links:
            title = a.get_text(strip=True)
            link = a["href"]
            full_url = f"https://www.fiercebiotech.com{link}" if link.startswith("/") else link
            results.append({
                "title": title,
                "summary": "Scraped from FierceBiotech homepage.",
                "source": "FierceBiotech",
                "url": full_url,
                "raw_text": "",
                "timestamp": ""
            })
        return results

    except Exception as e:
        st.error("FierceBiotech scraping failed.")
        st.code(str(e))
        return []
