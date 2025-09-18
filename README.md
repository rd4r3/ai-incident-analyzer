# AI Incident Analyzer

An AI-powered RAG pipeline for intelligent banking incident management. Automates root cause analysis, pattern detection, and solution generation using LangChain, Ollama, and ChromaDB.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 🔍 **AI-Powered Analysis**: Automated root cause identification using Ollama LLM
- 📊 **Smart Pattern Detection**: Identify recurring issues and trends across incidents
- 🎯 **Auto-Categorization**: Intelligent incident classification and tagging
- 💡 **Solution Generation**: AI-recommended resolutions based on historical data
- 📈 **Advanced Analytics**: MTTR tracking, severity analysis, frequency reports
- 🌐 **Web Dashboard**: Streamlit interface for real-time monitoring
- 🐳 **Containerized**: Full Docker support for easy deployment

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **AI/ML**: LangChain, Ollama (Llama2), Sentence Transformers
- **Vector Database**: ChromaDB for semantic search
- **Frontend**: Streamlit web application
- **Deployment**: Docker & Docker Compose

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM (for Ollama LLM)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/ai-incident-analyzer.git
cd ai-incident-analyzer

# Create data directory with proper permissions
mkdir -p chroma_data
chmod -R 777 chroma_data

# Start all services
docker-compose up -d --build

# Wait for services to initialize (2-3 minutes)
sleep 120

# Check service status
docker-compose ps
```

### Access Services

- **🌐 Web Dashboard**: http://localhost:8501
- **🔌 API Server**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **🤖 Ollama API**: http://localhost:11434

## 📖 Usage Examples

### Example 1: Adding Incidents

**Via API:**
```bash
# Add a new incident
curl -X POST "http://localhost:8000/api/incidents" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-00123",
    "timestamp": "2024-01-15T10:30:00",
    "category": "Database",
    "severity": "High",
    "description": "Database connection pool exhausted causing application timeouts. Error: ORA-12520: TNS:listener could not find available handler",
    "root_cause": "Connection pool configuration too low for peak load",
    "resolution": "Increased connection pool size from 50 to 200 connections",
    "affected_components": ["Oracle Database", "Application Servers"],
    "impact": "Customers unable to process transactions for 45 minutes"
  }'
```

**Via Web UI:**
1. Open http://localhost:8501
2. Navigate to "Add Incidents" tab
3. Fill in incident details
4. Click "Add Incident"

### Example 2: Root Cause Analysis

**Analyze an incident:**
```bash
curl -X POST "http://localhost:8000/api/analyze/root-cause" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Database connection issues during peak hours",
    "k": 5
  }'
```

**Example Response:**
```json
{
  "success": true,
  "result": "## Root Cause Analysis\n\n1. **Primary Root Cause**: Database connection pool configuration insufficient for peak load periods\n\n2. **Contributing Factors**: \n   - Unexpected traffic spike during business hours\n   - Lack of automatic scaling configuration\n   - Inadequate monitoring alerts\n\n3. **Evidence**: \n   - Similar incidents occurred during previous peak periods\n   - Error logs show ORA-12520 connection pool exhaustion\n   - Monitoring shows CPU and memory within limits\n\n4. **Recommended Solutions**:\n   - Implement dynamic connection pool scaling\n   - Add peak load monitoring and alerts\n   - Conduct load testing for peak scenarios\n\n5. **Preventive Measures**:\n   - Regular capacity planning reviews\n   - Automated scaling policies\n   - Enhanced monitoring with predictive analytics",
  "metadata": {
    "similar_incidents_used": 3,
    "analysis_time": "2.4s"
  }
}
```

### Example 3: Pattern Analysis

**Find patterns across incidents:**
```bash
curl -X POST "http://localhost:8000/api/analyze/patterns" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Network outages in east region datacenter",
    "k": 10
  }'
```

**Example Response:**
```json
{
  "success": true,
  "result": "## Pattern Analysis\n\n**Common Themes**:\n- Network outages occur primarily between 2-4 AM during maintenance windows\n- East region datacenter shows 3x more incidents than other regions\n- 80% of incidents involve router configuration changes\n\n**Frequency Analysis**:\n- Monthly average: 4-6 network incidents\n- Peak occurrence: Q4 2024 (12 incidents)\n- 65% reduction after implementing new change control process\n\n**Seasonal Trends**:\n- Increased incidents during holiday seasons\n- Fewer incidents during summer months\n\n**Recommendations**:\n1. Implement enhanced change validation for network configurations\n2. Schedule critical changes during low-traffic periods\n3. Add redundant network paths in east region",
  "metadata": {
    "time_period_analyzed": "6 months",
    "total_incidents_processed": 47
  }
}
```

### Example 4: Real-time Incident Processing

**Add and analyze immediately:**
```bash
# Add multiple incidents in batch
curl -X POST "http://localhost:8000/api/incidents/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "incident_id": "INC-2024-00124",
      "timestamp": "2024-01-16T14:22:00",
      "category": "Application",
      "severity": "Medium",
      "description": "User authentication service slow response times affecting login functionality"
    },
    {
      "incident_id": "INC-2024-00125", 
      "timestamp": "2024-01-16T15:30:00",
      "category": "Network",
      "severity": "High",
      "description": "VPN connectivity issues for remote employees in European region"
    }
  ]'

# Immediately analyze patterns
curl -X POST "http://localhost:8000/api/analyze/patterns" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Recent authentication and network issues",
    "k": 8
  }'
```

### Example 5: Advanced Search

**Find similar historical incidents:**
```bash
curl -X GET "http://localhost:8000/api/search?query=database%20connection%20timeout&k=5"
```

**Example Response:**
```json
{
  "success": true,
  "results": [
    {
      "incident_id": "INC-2024-00123",
      "similarity_score": 0.92,
      "content": "Database connection pool exhausted causing application timeouts...",
      "metadata": {
        "category": "Database",
        "severity": "High",
        "timestamp": "2024-01-15T10:30:00"
      }
    },
    {
      "incident_id": "INC-2023-04567", 
      "similarity_score": 0.87,
      "content": "Database latency issues during peak trading hours...",
      "metadata": {
        "category": "Database",
        "severity": "Medium", 
        "timestamp": "2023-12-05T09:15:00"
      }
    }
  ],
  "count": 5
}
```

## 🏗️ Project Structure

```
ai-incident-analyzer/
├── backend/
│   ├── Dockerfile          # Backend-specific Dockerfile
│   ├── app/
│   │   ├── main.py         # FastAPI application
│   │   └── __init__.py
│   └── requirements.txt    # Backend dependencies
│
├── frontend/
│   ├── Dockerfile          # Frontend-specific Dockerfile  
│   ├── app/
│   │   └── frontend.py     # Streamlit application
│   │   └── __init__.py           
│   └── requirements.txt    # Frontend dependencies
│
├── docker-compose.yml      # Orchestrates both services
└── README.md
```

## ⚙️ Configuration

### Environment Variables

```env
# Backend Configuration
OLLAMA_HOST=ollama
OLLAMA_PORT=11434
CHROMA_DB_PATH=/app/chroma_data
LOG_LEVEL=INFO

# Frontend Configuration  
API_BASE_URL=http://backend:8000
STREAMLIT_SERVER_PORT=8501

# Ollama Configuration
OLLAMA_MODEL=qwen2:1.5b-instruct-q4_K_M
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/incidents` | POST | Add new incident |
| `/api/incidents/batch` | POST | Add multiple incidents |
| `/api/analyze/root-cause` | POST | Root cause analysis |
| `/api/analyze/patterns` | POST | Pattern analysis |
| `/api/search` | GET | Search similar incidents |
| `/api/health` | GET | Health check |
| `/api/debug/network` | GET | Network diagnostics |

## 🐛 Troubleshooting

### Common Issues

1. **Ollama connection refused**:
   ```bash
   # Check if Ollama is running
   docker-compose logs ollama
   
   # Pull the model manually
   docker-compose exec ollama ollama pull llama2
   ```

2. **ChromaDB permission errors**:
   ```bash
   # Fix directory permissions
   sudo chmod -R 777 chroma_data
   
   # Rebuild containers
   docker-compose down
   docker-compose up -d --build
   ```

3. **Port conflicts**:
   ```bash
   # Check running services
   netstat -tuln | grep -E '(8000|8501|11434)'
   
   # Stop conflicting services or change ports in docker-compose.yml
   ```

### Debug Endpoints

```bash
# Check Ollama connectivity
curl http://localhost:8000/api/health/ollama

# Test network connectivity
curl http://localhost:8000/api/debug/network

# Check container status
curl http://localhost:8000/api/debug/containers
```

## 📊 Example Outputs

### Root Cause Analysis Output
```
## Root Cause Analysis

Primary Root Cause: Database connection pool configuration issues
- Connection pool size insufficient for peak loads
- No automatic scaling implemented

Evidence: 
- ORA-12520 errors in logs during peak hours
- Similar incidents in past 3 months
- CPU/Memory usage normal during incidents

Recommended Solutions:
1. Increase connection pool size from 50 to 200
2. Implement dynamic pool scaling
3. Add connection pool monitoring

Preventive Measures:
- Regular capacity planning reviews
- Load testing before peak seasons
- Automated alerting for pool usage >80%
```

### Pattern Analysis Output
```
## Pattern Analysis Summary

Frequency Patterns:
- 75% of database incidents occur during business hours
- Peak incidents: Monday mornings (34% of total)
- 60% reduction after configuration changes

Common Themes:
- Connection pool exhaustion (45% of database incidents)
- Index fragmentation issues (25%)
- Deadlock situations (20%)

Recommendations:
1. Implement proactive connection pool monitoring
2. Schedule maintenance during low-traffic periods
3. Add automated index maintenance
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-analysis-type`
3. Commit changes: `git commit -am 'Add new analysis feature'`
4. Push to branch: `git push origin feature/new-analysis-type`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For support and questions:
- Open an issue on GitHub
- Check the [API documentation](http://localhost:8000/docs)
- Review troubleshooting section above

---

**Note**: This is a demonstration system for incident analysis. Always validate AI-generated recommendations with domain experts before implementation in production environments.
