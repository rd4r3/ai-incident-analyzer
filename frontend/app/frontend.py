import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import time

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
st.set_page_config(page_title="AI Incident Analyzer", layout="wide", page_icon="🔍")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #ff6b00;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff6b00;
        margin-bottom: 1rem;
    }
    .plot-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
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
    """Check if API is available with multiple retries"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                return True
        except:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    return False

def call_api(endpoint: str, method: str = "GET", data: dict = None, timeout: int = 30):
    """Generic API call function with better error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
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
        st.error("⏰ API request timed out. The server might be busy or not responding.")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
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

def fetch_incidents():
    """Fetch incidents from backend API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/incidents", timeout=10)
        if response.status_code == 200:
            return response.json().get('results', [])
        return []
    except:
        return []

def create_sample_data():
    """Create sample data for demonstration"""
    return [
        {
            "incident_id": f"INC-{i:05d}",
            "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
            "category": ["Database", "Network", "Application", "Security", "Infrastructure"][i % 5],
            "severity": ["Low", "Medium", "High", "Critical"][i % 4],
            "description": f"Sample incident {i} description",
            "resolution_time_mins": [1, 2, 4, 8, 12, 24][i % 6]
        }
        for i in range(50)
    ]

# Visualization Functions
def create_metrics_row(incidents):
    """Create metrics overview row"""
    if not incidents:
        incidents = create_sample_data()
    
    df = pd.DataFrame(incidents)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Incidents", len(incidents))
    
    with col2:
        if not df.empty and 'severity' in df.columns:
            critical = len(df[df['severity'] == 'Critical'])
            st.metric("Critical Incidents", critical, delta=f"{critical/len(df)*100:.1f}%")
    
    with col3:
        if not df.empty and 'resolution_time_mins' in df.columns:
            mttr = df['resolution_time_mins'].mean()
            st.metric("Mean MTTR", f"{mttr:.1f}m")
    
    with col4:
        if not df.empty and 'category' in df.columns:
            unique_categories = df['category'].nunique()
            st.metric("Categories", unique_categories)

def create_category_distribution(incidents):
    """Create category distribution chart"""
    if not incidents:
        incidents = create_sample_data()
    
    df = pd.DataFrame(incidents)
    
    if df.empty or 'category' not in df.columns:
        return
    
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['Category', 'Count']
    
    fig = px.pie(category_counts, values='Count', names='Category', 
                 title='Incidents by Category', hole=0.4)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False)
    
    st.plotly_chart(fig, use_container_width=True)

def create_severity_timeline(incidents):
    """Create severity timeline chart"""
    if not incidents:
        incidents = create_sample_data()
    
    df = pd.DataFrame(incidents)
    
    if df.empty or 'timestamp' not in df.columns or 'severity' not in df.columns:
        return
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    daily_counts = df.groupby(['date', 'severity']).size().reset_index(name='count')
    
    fig = px.line(daily_counts, x='date', y='count', color='severity',
                  title='Daily Incidents by Severity',
                  labels={'date': 'Date', 'count': 'Number of Incidents', 'severity': 'Severity'})
    
    st.plotly_chart(fig, use_container_width=True)

def create_mttr_by_category(incidents):
    """Create MTTR by category chart"""
    if not incidents:
        incidents = create_sample_data()
    
    df = pd.DataFrame(incidents)
    
    if df.empty or 'category' not in df.columns or 'resolution_time_mins' not in df.columns:
        return
    
    mttr_by_category = df.groupby('category')['resolution_time_mins'].mean().reset_index()
    mttr_by_category.columns = ['Category', 'MTTR_Minutes']
    
    fig = px.bar(mttr_by_category, x='Category', y='MTTR_Minutes',
                 title='Mean Time to Resolution by Category',
                 labels={'MTTR_Minutes': 'MTTR (Minutes)', 'Category': 'Category'})
    fig.update_layout(xaxis_tickangle=-45)
    
    st.plotly_chart(fig, use_container_width=True)

def create_trend_analysis(incidents):
    """Create trend analysis chart"""
    if not incidents:
        incidents = create_sample_data()
    
    df = pd.DataFrame(incidents)
    
    if df.empty or 'timestamp' not in df.columns:
        return
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['week'] = df['timestamp'].dt.isocalendar().week
    df['year'] = df['timestamp'].dt.year
    weekly_trends = df.groupby(['year', 'week']).size().reset_index(name='count')
    weekly_trends['date'] = weekly_trends.apply(lambda x: f"{x['year']}-W{x['week']}", axis=1)
    
    fig = px.line(weekly_trends, x='date', y='count', 
                  title='Weekly Incident Trends',
                  labels={'date': 'Week', 'count': 'Number of Incidents'})
    fig.update_layout(xaxis_tickangle=-45)
    
    st.plotly_chart(fig, use_container_width=True)

def create_heatmap(incidents):
    """Create incident heatmap by day of week and hour"""
    if not incidents:
        incidents = create_sample_data()
    
    df = pd.DataFrame(incidents)
    
    if df.empty or 'timestamp' not in df.columns:
        return
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.day_name()
    df['day_of_week'] = pd.Categorical(df['day_of_week'], 
                                      categories=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                                      ordered=True)
    
    heatmap_data = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
    
    fig = px.density_heatmap(heatmap_data, x='hour', y='day_of_week', z='count',
                            title='Incident Heatmap by Day and Hour',
                            labels={'hour': 'Hour of Day', 'day_of_week': 'Day of Week', 'count': 'Incidents'})
    
    st.plotly_chart(fig, use_container_width=True)

def create_severity_distribution(incidents):
    """Create severity distribution chart"""
    if not incidents:
        incidents = create_sample_data()
    
    df = pd.DataFrame(incidents)
    
    if df.empty or 'severity' not in df.columns:
        return
    
    severity_counts = df['severity'].value_counts().reset_index()
    severity_counts.columns = ['Severity', 'Count']
    
    # Define severity order and colors
    severity_order = ['Critical', 'High', 'Medium', 'Low']
    colors = ['#FF4B4B', '#FF8C4B', '#FFC44B', '#4BAEFF']
    
    fig = px.bar(severity_counts, x='Severity', y='Count', color='Severity',
                 title='Incidents by Severity Level',
                 category_orders={"Severity": severity_order},
                 color_discrete_sequence=colors)
    
    st.plotly_chart(fig, use_container_width=True)

def create_top_incidents_table(incidents):
    """Create table of recent incidents"""
    if not incidents:
        incidents = create_sample_data()
    
    df = pd.DataFrame(incidents)
    
    if df.empty:
        return
    
    # Select and format columns for display
    display_cols = ['incident_id', 'timestamp', 'category', 'severity']
    if all(col in df.columns for col in display_cols):
        recent_incidents = df[display_cols].copy()
        recent_incidents['timestamp'] = pd.to_datetime(recent_incidents['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        recent_incidents = recent_incidents.sort_values('timestamp', ascending=False).head(10)
        
        st.subheader("📋 Recent Incidents")
        st.dataframe(recent_incidents, use_container_width=True, hide_index=True)

# Main Application
def main():
    st.markdown('<h1 class="main-header">🔍 AI Incident Analyzer Dashboard</h1>', unsafe_allow_html=True)
    
    # Check API connection
    api_connected = show_api_status()
    
    if not api_connected:
        st.warning("""
        ⚠️ **API Connection Required**
        
        The frontend cannot connect to the backend API. Please:
        
        1. **Ensure the backend is running**: 
           ```bash
           docker-compose up backend
           # or
           uvicorn app.main:app --reload --port 8000
           ```
        
        2. **Check if ports are available**: 
           - Backend: http://localhost:8000
           - Frontend: http://localhost:8501
        
        3. **Try manual connection test**:
           ```bash
           curl http://localhost:8000/health
           ```
        """)
        
        if st.button("🔄 Retry Connection"):
            st.rerun()
        
        # Show sample data in demo mode
        st.info("📊 Showing sample data in demo mode")
        incidents = create_sample_data()
    else:
        # Fetch real data from API
        incidents = fetch_incidents()
        if not incidents:
            st.info("No incidents found. Showing sample data for demonstration.")
            incidents = create_sample_data()

    # Navigation
    page = st.sidebar.radio("Navigation", ["Dashboard", "Incident Analysis", "Add Incidents", "Statistics"])
    
    if page == "Dashboard":
        show_dashboard(incidents)
    elif page == "Incident Analysis":
        show_analysis_page()
    elif page == "Add Incidents":
        show_add_incidents_page()
    elif page == "Statistics":
        show_statistics_page(incidents)

def show_dashboard(incidents):
    """Show main dashboard with graphs"""
    # Metrics row
    create_metrics_row(incidents)
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Trends", "🔥 Heatmap", "📋 Details"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="plot-container">', unsafe_allow_html=True)
            create_category_distribution(incidents)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="plot-container">', unsafe_allow_html=True)
            create_mttr_by_category(incidents)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="plot-container">', unsafe_allow_html=True)
            create_severity_distribution(incidents)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="plot-container">', unsafe_allow_html=True)
            create_severity_timeline(incidents)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        create_trend_analysis(incidents)
        st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="plot-container">', unsafe_allow_html=True)
            st.write("Weekly Resolution Trends")
            st.info("Additional trend analysis features coming soon!")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="plot-container">', unsafe_allow_html=True)
            st.write("Category Trends Over Time")
            st.info("Category trend visualization in development!")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        create_heatmap(incidents)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("""
        **Heatmap Insights:**
        - Darker colors indicate more incidents
        - Identify peak incident hours
        - Spot patterns by day of week
        """)
    
    with tab4:
        create_top_incidents_table(incidents)
        
        # Additional details
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Performance Metrics")
            if incidents and len(incidents) > 0:
                df = pd.DataFrame(incidents)
                if 'resolution_time_mins' in df.columns:
                    avg_resolution = df['resolution_time_mins'].mean()
                    max_resolution = df['resolution_time_mins'].max()
                    min_resolution = df['resolution_time_mins'].min()
                    
                    st.metric("Average Resolution Time", f"{avg_resolution:.1f} minutes")
                    st.metric("Longest Resolution", f"{max_resolution:.1f} minutes")
                    st.metric("Shortest Resolution", f"{min_resolution:.1f} minutes")
        
        with col2:
            st.subheader("🔍 Analysis Tools")
            if st.button("Run Root Cause Analysis", use_container_width=True):
                st.session_state.page = "Incident Analysis"
                st.rerun()
            if st.button("Generate Pattern Report", use_container_width=True):
                st.session_state.page = "Incident Analysis"
                st.rerun()
            if st.button("Export Incident Data", use_container_width=True):
                st.success("📊 Data export functionality coming soon!")

def show_analysis_page():
    """Show incident analysis page"""
    st.header("Incident Analysis")
    
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
                
                st.success("✅ Analysis completed successfully!")
            else:
                st.error("Analysis failed. Please check if the backend is running properly.")
        else:
            st.warning("Please enter a query")

def show_add_incidents_page():
    """Show add incidents page"""
    st.header("Add New Incidents")
    
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

def show_statistics_page(incidents):
    """Show statistics page"""
    st.header("Statistics")
    
    if not incidents:
        st.warning("No data available for statistics")
        return
    
    # Additional statistics visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Overview")
        df = pd.DataFrame(incidents)
        st.metric("Total Incidents", len(incidents))
        
        if 'severity' in df.columns:
            severity_counts = df['severity'].value_counts()
            st.write("**Severity Distribution:**")
            for severity, count in severity_counts.items():
                st.write(f"- {severity}: {count}")
    
    with col2:
        st.subheader("Actions")
        if st.button("Refresh Statistics"):
            st.rerun()
        
        if st.button("Export Statistics"):
            st.success("📈 Export functionality coming soon!")
    
    # Additional statistics charts
    st.subheader("Advanced Statistics")
    
    if 'timestamp' in df.columns and 'resolution_time_mins' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['week'] = df['timestamp'].dt.isocalendar().week
        
        weekly_stats = df.groupby('week').agg({
            'resolution_time_mins': 'mean',
            'incident_id': 'count'
        }).reset_index()
        
        fig = px.line(weekly_stats, x='week', y='resolution_time_mins',
                     title='Weekly Average Resolution Time',
                     labels={'week': 'Week', 'resolution_time_mins': 'MTTR (Minutes)'})
        st.plotly_chart(fig, use_container_width=True)

# Sidebar with filters and controls
# def setup_sidebar():
#     """Setup sidebar controls"""
#     with st.sidebar:
        # st.header("🎛️ Dashboard Controls")
        
        # # Date filter
        # st.subheader("Date Range")
        # date_range = st.date_input("Select date range:", [])
        
        # # Category filter
        # incidents = fetch_incidents() or create_sample_data()
        # df = pd.DataFrame(incidents)
        # if 'category' in df.columns:
        #     categories = df['category'].unique()
        #     selected_categories = st.multiselect("Categories:", categories, default=categories)
        
        # # Severity filter
        # severity_options = ["Critical", "High", "Medium", "Low"]
        # selected_severity = st.multiselect("Severity:", severity_options, default=severity_options)
        
        # # Refresh button
        # if st.button("🔄 Refresh Data", use_container_width=True):
        #     st.rerun()
        
        # API status
        # st.subheader("🔌 API Status")
        # try:
        #     response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        #     if response.status_code == 200:
        #         st.success("✅ Backend API Connected")
        #     else:
        #         st.error("❌ API Connection Failed")
        # except:
        #     st.error("❌ Cannot connect to API")
        
        # Debug info
        # if st.checkbox("Show Debug Info"):
        #     st.subheader("🐛 Debug Information")
        #     st.write(f"API Base URL: {API_BASE_URL}")
        #     st.write(f"Incidents loaded: {len(incidents)}")

if __name__ == "__main__":
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard"
    
    # Setup sidebar
    # setup_sidebar()
    
    # Run main application
    main()