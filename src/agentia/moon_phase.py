import ephem
import structlog
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

from agentia.models import AgentState
from agentia.llm import get_llm_provider

log = structlog.get_logger()


def _compute_phase_data() -> dict:
    now = ephem.now()
    moon = ephem.Moon(now)

    illumination = round(float(moon.phase), 1)

    prev_new = ephem.previous_new_moon(now)
    next_new = ephem.next_new_moon(now)
    cycle_length = float(next_new - prev_new)
    elapsed = float(now - prev_new)
    fraction = elapsed / cycle_length

    if fraction < 0.025:
        phase_name = "New Moon"
    elif fraction < 0.25:
        phase_name = "Waxing Crescent"
    elif fraction < 0.275:
        phase_name = "First Quarter"
    elif fraction < 0.5:
        phase_name = "Waxing Gibbous"
    elif fraction < 0.525:
        phase_name = "Full Moon"
    elif fraction < 0.75:
        phase_name = "Waning Gibbous"
    elif fraction < 0.775:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    next_full = ephem.next_full_moon(now)
    days_to_new = round(float(next_new - now), 1)
    days_to_full = round(float(next_full - now), 1)

    return {
        "phase_name": phase_name,
        "illumination": illumination,
        "days_to_new_moon": days_to_new,
        "days_to_full_moon": days_to_full,
    }


def calculate_phase_node(state: AgentState) -> dict:
    log.info("node.enter", node="calculate_phase", thread_id=state["thread_id"])
    data = _compute_phase_data()
    log.info("node.exit", node="calculate_phase", thread_id=state["thread_id"], phase=data["phase_name"])
    return {"moon_phase_data": data}


_INTERPRET_SYS = SystemMessage(content=(
    "你是一位融合東西方智慧的引導者，請務必使用『繁體中文』回答。\n"
    "根據提供的月相資訊，依序給出兩段詮釋：\n\n"
    "【道家】引用道家哲學（老子、莊子、陰陽五行）對此月相所象徵的內在狀態與自然規律的解讀。\n"
    "【西方】引用西方天文民俗、詩句或古老傳說對此月相的傳統描述。\n\n"
    "每段約 2–3 句，語氣富有詩意而不過度華麗。"
))


def interpret_phase_node(state: AgentState) -> dict:
    log.info("node.enter", node="interpret_phase", thread_id=state["thread_id"])
    data = state.get("moon_phase_data", {})

    phase_name = data.get("phase_name", "Unknown")
    illumination = data.get("illumination", 0)
    days_to_new = data.get("days_to_new_moon", 0)
    days_to_full = data.get("days_to_full_moon", 0)

    header = (
        f"**{phase_name}** · {illumination}% illuminated\n"
        f"New Moon in {days_to_new} days · Full Moon in {days_to_full} days\n\n"
    )

    user_msg = HumanMessage(content=(
        f"月相：{phase_name}，照明度：{illumination}%，"
        f"距新月 {days_to_new} 天，距滿月 {days_to_full} 天。"
    ))

    llm = get_llm_provider()
    response = llm.invoke([_INTERPRET_SYS, user_msg])

    log.info("node.exit", node="interpret_phase", thread_id=state["thread_id"])
    return {"messages": [AIMessage(content=header + response.content)]}


def build_moon_phase_graph():
    builder = StateGraph(AgentState)
    builder.add_node("calculate_phase", calculate_phase_node)
    builder.add_node("interpret_phase", interpret_phase_node)
    builder.add_edge(START, "calculate_phase")
    builder.add_edge("calculate_phase", "interpret_phase")
    builder.add_edge("interpret_phase", END)
    return builder.compile()
