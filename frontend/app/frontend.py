import streamlit as st
import requests
import json
import os
from datetime import datetime
import time

# API configuration - Updated for Docker and local environments
# API_BASE_URL = "http://localhost:8000"  # For local development
# API_BASE_URL = "http://backend:8000"  # For Docker compose
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


st.set_page_config(
    page_title="AI Incident Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #ff6b00;
        text-align: center;
        margin-bottom: 2rem;
    }
    .analysis-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .incident-card {
        border-left: 4px solid #ff6b00;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: white;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def check_api_health():
    """Check if API is available with retries"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=15)
            if response.status_code == 200:
                return True
        except (requests.ConnectionError, requests.Timeout):
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retrying
                continue
    return False

def call_api(endpoint: str, method: str = "GET", data: dict = None, timeout: int = 300):
    """Generic API call function with better error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return None
            
    except requests.ConnectionError:
        st.error("🚫 Cannot connect to the API server. Please make sure the backend is running.")
        return None
    except requests.Timeout:
        st.error("⏰ API request timed out. The server might be busy.")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        return None

def show_api_status():
    """Show API connection status"""
    if check_api_health():
        st.sidebar.success("✅ API Connected")
        return True
    else:
        st.sidebar.error("❌ API Disconnected")
        st.sidebar.info("Please start the backend server: `uvicorn app.main:app --reload`")
        return False

def main():
    st.markdown('<h1 class="main-header">🔍 AI Incident Analyzer</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to", ["Dashboard", "Incident Analysis", "Add Incidents", "Statistics"])
        
        st.header("API Status")
        api_connected = show_api_status()
        
        if not api_connected:
            st.warning("Some features may not work without API connection")
    
    # Dashboard Page
    if page == "Dashboard":
        st.header("Dashboard")
        
        if not api_connected:
            st.warning("Please connect to the API to view dashboard data")
            return
            
        col1, col2, col3 = st.columns(3)
        
        stats = call_api("/api/incidents/stats")
        if stats and stats.get('success'):
            col1.metric("Total Incidents", stats['stats'].get('total_documents', 0))
            col2.metric("Knowledge Chunks", stats['stats'].get('total_chunks', 0))
            col3.metric("API Status", "Online" if stats['success'] else "Offline")
        
        st.subheader("Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        if col1.button("🔍 Analyze Patterns"):
            st.session_state.page = "Incident Analysis"
            st.rerun()
        
        if col2.button("➕ Add Incident"):
            st.session_state.page = "Add Incidents"
            st.rerun()
        
        if col3.button("📊 View Stats"):
            st.session_state.page = "Statistics"
            st.rerun()
    
    # Incident Analysis Page
    elif page == "Incident Analysis":
        st.header("Incident Analysis")
        
        if not api_connected:
            st.warning("API connection required for analysis")
            return
            
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Root Cause Analysis", "Pattern Analysis", "General Search"]
        )
        
        query = st.text_area(
            "Describe the incident or ask a question:",
            placeholder="e.g., Database connection issues during peak hours...",
            height=100
        )
        
        k = st.slider("Number of similar incidents to consider:", 1, 10, 5)
        
        if st.button("Run Analysis", type="primary"):
            if query:
                with st.spinner("Analyzing..."):
                    if analysis_type == "Root Cause Analysis":
                        result = call_api("/api/analyze/root-cause", "POST", 
                                        {"query": query, "k": k})
                    elif analysis_type == "Pattern Analysis":
                        result = call_api("/api/analyze/patterns", "POST", 
                                        {"query": query, "k": k})
                    else:
                        result = call_api(f"/api/search?query={query}&k={k}")
                
                if result and result.get('success'):
                    st.subheader("Analysis Results")
                    st.markdown("---")
                    
                    if analysis_type == "General Search":
                        st.write(f"Found {len(result['results'])} similar incidents:")
                        for res in result['results']:
                            with st.expander(f"Incident: {res['metadata'].get('incident_id', 'Unknown')}"):
                                st.write(f"**Category**: {res['metadata'].get('category', 'Unknown')}")
                                st.write(f"**Severity**: {res['metadata'].get('severity', 'Unknown')}")
                                st.write(f"**Content**: {res['content']}")
                    else:
                        st.markdown(result['result'])
                
                else:
                    st.error("Analysis failed. Please check if the backend is running properly.")
            else:
                st.warning("Please enter a query")
    
    # Add Incidents Page
    elif page == "Add Incidents":
        st.header("Add New Incidents")
        
        if not api_connected:
            st.warning("API connection required to add incidents")
            return
            
        tab1, tab2 = st.tabs(["Single Incident", "Batch Upload"])
        
        with tab1:
            with st.form("single_incident_form"):
                col1, col2 = st.columns(2)
                incident_id = col1.text_input("Incident ID*")
                timestamp = col2.text_input("Timestamp", value=datetime.now().isoformat())
                
                col1, col2 = st.columns(2)
                category = col1.selectbox("Category*", ["Network", "Database", "Application", "Security", "Infrastructure"])
                severity = col2.selectbox("Severity*", ["Low", "Medium", "High", "Critical"])
                
                description = st.text_area("Description*", height=100)
                root_cause = st.text_input("Root Cause (optional)")
                resolution = st.text_input("Resolution (optional)")
                
                if st.form_submit_button("Add Incident"):
                    if incident_id and category and severity and description:
                        incident_data = {
                            "incident_id": incident_id,
                            "timestamp": timestamp,
                            "category": category,
                            "severity": severity,
                            "description": description,
                            "root_cause": root_cause,
                            "resolution": resolution
                        }
                        
                        result = call_api("/api/incidents", "POST", incident_data)
                        if result and result.get('success'):
                            st.success(f"✅ Incident {incident_id} added successfully!")
                        else:
                            st.error("❌ Failed to add incident")
                    else:
                        st.warning("⚠️ Please fill required fields (*)")
        
        with tab2:
            st.subheader("Upload JSON File")
            uploaded_file = st.file_uploader("Choose a JSON file", type="json")
            
            if uploaded_file:
                try:
                    incidents = json.load(uploaded_file)
                    if not isinstance(incidents, list):
                        incidents = [incidents]
                    
                    if st.button("Upload Incidents"):
                        result = call_api("/api/incidents/batch", "POST", incidents)
                        if result and result.get('success'):
                            st.success(f"✅ Uploaded {result['processed_count']} incidents successfully!")
                        else:
                            st.error("❌ Upload failed")
                
                except json.JSONDecodeError:
                    st.error("Invalid JSON file")
    
    # Statistics Page
    elif page == "Statistics":
        st.header("Statistics")
        
        if not api_connected:
            st.warning("API connection required to view statistics")
            return
            
        stats = call_api("/api/incidents/stats")
        if stats and stats.get('success'):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Overview")
                st.metric("Total Documents", stats['stats'].get('total_documents', 0))
                
            with col2:
                st.subheader("Actions")
                if st.button("Refresh Statistics"):
                    st.rerun()
        
        # Recent activity
        st.subheader("Recent Activity")
        st.info("Statistics and visualization features will be implemented here.")

if __name__ == "__main__":
    main()