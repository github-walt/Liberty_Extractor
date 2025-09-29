import streamlit as st
from utils.groq_llm import query_groq
from sources.aggregator import aggregate_articles
from sources.openfda_source import get_openfda_query_categories, get_queries_for_category
from datetime import datetime, timedelta

st.set_page_config(page_title="MedTech Insight Extractor", layout="wide")

# Liberty-themed visual styling
st.markdown("""
<style>
    .reportview-container {
        background: linear-gradient(to right, #f4f4f4, #e6f0ff);
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    h1, h2, h3 {
        color: #1a73e8;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton>button {
        background-color: #1a73e8;
        color: white;
        border-radius: 4px;
        padding: 0.5em 1em;
    }
    .stMarkdown {
        font-family: 'Segoe UI', sans-serif;
    }
</style>
""", unsafe_allow_html=True)


# Title and description
st.title("🗽 Liberty Extractor: MedTech Intelligence")
st.markdown("Empowering MedTech professionals with autonomous insight—rooted in Liberty, powered by Groq.")


# Enhanced source options with OpenFDA
source_options = {
    "NewsAPI only": ("newsapi",),
    "ClinicalTrials.gov only": ("clinical_trials",),
    "OpenFDA only": ("openfda",),
    "Aggregate all": ("newsapi", "clinical_trials", "openfda", "medtechdive")
}

with st.sidebar.expander("🧭 Philosophy of Insight"):
    st.markdown("""
    This tool reflects a belief in diagnostic transparency, modular control, and user autonomy.
    Inspired by Liberty Village’s spirit of innovation and Walter van Lieshout’s commitment to clarity.
    """)


selected_source_label = st.sidebar.radio("🧭 Sources to use", list(source_options.keys()))
selected_sources = source_options[selected_source_label]

# OpenFDA query configuration
openfda_params = None
if "openfda" in selected_sources:
    st.sidebar.header("📊 OpenFDA Queries")
    
    # Query category selection
    categories = get_openfda_query_categories()
    selected_category = st.sidebar.selectbox("Query Category", categories)
    
    # Query selection
    queries = get_queries_for_category(selected_category)
    query_names = [q["name"] for q in queries]
    selected_query_name = st.sidebar.selectbox("Query Type", query_names)
    
    # Parameter inputs
    selected_query = next((q for q in queries if q["name"] == selected_query_name), None)
    if selected_query:
        st.sidebar.markdown(f"**Purpose:** {selected_query['description']}")
        
        parameters = {}
        for param_name, param_desc in selected_query.get("parameters", {}).items():
            if "date" in param_name.lower():
                # Date parameters
                default_date = datetime.now() if param_name == "end_date" else datetime.now() - timedelta(days=365)
                parameters[param_name] = st.sidebar.date_input(
                    param_desc, 
                    value=default_date,
                    key=f"openfda_{param_name}"
                ).strftime("%Y-%m-%d")
            else:
                # Text parameters with default values
                default_value = ""
                if selected_query.get('defaults') and param_name in selected_query['defaults']:
                    default_value = selected_query['defaults'][param_name]
                
                parameters[param_name] = st.sidebar.text_input(
                    param_desc, 
                    value=default_value,
                    key=f"openfda_{param_name}",
                    placeholder=f"e.g., {default_value}" if default_value else "Enter value"
                )
        
        # Validate that required parameters are filled
        missing_params = [name for name, value in parameters.items() if not value.strip()]
        if missing_params:
            st.sidebar.warning(f"Please fill in: {', '.join(missing_params)}")
        else:
            openfda_params = {
                "query_type": selected_category,
                "query_name": selected_query_name,
                "parameters": parameters
            }

# Sidebar search
with st.sidebar:
    st.header("🔍 Search Configuration")
    user_query = st.text_input("Enter keyword", value="robotic surgery")
    max_results = st.slider("Max articles per source", 5, 20, 10)
    system_msg = st.text_input("System Prompt", value="Extract key device insights for MedTech sales teams.")
    show_raw = st.checkbox("Show Raw LLM Output", value=False)
    show_debug = st.checkbox("Show Diagnostic Logs", value=False)

# Aggregate articles
try:
    articles = aggregate_articles(
        query=user_query, 
        max_results=max_results, 
        sources=selected_sources,
        openfda_params=openfda_params
    )
    
    if articles:
        titles = [f"{a['title']} ({a['source']})" for a in articles]
        selected_title = st.selectbox("📰 Choose an article", titles)
        
        # Display and extract
        selected_article = next(
            (a for a in articles if f"{a['title']} ({a['source']})" == selected_title),
            None
        )
        
        if selected_article:
            st.markdown(f"### {selected_article['title']}")
            st.markdown(f"**Source:** {selected_article['source']}")
        
            # Enhanced display for OpenFDA data
            if "OpenFDA" in selected_article['source']:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Summary:**")
                    st.info(selected_article["summary"])
                    
                with col2:
                    st.markdown("**Actions:**")
                    if selected_article["url"]:
                        st.markdown(f"[📚 OpenFDA Docs]({selected_article['url']})")
                    
                with st.expander("📋 Detailed Regulatory Data"):
                    st.json(selected_article['metadata']['raw_data'])
                    
                with st.expander("🔍 Raw API Response"):
                    st.code(selected_article['raw_text'])
            
            else:
                # Regular article display
                st.markdown(selected_article["summary"])
                if selected_article["url"]:
                    st.markdown(f"[Read full article]({selected_article['url']})")
            
            if st.button("Extract Insights with Groq"):
                with st.spinner("Querying Groq LLM…"):
                    # Enhanced prompt for OpenFDA data
                    if "OpenFDA" in selected_article['source']:
                        enhanced_prompt = f"""
                        Analyze this regulatory data from OpenFDA and provide insights for MedTech professionals:
                        
                        TITLE: {selected_article['title']}
                        SUMMARY: {selected_article['summary']}
                        
                        RAW REGULATORY DATA:
                        {str(selected_article['metadata']['raw_data'])}
                        
                        Please provide:
                        1. Key regulatory insights
                        2. Potential business implications
                        3. Competitive intelligence
                        4. Any safety or compliance concerns
                        """
                        result = query_groq(enhanced_prompt, system_message=system_msg)
                    else:
                        result = query_groq(selected_article["summary"], system_message=system_msg)
                    
                    if result:
                        st.success("✅ Insight Extracted")
                        st.markdown(result)
                        if show_raw:
                            st.code(result)
        else:
            st.warning("No articles found. Try adjusting your search criteria.")
        
except Exception as e:
    st.error(f"Error aggregating articles: {str(e)}")


# Enhanced diagnostic transparency
if show_debug:
    with st.expander("🧪 Diagnostic Logs"):
        st.markdown("This section surfaces raw inputs and fallback logic.")
        st.code(f"Search Query: {user_query}")
        st.code(f"System Message: {system_msg}")
        st.code(f"Selected Sources: {selected_sources}")
        if openfda_params:
            st.code(f"OpenFDA Parameters: {openfda_params}")
        if articles:
            st.code(f"Total Articles Found: {len(articles)}")
            source_counts = {}
            for a in articles:
                source_counts[a["source"]] = source_counts.get(a["source"], 0) + 1
            st.code(f"Source Breakdown: {source_counts}")