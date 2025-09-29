import streamlit as st
import requests
import time

GROQ_API_KEY = st.secrets["groq"]["api_key"]
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

def query_groq(prompt, system_message=None, max_retries=3):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt  # Exponential backoff
                st.warning(f"Rate limit hit. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                st.error("Groq API request failed.")
                st.code(f"Status: {response.status_code}\nError: {e}\nResponse: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            st.error("Groq API request timed out.")
            return None
            
        except Exception as e:
            st.error("Unexpected error in Groq API call.")
            st.code(str(e))
            return None

    st.error("Max retries exceeded for Groq API.")
    return None