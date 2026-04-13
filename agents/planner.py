from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from utils.logging_config import logger
from agents.analyzer import analyzer_agent
from agents.executor import executor_agent
from agents.monitor import monitor_agent

class BotState(TypedDict):
    price_history: List[float]
    iteration_count: int
    has_opportunity: bool

def perceive_node(state: BotState):
    import random
    new_price = 140.0 + random.uniform(-2, 2)
    state["price_history"].append(new_price)
    if len(state["price_history"]) > 20:
        state["price_history"].pop(0)
    logger.info(f"Perceive: New price ${new_price:.2f}")
    return state

def analyze_node(state: BotState):
    state["has_opportunity"] = analyzer_agent.analyze_market_data(state["price_history"])
    return state

def execute_node(state: BotState):
    if state.get("has_opportunity"):
        logger.info("Plan: Opportunity found, executing...")
    else:
        logger.info("Plan: No opportunity, skipping.")
    return state

def monitor_node(state: BotState):
    status = monitor_agent.check_health()
    logger.info(f"Monitor: Health Status [{status}]")
    state["iteration_count"] += 1
    return state

# Build Graph
workflow = StateGraph(BotState)
workflow.add_node("perceive", perceive_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("execute", execute_node)
workflow.add_node("monitor", monitor_node)

workflow.set_entry_point("perceive")
workflow.add_edge("perceive", "analyze")
workflow.add_edge("analyze", "execute")
workflow.add_edge("execute", "monitor")
workflow.add_edge("monitor", "perceive")

# ЭКСПОРТ ДЛЯ ИМПОРТА
app = workflow.compile()
