from langgraph.graph import END, START, StateGraph
from src.agents.nodes import report_node, retriever_node
from src.state import AgentState

workflow = StateGraph(AgentState)

workflow.add_node("retriever", retriever_node)
workflow.add_node("reporter", report_node)

workflow.add_edge(START, "retriever")
workflow.add_edge("retriever", "reporter")
workflow.add_edge("reporter", END)

app = workflow.compile()
