from .pipeline import IncidentAnalyzer
from typing import List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class IncidentService:
    def __init__(self):
        self.analyzer = IncidentAnalyzer()
    
    def add_incident(self, incident_data: Dict[str, Any]) -> str:
        """Add a single incident"""
        incident_id = incident_data.get('incident_id')
        if not incident_id:
            raise ValueError("Incident ID is required")
        
        success = self.analyzer.ingest_incident(incident_data)
        if success:
            logger.info(f"Added incident {incident_id}")
            return incident_id
        else:
            raise Exception("Failed to add incident")
    
    def add_incidents_batch(self, incidents: List[Dict[str, Any]]) -> int:
        """Add multiple incidents"""
        success_count = 0
        for incident in incidents:
            try:
                self.add_incident(incident)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to add incident: {e}")
        return success_count
    
    def analyze_root_cause(self, query: str, k: int = 5) -> str:
        """Analyze root cause"""
        return self.analyzer.analyze_root_cause(query, k)
    
    def analyze_patterns(self, query: str, k: int = 5) -> str:
        """Analyze patterns"""
        return self.analyzer.analyze_patterns(query, k)
    
    def search_incidents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search incidents and return formatted results"""
        docs = self.analyzer.search_incidents(query, k)
        results = []
        
        for doc in docs:
            results.append({
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata,
                "score": getattr(doc, 'score', None)
            })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        return self.analyzer.get_stats()

    def get_incidents(self) -> List[Dict]:
        """Get incidents"""
        return self.analyzer.get_incidents()