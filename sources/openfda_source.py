import streamlit as st
import requests
from datetime import datetime, timedelta
import urllib.parse

OPENFDA_BASE_URL = "https://api.fda.gov"

# Predefined queries for different use cases with default values
OPENFDA_QUERIES = {
    "Market Intelligence & Competitive Analysis": [
        {
            "name": "Devices by Product Code",
            "endpoint": "/device/510k.json",
            "query_template": "search=product_code:\"{product_code}\"",
            "parameters": {"product_code": "Enter product code (e.g., KYZ)"},
            "description": "Identify cleared devices by product code",
            "defaults": {"product_code": "KYZ"}
        },
        {
            "name": "Competitor 510(k) Clearances",
            "endpoint": "/device/510k.json",
            "query_template": "search=applicant:\"{competitor_name}\"+AND+decision_date:[{start_date}+TO+{end_date}]",
            "parameters": {
                "competitor_name": "Competitor company name",
                "start_date": "Start date (YYYY-MM-DD)",
                "end_date": "End date (YYYY-MM-DD)"
            },
            "description": "Track a competitor's recent 510(k) clearances",
            "defaults": {
                "competitor_name": "Medtronic",
                "start_date": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d")
            }
        },
        {
            "name": "PMA Approvals by Product Code",
            "endpoint": "/device/pma.json",
            "query_template": "search=product_code:\"{product_code}\"",
            "parameters": {"product_code": "Enter product code"},
            "description": "Identify approved PMA devices by product code",
            "defaults": {"product_code": "LNI"}
        }
    ],
    "Post-Market Surveillance": [
        {
            "name": "Device Adverse Events",
            "endpoint": "/device/event.json",
            "query_template": "search=product_code:\"{product_code}\"+AND+date_received:[{start_date}+TO+{end_date}]",
            "parameters": {
                "product_code": "Product code",
                "start_date": "Start date (YYYY-MM-DD)",
                "end_date": "End date (YYYY-MM-DD)"
            },
            "description": "Monitor adverse events for a device type",
            "defaults": {
                "product_code": "KYZ",
                "start_date": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d")
            }
        },
        {
            "name": "Device Recalls",
            "endpoint": "/device/enforcement.json",
            "query_template": "search=manufacturer_name:\"{company_name}\"",
            "parameters": {"company_name": "Manufacturer name"},
            "description": "Monitor recall actions for a company",
            "defaults": {"company_name": "Philips"}
        }
    ],
    "Regulatory Strategy": [
        {
            "name": "Device Classification",
            "endpoint": "/device/classification.json",
            "query_template": "search=product_code:\"{product_code}\"",
            "parameters": {"product_code": "Product code"},
            "description": "Determine regulatory class and submission type",
            "defaults": {"product_code": "KYZ"}
        },
        {
            "name": "Predicate Device Search",
            "endpoint": "/device/510k.json",
            "query_template": "search=device_name:\"{keyword}\"",
            "parameters": {"keyword": "Device name or keyword"},
            "description": "Find predicate devices for 510(k) drafting",
            "defaults": {"keyword": "laparoscopic"}
        }
    ],
    "Business Development": [
        {
            "name": "Company 510(k) Portfolio",
            "endpoint": "/device/510k.json",
            "query_template": "search=applicant:\"{company_name}\"",
            "parameters": {"company_name": "Company name"},
            "description": "Assess 510(k) portfolio of a company",
            "defaults": {"company_name": "Medtronic"}
        },
        {
            "name": "Company PMA Portfolio",
            "endpoint": "/device/pma.json",
            "query_template": "search=applicant:\"{company_name}\"",
            "parameters": {"company_name": "Company name"},
            "description": "Assess PMA portfolio of a company",
            "defaults": {"company_name": "Boston Scientific"}
        }
    ]
}

def sanitize_company_name(company_name):
    """Sanitize company names for OpenFDA API - handle special characters"""
    # Remove problematic characters and handle common company name variations
    sanitized = company_name.replace('&', 'and').replace('"', '').replace("'", "")
    
    # Handle common company name variations
    variations = {
        'johnson and johnson': 'Johnson+AND+Johnson',
        'johnson & johnson': 'Johnson+AND+Johnson', 
        'boston scientific': 'Boston+Scientific',
        'medtronic': 'Medtronic',
        'philips': 'Philips',
        'siemens': 'Siemens',
        'ge healthcare': 'GE+Healthcare',
        'abbott': 'Abbott'
    }
    
    lower_name = sanitized.lower()
    if lower_name in variations:
        return variations[lower_name]
    
    # For other companies, replace spaces with +
    return sanitized.replace(' ', '+')

def fetch_openfda_data(query_type, query_name, parameters, max_results=10):
    """Fetch data from OpenFDA API based on predefined queries"""
    
    # Find the selected query configuration
    selected_query = None
    for category in OPENFDA_QUERIES.values():
        for query in category:
            if query["name"] == query_name:
                selected_query = query
                break
        if selected_query:
            break
    
    if not selected_query:
        st.error(f"Query configuration not found: {query_name}")
        return []
    
    try:
        # Validate and sanitize parameters
        validated_parameters = {}
        for param_name, param_value in parameters.items():
            if param_value and param_value.strip():  # Only include non-empty parameters
                # Sanitize company names
                if param_name in ['company_name', 'competitor_name']:
                    validated_parameters[param_name] = sanitize_company_name(param_value.strip())
                else:
                    validated_parameters[param_name] = param_value.strip()
            else:
                # Use default if available
                if selected_query.get('defaults') and param_name in selected_query['defaults']:
                    default_value = selected_query['defaults'][param_name]
                    if param_name in ['company_name', 'competitor_name']:
                        validated_parameters[param_name] = sanitize_company_name(default_value)
                    else:
                        validated_parameters[param_name] = default_value
                else:
                    st.warning(f"Parameter '{param_name}' is empty. Using wildcard search.")
                    validated_parameters[param_name] = "*"
        
        # Build the query string
        query_string = selected_query["query_template"].format(**validated_parameters)
        url = f"{OPENFDA_BASE_URL}{selected_query['endpoint']}?{query_string}&limit={max_results}"
        
        st.sidebar.write(f"🔍 OpenFDA Query: {query_name}")
        st.sidebar.write(f"📊 Using parameters: {validated_parameters}")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 404:
            # No results found - try a broader search
            st.warning("No exact matches found. Trying broader search...")
            return try_broader_search(selected_query, validated_parameters, max_results)
            
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("results", []):
            # Extract relevant information based on endpoint
            title = extract_title(item, selected_query["endpoint"])
            summary = extract_summary(item, selected_query["endpoint"])
            
            results.append({
                "title": title,
                "summary": summary,
                "source": f"OpenFDA - {query_name}",
                "url": construct_openfda_url(selected_query["endpoint"], item),
                "raw_text": str(item),
                "timestamp": extract_timestamp(item, selected_query["endpoint"]),
                "metadata": {
                    "endpoint": selected_query["endpoint"],
                    "query_type": query_type,
                    "raw_data": item
                }
            })
        
        if not results:
            st.info("No results found for this query. Try adjusting your search parameters.")
        
        return results
        
    except requests.exceptions.HTTPError as e:
        st.error(f"OpenFDA API request failed: {str(e)}")
        if 'response' in locals():
            try:
                error_data = response.json().get('error', {})
                st.error(f"Error details: {error_data.get('message', 'Unknown error')}")
            except:
                st.error(f"Response text: {response.text}")
        return []
    except Exception as e:
        st.error(f"Unexpected error in OpenFDA API call: {str(e)}")
        return []

def try_broader_search(selected_query, parameters, max_results):
    """Try a broader search when exact match fails"""
    broader_urls = []
    
    if "510k" in selected_query["endpoint"]:
        # Try searching just by company name without date filter
        company_param = parameters.get('company_name') or parameters.get('competitor_name')
        if company_param and company_param != "*":
            broader_url = f"{OPENFDA_BASE_URL}{selected_query['endpoint']}?search=applicant:{company_param}&limit={max_results}"
            broader_urls.append(("Company name only", broader_url))
        
        # Try recent devices
        recent_url = f"{OPENFDA_BASE_URL}{selected_query['endpoint']}?sort=decision_date:desc&limit={max_results}"
        broader_urls.append(("Recent devices", recent_url))
    
    elif "pma" in selected_query["endpoint"]:
        # Try recent PMAs
        recent_url = f"{OPENFDA_BASE_URL}{selected_query['endpoint']}?sort=decision_date:desc&limit={max_results}"
        broader_urls.append(("Recent PMAs", recent_url))
    
    results = []
    for search_type, url in broader_urls:
        try:
            st.sidebar.write(f"Trying {search_type}...")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("results", []):
                    title = extract_title(item, selected_query["endpoint"])
                    summary = extract_summary(item, selected_query["endpoint"])
                    
                    results.append({
                        "title": f"{search_type}: {title}",
                        "summary": summary,
                        "source": f"OpenFDA - {selected_query['name']}",
                        "url": construct_openfda_url(selected_query["endpoint"], item),
                        "raw_text": str(item),
                        "timestamp": extract_timestamp(item, selected_query["endpoint"]),
                        "metadata": {
                            "endpoint": selected_query["endpoint"],
                            "query_type": "Broader Search",
                            "raw_data": item
                        }
                    })
                
                if results:
                    st.success(f"Found {len(results)} results using {search_type}")
                    break
                
        except Exception as e:
            continue
    
    return results

def extract_title(item, endpoint):
    """Extract title based on endpoint type"""
    if "510k" in endpoint:
        device_name = item.get("device_name", "Unnamed 510(k) Device")
        k_number = item.get("k_number", "")
        return f"510(k): {device_name} [{k_number}]" if k_number else f"510(k): {device_name}"
    elif "pma" in endpoint:
        device_name = item.get("device_name", "Unnamed PMA Device")
        pma_number = item.get("pma_number", "")
        return f"PMA: {device_name} [{pma_number}]" if pma_number else f"PMA: {device_name}"
    elif "event" in endpoint:
        return f"Adverse Event: {item.get('product_problem', 'Unknown Problem')}"
    elif "enforcement" in endpoint:
        return f"Recall: {item.get('product_description', 'Unknown Product')}"
    elif "classification" in endpoint:
        return f"Classification: {item.get('device_name', 'Unclassified Device')}"
    else:
        return "OpenFDA Data Result"

def extract_summary(item, endpoint):
    """Extract summary based on endpoint type"""
    if "510k" in endpoint:
        applicant = item.get("applicant", "Unknown")
        decision_date = item.get("decision_date", "Unknown")
        product_code = item.get("product_code", "Unknown")
        return f"Applicant: {applicant} | Decision Date: {decision_date} | Product Code: {product_code}"
    elif "pma" in endpoint:
        applicant = item.get("applicant", "Unknown")
        decision_date = item.get("decision_date", "Unknown")
        product_code = item.get("product_code", "Unknown")
        return f"Applicant: {applicant} | Decision Date: {decision_date} | Product Code: {product_code}"
    elif "event" in endpoint:
        problem = item.get("product_problem", "No problem specified")
        date_received = item.get("date_received", "Unknown date")
        return f"Problem: {problem} | Date Received: {date_received}"
    elif "enforcement" in endpoint:
        reason = item.get("reason_for_recall", "No reason specified")
        recall_date = item.get("recall_initiation_date", "Unknown date")
        return f"Reason: {reason[:150]}... | Recall Date: {recall_date}"
    elif "classification" in endpoint:
        class_type = item.get("device_class", "Unknown")
        regulation = item.get("regulation_number", "Unknown")
        return f"Class: {class_type} | Regulation: {regulation}"
    else:
        return "OpenFDA regulatory data"

def extract_timestamp(item, endpoint):
    """Extract timestamp based on endpoint type"""
    if "510k" in endpoint:
        return item.get("decision_date", "")
    elif "pma" in endpoint:
        return item.get("decision_date", "")
    elif "event" in endpoint:
        return item.get("date_received", "")
    elif "enforcement" in endpoint:
        return item.get("recall_initiation_date", "")
    else:
        return ""

def construct_openfda_url(endpoint, item):
    """Construct a meaningful URL for the OpenFDA data"""
    base_docs_url = "https://open.fda.gov/apis/"
    
    if "510k" in endpoint:
        return "https://open.fda.gov/apis/device/510k/"
    elif "pma" in endpoint:
        return "https://open.fda.gov/apis/device/pma/"
    elif "event" in endpoint:
        return "https://open.fda.gov/apis/device/event/"
    elif "enforcement" in endpoint:
        return "https://open.fda.gov/apis/device/enforcement/"
    elif "classification" in endpoint:
        return "https://open.fda.gov/apis/device/classification/"
    else:
        return "https://open.fda.gov"

def get_openfda_query_categories():
    """Return available OpenFDA query categories"""
    return list(OPENFDA_QUERIES.keys())

def get_queries_for_category(category):
    """Return queries for a specific category"""
    return OPENFDA_QUERIES.get(category, [])