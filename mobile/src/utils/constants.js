export const API_BASE_URL = 'http://localhost:8000'; // Change to your server IP for mobile

export const INCIDENT_CATEGORIES = [
  'Network',
  'Database', 
  'Application',
  'Security',
  'Infrastructure',
  'Other'
];

export const INCIDENT_SEVERITIES = [
  'Low',
  'Medium',
  'High', 
  'Critical'
];

export const ANALYSIS_TYPES = {
  ROOT_CAUSE: 'root_cause',
  PATTERNS: 'patterns',
  SEARCH: 'search'
};

export const COLORS = {
  primary: '#ff6b00', // ING orange
  secondary: '#005aa9', // ING blue
  success: '#28a745',
  danger: '#dc3545',
  warning: '#ffc107',
  info: '#17a2b8',
  light: '#f8f9fa',
  dark: '#343a40',
  white: '#ffffff',
  black: '#000000'
};