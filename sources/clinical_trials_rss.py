import streamlit as st
import feedparser

def fetch_clinical_trials_rss(max_results=5):
    st.sidebar.write("🧪 ClinicalTrials.gov RSS triggered")

    feed_url = "https://clinicaltrials.gov/ct2/results/rss.xml?cond=medical+device&recrs=a"
    feed = feedparser.parse(feed_url)

    if st.sidebar.checkbox("Show RSS Feed Metadata"):
        st.expander("🧾 Feed Metadata").write({
            "Title": feed.feed.get("title", ""),
            "Link": feed.feed.get("link", ""),
            "Description": feed.feed.get("description", ""),
            "Entries": len(feed.entries)
        })

    results = []
    seen_titles = set()

    for entry in feed.entries:
        title = entry.get("title", "").strip()
        summary = entry.get("summary", "").strip()
        link = entry.get("link", "")
        published = entry.get("published", "")

        if title and title not in seen_titles:
            results.append({
                "title": title,
                "summary": summary,
                "source": "ClinicalTrials.gov RSS",
                "url": link,
                "raw_text": "",
                "timestamp": published
            })
            seen_titles.add(title)

        if len(results) >= max_results:
            break

    if st.sidebar.checkbox("Show Matched Titles"):
        st.expander("📰 Matched Titles").write([r["title"] for r in results])

    return results
