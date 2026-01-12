from langchain_core.tools import tool
from src.knowledge.vector_store import query_strategy_rules

@tool
def lookup_strategy_rules(topic: str) -> str:
    """
    Useful for retrieving strategy rules and constraints from the knowledge base.
    Args:
        topic: The specific strategy topic to look up (e.g., 'short strangle management', 'iron condor entry').
    Returns:
        A string containing the top relevant rules found in the documentation.
    """
    results = query_strategy_rules(topic)
    if not results:
        return "No specific rules found for this topic."
    return "\n\n".join(results)
