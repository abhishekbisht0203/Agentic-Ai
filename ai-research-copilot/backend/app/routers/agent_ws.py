
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.cli_agent.cli_agent import CLIAgent
from app.agents.orchestrator.orchestrator import AIOrchestrator
from app.llms.factory import LLMFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])

_active_connections: dict[str, WebSocket] = {}


def _get_orchestrator() -> AIOrchestrator | None:
    try:
        factory = LLMFactory(default_provider="opencode")
        for provider_name in ["opencode", "openai", "anthropic"]:
            try:
                provider = factory.get_provider(provider_name)
                return AIOrchestrator(provider)
            except Exception:
                continue
    except Exception as exc:
        logger.warning("Failed to create orchestrator: %s", exc)
    return None


@router.websocket("/agent/{client_id}")
async def agent_websocket(websocket: WebSocket, client_id: str):
    await websocket.accept()
    _active_connections[client_id] = websocket
    logger.info("WebSocket client connected: %s", client_id)

    orchestrator = _get_orchestrator()
    cli_agent: CLIAgent | None = None
    if orchestrator:
        cli_agent = orchestrator.get_agent("cli_agent")
    else:
        factory = LLMFactory(default_provider="opencode")
        for provider_name in ["opencode", "openai", "anthropic"]:
            try:
                provider = factory.get_provider(provider_name)
                cli_agent = CLIAgent(provider)
                break
            except Exception:
                continue

    if cli_agent is None:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "No LLM provider available. Set OPENCODE_API_KEY in .env",
            "done": True,
        }))
        await websocket.close()
        return

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "message")
            content = data.get("content", "")

            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            if msg_type == "message":
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "content": "Processing...",
                    "done": False,
                }))

                try:
                    result = await cli_agent.chat(content)
                    response = result.get("response", "")

                    tool_calls = result.get("tool_calls", [])
                    for tc in tool_calls:
                        await websocket.send_text(json.dumps({
                            "type": "tool_call",
                            "tool": tc.get("name", ""),
                            "arguments": tc.get("arguments", {}),
                            "done": False,
                        }))

                    if tool_calls:
                        thought = result.get("thought", "")
                        if thought:
                            await websocket.send_text(json.dumps({
                                "type": "thought",
                                "content": thought,
                                "done": False,
                            }))
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "content": f"Calling {len(tool_calls)} tool(s)...",
                            "done": False,
                        }))

                    await websocket.send_text(json.dumps({
                        "type": "response",
                        "content": response,
                        "done": result.get("done", True),
                    }))
                except Exception as exc:
                    logger.exception("Agent execution failed")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": str(exc),
                        "done": True,
                    }))

            if msg_type == "disconnect":
                break

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected: %s", client_id)
    except Exception as exc:
        logger.exception("WebSocket error: %s", exc)
    finally:
        _active_connections.pop(client_id, None)


@router.get("/status")
async def ws_status() -> dict[str, Any]:
    return {
        "active_connections": len(_active_connections),
        "clients": list(_active_connections.keys()),
    }
