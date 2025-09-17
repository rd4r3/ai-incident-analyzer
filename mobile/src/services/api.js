import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.message);
    return Promise.reject(error);
  }
);

// API methods
export const incidentAPI = {
  // Health check
  healthCheck: () => api.get('/health'),
  
  // Add incident
  addIncident: (incidentData) => api.post('/api/incidents', incidentData),
  
  // Add multiple incidents
  addIncidentsBatch: (incidents) => api.post('/api/incidents/batch', incidents),
  
  // Root cause analysis
  analyzeRootCause: (query, k = 5) => 
    api.post('/api/analyze/root-cause', { query, k }),
  
  // Pattern analysis
  analyzePatterns: (query, k = 5) => 
    api.post('/api/analyze/patterns', { query, k }),
  
  // Search incidents
  searchIncidents: (query, k = 5) => 
    api.get(`/api/search?query=${encodeURIComponent(query)}&k=${k}`),
  
  // Get all incidents
  getIncidents: () => api.get('/api/incidents'),
  
  // Get analytics
  getAnalytics: () => api.get('/api/analytics'),
};

export default api;