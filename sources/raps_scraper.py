from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import streamlit as st

def fetch_raps_articles(max_results=5):
    st.sidebar.write("🧪 RAPS scraper triggered (Playwright)")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("https://www.raps.org/news-and-articles", timeout=15000)
            page.wait_for_timeout(3000)  # wait for JS to load
            content = page.content()
            browser.close()

        soup = BeautifulSoup(content, "html.parser")
        article_links = soup.select("div.card-title a")[:max_results]

        results = []
        for a in article_links:
            title = a.get_text(strip=True)
            href = a["href"]
            full_url = f"https://www.raps.org{href}" if href.startswith("/") else href
            results.append({
                "title": title,
                "summary": "Scraped from RAPS homepage via Playwright.",
                "source": "RAPS",
                "url": full_url,
                "raw_text": "",
                "timestamp": ""
            })

        if st.sidebar.checkbox("Show Matched Titles"):
            st.expander("📰 Matched Titles").write([r["title"] for r in results])

        return results

    except Exception as e:
        st.error("RAPS Playwright scrape failed.")
        st.code(str(e))
        return []
