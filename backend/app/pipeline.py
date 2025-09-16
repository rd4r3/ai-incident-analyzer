import os
import logging
from typing import List, Dict, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

# Environment variables
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "/app/chroma_data")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral:7b-instruct-v0.3-q4_K_M")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class INGIncidentAnalyzer:
    def __init__(self):
        self.persist_directory = CHROMA_DB_PATH
        self.setup_components()

    def setup_components(self):
        """Initialize LangChain components"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="ing_incidents",
            collection_metadata={"hnsw:space": "cosine"}
        )

        self.llm = Ollama(
            model=LLM_MODEL,
            temperature=0.1,
            base_url=OLLAMA_BASE_URL,
            timeout=1000,
            verbose=True
        )

        self.setup_prompts()
        self.setup_chains()

    def setup_prompts(self):
        """Define prompt templates"""
        self.root_cause_prompt = ChatPromptTemplate.from_template("""
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
            """)

        self.pattern_prompt = ChatPromptTemplate.from_template("""
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
            """)
    
    def setup_chains(self):
        """Setup LangChain chains"""
        self.format_docs = lambda docs: "\n\n".join(doc.page_content for doc in docs)

        def log_prompt(x):
            prompt = self.root_cause_prompt.invoke(x)
            logger.info(f"Prompt sent to Ollama:\n{prompt.to_string()}")
            return x


        self.root_cause_chain = (
            {
                "context": lambda x: self.format_docs(x["context_docs"]),
                "question": lambda x: x["question"]
            }
            | RunnableLambda(log_prompt)
            | self.root_cause_prompt
            | self.llm
            | StrOutputParser()
        )

        self.pattern_chain = (
            {
                "context": lambda x: self.format_docs(x["context_docs"]),
                "question": lambda x: x["question"]
            }
            | RunnableLambda(log_prompt)
            | self.pattern_prompt
            | self.llm
            | StrOutputParser()
        )

    def ingest_incident(self, incident: Dict[str, Any]) -> bool:
        """Add a single incident to vector store"""
            content = f"""
            INCIDENT ID: {incident.get('incident_id')}
            TIMESTAMP: {incident.get('timestamp')}
            CATEGORY: {incident.get('category')}
            SEVERITY: {incident.get('severity')}
            DESCRIPTION: {incident.get('description')}
            ROOT CAUSE: {incident.get('root_cause', 'Not specified')}
            RESOLUTION: {incident.get('resolution', 'Not resolved')}
            IMPACT: {incident.get('impact', 'Not specified')}
            """
        chunks = self.text_splitter.split_text(content)
        documents = []

        for i, chunk in enumerate(chunks):
            documents.append(Document(
                page_content=chunk,
                metadata={
                    "incident_id": incident.get("incident_id"),
                    "timestamp": incident.get("timestamp"),
                    "category": incident.get("category"),
                    "severity": incident.get("severity")
                }
            ))

        if documents:
            self.vectorstore.add_documents(documents)
            return True
        return False

    def search_incidents(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar incidents"""
        results: List[Tuple[Document, float]] = self.vectorstore.similarity_search_with_score(query, k=k)
        # for i, (doc, score) in enumerate(results):
        #     logger.info(f"[{i}] Score: {score:.4f}")
        #     logger.info(f"Content: {doc.page_content[:200]}...")  # Truncate for readability
        #     logger.info(f"Metadata: {doc.metadata}")
        #     logger.info("-" * 40)
        filtered = [doc for doc, score in results if score < 0.5] 
        return filtered

    def analyze_root_cause(self, query: str, k: int = 5) -> str:
        """Perform root cause analysis"""
        logger.info(f"Analyzing root cause for query: {query}")
        docs = self.search_incidents(query, k)
        return self.root_cause_chain.invoke({
            "context_docs": docs,
            "question": query
        })

    def analyze_patterns(self, query: str, k: int = 5) -> str:
        """Analyze patterns across incidents"""
        logger.info(f"Analyzing patterns for query: {query}")
        docs = self.search_incidents(query, k)
        return self.pattern_chain.invoke({
            "context_docs": docs,
            "question": query
        })

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = getattr(self.vectorstore._collection, "count", lambda: 0)()
            return {"total_documents": count}
        except Exception as e:
            logger.warning(f"Failed to get stats: {e}")
            return {"total_documents": 0}

