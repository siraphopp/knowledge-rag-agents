from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.agents.prompts import (
    KB_SUMMARY_SYSTEM_PROMPT,
    REPORTER_SYSTEM_PROMPT,
    RETRIEVER_SYSTEM_PROMPT,
)
from src.config import settings
from src.state import AgentState
from src.tools.retriever_tool import search_knowledge_base


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        streaming=True,
    )


def _get_kb_summary(llm: ChatOpenAI) -> str:
    """Load cached knowledge base summary or generate and save `<kb>.summary.txt` if missing."""
    kb_path = settings.knowledge_base_path
    if not kb_path.exists():
        return "General knowledge base."

    summary_path = kb_path.with_suffix(".summary.txt")
    if (
        summary_path.exists()
        and summary_path.stat().st_mtime >= kb_path.stat().st_mtime
    ):
        return summary_path.read_text(encoding="utf-8").strip()

    raw_text = kb_path.read_text(encoding="utf-8").strip()
    response = llm.invoke(
        [
            SystemMessage(content=KB_SUMMARY_SYSTEM_PROMPT),
            HumanMessage(content=raw_text),
        ]
    )
    summary = response.content.strip()
    summary_path.write_text(summary, encoding="utf-8")
    return summary


def retriever_node(state: AgentState) -> dict:
    """Data Retriever Agent: calls search_knowledge_base tool and returns raw snippets + match details."""
    llm = _get_llm()
    kb_summary = _get_kb_summary(llm)

    llm_with_tools = llm.bind_tools(
        [search_knowledge_base],
        tool_choice="search_knowledge_base",
    )

    response = llm_with_tools.invoke(
        [
            SystemMessage(content=RETRIEVER_SYSTEM_PROMPT.format(kb_summary=kb_summary)),
            HumanMessage(content=state["query"]),
        ]
    )

    search_queries = []
    snippets = []
    retrieval_details = []

    for tool_call in response.tool_calls:
        if tool_call["name"] == "search_knowledge_base":
            q = tool_call["args"].get("query", state["query"])
            search_queries.append(q)
            results = search_knowledge_base.invoke(tool_call["args"])
            for item in results:
                if item["snippet"] not in snippets:
                    snippets.append(item["snippet"])
                    retrieval_details.append(item)

    if not snippets:
        search_queries.append(state["query"])
        results = search_knowledge_base.invoke({"query": state["query"]})
        for item in results:
            snippets.append(item["snippet"])
            retrieval_details.append(item)

    return {
        "search_queries": search_queries,
        "retrieved_snippets": snippets,
        "retrieval_details": retrieval_details,
    }


def report_node(state: AgentState) -> dict:
    """Report Generator Agent: synthesizes retrieved snippets into a polished answer."""
    snippets = state.get("retrieved_snippets", [])
    formatted_snippets = (
        "\n\n".join(f"Snippet {i + 1}:\n{s}" for i, s in enumerate(snippets))
        if snippets
        else "No relevant snippets found."
    )

    user_content = (
        f"User Query:\n{state['query']}\n\n"
        f"Retrieved Knowledge Base Snippets:\n{formatted_snippets}"
    )

    response = _get_llm().invoke(
        [
            SystemMessage(content=REPORTER_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]
    )

    return {"final_report": response.content}
