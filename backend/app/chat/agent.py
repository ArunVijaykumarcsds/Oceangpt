"""
OceanGPT conversational agent.

Flow for each user turn:
  1. Retrieve relevant knowledge-base chunks via the vector store (RAG),
     using local sentence-transformer embeddings (no API cost).
  2. Send the user's message + retrieved context + conversation history to
     Groq's free-tier, OpenAI-compatible chat completions API, with
     live-data tools available via function calling.
  3. If the model requests a tool call (e.g. "get current wave height at
     these coordinates"), execute it against the real API and feed the
     result back to the model.
  4. Loop until the model produces a final text answer.
  5. Collect every piece of evidence used (RAG docs + tool results) as
     `SourceRef`s so the frontend can show the user where the answer came from.
"""

import json
import logging

from openai import AsyncOpenAI

from app.config import get_settings
from app.models import ChatMessage, SourceRef
from app.rag.store import vector_store
from app.tools.registry import TOOL_SCHEMAS, dispatch_tool_call

logger = logging.getLogger("oceangpt.agent")
settings = get_settings()
_client = AsyncOpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)

SYSTEM_PROMPT = """You are OceanGPT, a marine science assistant for an ocean intelligence dashboard.

You have two ways to ground your answers in real information:
1. RETRIEVED CONTEXT - factual reference snippets about species and oceanography concepts, provided below each user message. Use these for general/background knowledge questions.
2. LIVE TOOLS - real-time and near-real-time data from OBIS (species occurrence records), WoRMS (taxonomy), NOAA CO-OPS (US tide stations), and Open-Meteo Marine (global wave/sea-temperature data). Use these whenever the user asks about current conditions, real observation data, or anything time-sensitive.

Rules:
- If a question needs current/live data (tides, waves, recent species sightings) and you don't have a specific station ID or coordinates, ask the user for the location, or make a reasonable assumption and say so explicitly.
- NOAA CO-OPS only covers US stations. For non-US locations needing wave/ocean conditions, use get_marine_forecast (Open-Meteo) instead, which works globally but does not provide tide-table predictions.
- Never fabricate data values. If a tool call fails or returns nothing, say so plainly rather than guessing a plausible-sounding number.
- Be concise and conversational. This is a dashboard chat panel, not a report - skip headers and bullet-point walls unless the user is asking for a structured comparison.
- When you use retrieved context or a live tool result, the system will track it separately for citation - just answer naturally, you don't need to cite sources inline.
"""

MAX_TOOL_ITERATIONS = 5


async def run_agent_turn(
    user_message: str,
    history: list[ChatMessage],
) -> tuple[str, list[SourceRef]]:
    sources: list[SourceRef] = []

    # --- 1. RAG retrieval ---
    retrieved = await vector_store.search(user_message, top_k=3)
    context_block = ""
    if retrieved:
        context_lines = []
        for doc, score in retrieved:
            if score < 0.15:  # skip irrelevant matches
                continue
            context_lines.append(f"[{doc.title}]: {doc.text}")
            sources.append(
                SourceRef(
                    type="knowledge_base",
                    label=doc.title,
                    detail=f"similarity={score:.2f}",
                )
            )
        if context_lines:
            context_block = "\n\nRETRIEVED CONTEXT:\n" + "\n\n".join(context_lines)

    # --- 2. Build message history ---
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history[-10:]:  # cap history to keep token usage sane
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": user_message + context_block})

    # --- 3. Tool-calling loop ---
    for _ in range(MAX_TOOL_ITERATIONS):
        response = await _client.chat.completions.create(
            model=settings.groq_chat_model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.3,
        )
        choice = response.choices[0]
        message = choice.message

        if not message.tool_calls:
            return message.content or "", sources

        # Model wants to call one or more tools
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in message.tool_calls
                ],
            }
        )

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}

            try:
                result = await dispatch_tool_call(name, arguments)
                result_payload = _to_jsonable(result)
                sources.append(_source_ref_for_tool(name, arguments, result_payload))
            except Exception as exc:  # noqa: BLE001 - we want to surface any failure to the model
                logger.warning("Tool %s failed: %s", name, exc)
                result_payload = {"error": str(exc)}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result_payload, default=str)[:6000],
                }
            )

    # If we exhausted iterations without a final answer, ask the model to wrap up
    final = await _client.chat.completions.create(
        model=settings.groq_chat_model,
        messages=messages + [{"role": "user", "content": "Please give your final answer now."}],
        temperature=0.3,
    )
    return final.choices[0].message.content or "", sources


def _to_jsonable(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if obj is None:
        return None
    return obj


def _source_ref_for_tool(name: str, arguments: dict, result: dict) -> SourceRef:
    type_map = {
        "search_species_occurrences": "obis",
        "lookup_taxon_by_name": "worms",
        "get_water_level": "noaa",
        "get_tide_predictions": "noaa",
        "get_marine_forecast": "open_meteo",
    }
    label_map = {
        "search_species_occurrences": f"OBIS occurrence search: {arguments.get('scientific_name', '')}",
        "lookup_taxon_by_name": f"WoRMS taxonomy: {arguments.get('scientific_name', '')}",
        "get_water_level": f"NOAA water level - station {arguments.get('station_id', '')}",
        "get_tide_predictions": f"NOAA tide predictions - station {arguments.get('station_id', '')}",
        "get_marine_forecast": f"Open-Meteo marine forecast ({arguments.get('latitude')}, {arguments.get('longitude')})",
    }
    has_error = isinstance(result, dict) and "error" in result
    return SourceRef(
        type=type_map.get(name, "knowledge_base"),
        label=label_map.get(name, name),
        detail="failed" if has_error else "live data",
    )
