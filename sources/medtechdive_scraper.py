import streamlit as st
import requests
from bs4 import BeautifulSoup

def fetch_medtechdive_articles(max_results=5):
    url = "https://www.medtechdive.com/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        if st.sidebar.checkbox("Show MedTechDive HTML Preview"):
            st.expander("🔍 Raw HTML Preview").code(soup.prettify()[:1500])


        # Updated selector based on current layout
        article_links = soup.select("a.article-link")[:max_results]

        results = []
        for a in article_links:
            title = a.get_text(strip=True)
            link = a["href"]
            full_url = f"https://www.medtechdive.com{link}" if link.startswith("/") else link
            results.append({
                "title": title,
                "summary": "Scraped from MedTechDive homepage.",
                "source": "MedTechDive",
                "url": full_url,
                "raw_text": "",
                "timestamp": ""
            })
        return results

    except Exception as e:
        st.error("MedTechDive scraping failed.")
        st.code(str(e))
        return []
