import json
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from openai import OpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

import tools

client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

SYSTEM_PROMPT = (
    "你是文档知识库问答助手。用户的问题通常只存在于知识库中，"
    "回答前你必须先调用 search_knowledge 工具检索知识库，基于检索到的文档内容回答并引用来源；"
    "禁止使用你自己的通用知识作答。只有当检索结果为空时，"
    "才说明'知识库中未找到相关信息'，不要编造。"
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "在私有知识库中检索与问题相关的文档片段",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "检索关键词或问题"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_doc",
            "description": "对指定文档整体生成摘要",
            "parameters": {
                "type": "object",
                "properties": {"doc_name": {"type": "string", "description": "文档文件名"}},
                "required": ["doc_name"],
            },
        },
    },
]


def search_knowledge(query):
    try:
        hits = tools.search(query)
        return "\n".join(hits) if hits else "知识库为空或未检索到相关内容"
    except Exception as e:
        return f"检索失败: {e}"


def summarize_doc(doc_name):
    data = tools.collection.get(where={"source": doc_name}, include=["documents"])
    docs = data.get("documents") or []
    if not docs:
        return f"未找到文档 {doc_name}"
    content = "\n".join(docs[:8])[:3000]
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": f"请对以下文档内容生成300字以内摘要：\n{content}"}],
    )
    return resp.choices[0].message.content


class AgentState(TypedDict):
    messages: list
    steps: int


def call_agent(state):
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=state["messages"],
        tools=TOOLS,
        tool_choice="auto",
    )
    return {"messages": state["messages"] + [resp.choices[0].message.model_dump()], "steps": state["steps"] + 1}


def call_tools(state):
    last = state["messages"][-1]
    results = []
    for tc in last.get("tool_calls", []):
        fn = {"search_knowledge": search_knowledge, "summarize_doc": summarize_doc}[tc["function"]["name"]]
        args = json.loads(tc["function"].get("arguments") or "{}")
        results.append({"role": "tool", "tool_call_id": tc["id"], "content": str(fn(**args))})
    return {"messages": state["messages"] + results}


def route(state):
    if state["steps"] >= 5:
        return "end"
    if state["messages"][-1].get("tool_calls"):
        return "tools"
    return "end"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("agent", call_agent)
    g.add_node("tools", call_tools)
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", route, {"tools": "tools", "end": END})
    g.add_edge("tools", "agent")
    return g.compile()


def ask(query, history=None):
    history = (history or [])[-6:]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": query}]
    result = build_graph().invoke({"messages": messages, "steps": 0})
    return result["messages"][-1]["content"]
