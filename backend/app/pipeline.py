import os
import logging
import re
from typing import List, Dict, Any, Tuple, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from .mistral_chat import ChatMistral
from dotenv import load_dotenv
from .embeddings import TransformersEmbedding
from chromadb.config import Settings

# Constants
DEFAULT_CHROMA_DB_PATH = "/app/chroma_data"
DEFAULT_OLLAMA_BASE_URL = "http://host.docker.internal:11434"
DEFAULT_LLM_MODEL = "mistral:7b-instruct-v0.3-q4_K_M"
DEFAULT_MISTRAL_MODEL = "open-mistral-7b"
SIMILARITY_THRESHOLD = 0.5
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TEMPERATURE = 0.1

# Load environment variables
load_dotenv()

# Environment variables
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", DEFAULT_CHROMA_DB_PATH)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
LLM_MODEL = os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", DEFAULT_MISTRAL_MODEL)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptTemplates:
    """Centralized prompt template management"""

    @staticmethod
    def root_cause_template() -> str:
        return """
        You are an expert incident analyst. Use the following historical incident context to identify the root cause of the current issue.

        Historical Context:
        {context}

        Current Issue:
        {question}

        Please provide a structured analysis with:
        1. Primary Root Cause
        2. Contributing Factors
        3. Evidence
        4. Recommended Solutions
        5. Preventive Measures

        Analysis:
        """

    @staticmethod
    def pattern_template() -> str:
        return """
        You are an expert incident analyst. Use the following historical incident context to identify patterns.

        Historical Context:
        {context}

        Current Issue:
        {question}

        Provide:
        1. Common themes
        2. Frequency patterns
        3. Timeline trends
        4. Severity correlations
        5. Strategic recommendations

        Analysis:
        """

class IncidentAnalyzer:
    def __init__(self):
        self.persist_directory = CHROMA_DB_PATH
        self.text_splitter = self._initialize_text_splitter()
        self.embeddings = self._initialize_embeddings()
        self.vectorstore = self._initialize_vectorstore()
        self.llm = self._initialize_llm()
        self.prompts = self._initialize_prompts()
        self.chains = self._initialize_chains()

    def _initialize_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """Initialize text splitter with configured parameters"""
        return RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

    def _initialize_embeddings(self) -> TransformersEmbedding:
        """Initialize embeddings model"""
        return TransformersEmbedding("thenlper/gte-small")

    def _initialize_vectorstore(self) -> Chroma:
        """Initialize vector store with persistence"""
        client_settings = Settings(
            anonymized_telemetry=False
        )
        return Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="incidents",
            collection_metadata={"hnsw:space": "cosine"},
            client_settings=client_settings
        )

    def _initialize_llm(self):
        """Initialize language model with fallback"""
        try:
            return ChatMistral(
                api_key=MISTRAL_API_KEY,
                model=MISTRAL_MODEL,
                temperature=TEMPERATURE
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ChatMistral: {e}")
            return Ollama(
                model=LLM_MODEL,
                temperature=TEMPERATURE,
                base_url=OLLAMA_BASE_URL,
                timeout=1000,
                verbose=True
            )

    def _initialize_prompts(self) -> Dict[str, ChatPromptTemplate]:
        """Initialize prompt templates"""
        return {
            "root_cause": ChatPromptTemplate.from_template(PromptTemplates.root_cause_template()),
            "pattern": ChatPromptTemplate.from_template(PromptTemplates.pattern_template())
        }

    def _initialize_chains(self) -> Dict[str, Any]:
        """Initialize analysis chains"""
        def log_prompt(x: Dict[str, Any]) -> Dict[str, Any]:
            """Log prompt before sending to LLM"""
            prompt = self.prompts["root_cause"].invoke(x)
            logger.info(f"Prompt sent to LLM:\n{prompt.to_string()}")
            return x

        def create_chain(prompt_template: ChatPromptTemplate) -> Any:
            """Factory method for creating analysis chains"""
            return (
                {
                    "context": lambda x: self._format_docs(x["context_docs"]),
                    "question": lambda x: x["question"]
                }
                | RunnableLambda(log_prompt)
                | prompt_template
                | self.llm
                | StrOutputParser()
            )

        return {
            "root_cause": create_chain(self.prompts["root_cause"]),
            "pattern": create_chain(self.prompts["pattern"])
        }

    def _format_docs(self, docs: List[Document]) -> str:
        """Format documents for prompt context"""
        return "\n\n".join(doc.page_content for doc in docs)

    def parse_incident_string(self, doc: str) -> Dict[str, str]:
        """Parse incident string into structured data"""
        pattern = r"(?P<key>[A-Z _]+): (?P<value>.+)"
        incident = {}
        for line in doc.split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                key = match.group("key").strip().lower().replace(" ", "_")
                value = match.group("value").strip()
                incident[key] = value
        return incident

    def ingest_incident(self, incident: Dict[str, Any]) -> bool:
        """Add a single incident to vector store"""
        try:
            content = f"""
                INCIDENT ID: {incident.get('incident_id')}
                TIMESTAMP: {incident.get('timestamp')}
                CATEGORY: {incident.get('category')}
                SEVERITY: {incident.get('severity')}
                DESCRIPTION: {incident.get('description')}
                ROOT CAUSE: {incident.get('root_cause', 'Not specified')}
                RESOLUTION: {incident.get('resolution', 'Not resolved')}
                IMPACT: {incident.get('impact', 'Not specified')}
                RESOLUTION TIME MINS: {incident.get('resolution_time_mins')}
                """
            chunks = self.text_splitter.split_text(content)
            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        "incident_id": incident.get("incident_id"),
                        "timestamp": incident.get("timestamp"),
                        "category": incident.get("category"),
                        "severity": incident.get("severity")
                    }
                )
                for i, chunk in enumerate(chunks)
            ]

            if documents:
                self.vectorstore.add_documents(documents)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to ingest incident: {e}")
            return False

    def search_incidents(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar incidents with similarity filtering"""
        try:
            results: List[Tuple[Document, float]] = self.vectorstore.similarity_search_with_score(query, k=k)
            return [doc for doc, score in results if score < SIMILARITY_THRESHOLD]
        except Exception as e:
            logger.error(f"Failed to search incidents: {e}")
            return []

    def analyze_root_cause(self, query: str, k: int = 5) -> str:
        """Perform root cause analysis"""
        try:
            logger.info(f"Analyzing root cause for query: {query}")
            docs = self.search_incidents(query, k)
            return self.chains["root_cause"].invoke({
                "context_docs": docs,
                "question": query
            })
        except Exception as e:
            logger.error(f"Failed to analyze root cause: {e}")
            return ""

    def analyze_patterns(self, query: str, k: int = 5) -> str:
        """Analyze patterns across incidents"""
        try:
            logger.info(f"Analyzing patterns for query: {query}")
            docs = self.search_incidents(query, k)
            return self.chains["pattern"].invoke({
                "context_docs": docs,
                "question": query
            })
        except Exception as e:
            logger.error(f"Failed to analyze patterns: {e}")
            return ""

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = getattr(self.vectorstore._collection, "count", lambda: 0)()
            return {"total_documents": count}
        except Exception as e:
            logger.warning(f"Failed to get stats: {e}")
            return {"total_documents": 0}

    def get_incidents(self) -> List[Dict[str, str]]:
        """Get all incidents from vector store"""
        try:
            raw_docs = self.vectorstore.get()["documents"]
            return [self.parse_incident_string(doc) for doc in raw_docs]
        except Exception as e:
            logger.error(f"Failed to get incidents: {e}")
            return []
