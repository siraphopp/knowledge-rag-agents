from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict):
    query: str
    search_queries: List[str]
    retrieved_snippets: List[str]
    retrieval_details: List[Dict[str, Any]]
    final_report: str
