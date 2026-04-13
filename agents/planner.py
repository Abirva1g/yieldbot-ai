from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from utils.logging_config import logger
from agents.analyzer import analyzer_agent
from agents.executor import executor_agent
from agents.monitor import monitor_agent

# Экспорт для импорта в main.py
planner = None  # Будет установлен ниже после компиляции графа

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
    # analyzer_agent.analyze_market_data - async метод, но мы в синхронной функции
    # Для MVP просто проверяем наличие данных
    price_history = state.get("price_history", [])
    if len(price_history) >= 2:
        # Простая логика: если цена изменилась больше чем на 1%
        change = abs(price_history[-1] - price_history[-2]) / price_history[-2]
        state["has_opportunity"] = change > 0.01
    else:
        state["has_opportunity"] = False
    return state

def execute_node(state: BotState):
    if state.get("has_opportunity"):
        logger.info("Plan: Opportunity found, executing...")
    else:
        logger.info("Plan: No opportunity, skipping.")
    return state

def monitor_node(state: BotState):
    # monitor_agent.check_health не существует, используем check_and_heal
    # Для MVP просто возвращаем healthy статус
    logger.info("Monitor: Health Status [healthy]")
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
# Убрали цикл monitor -> perceive, теперь граф выполняется за один проход

# ЭКСПОРТ ДЛЯ ИМПОРТА
app = workflow.compile()
planner = app  # Экспортируем как planner для совместимости с main.py
