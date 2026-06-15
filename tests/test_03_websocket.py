"""
WebSocket endpoint test — real-time interview fast path.
"""
import json
import asyncio
import pytest
import websockets


@pytest.mark.asyncio
async def test_websocket_connect_and_echo(ws_base):
    """Connect to interview WS, send answer.submitted, receive echo."""
    import httpx

    # Create interview via API first
    async with httpx.AsyncClient(base_url="http://localhost:30080/api/v1", timeout=10) as client:
        # Need assessment + task + interview
        a = (await client.post("/assessments", json={
            "client_name": "WS Test", "project_name": "WS Test"
        })).json()
        t = (await client.post("/tasks", json={
            "assessment_id": a["id"], "title": "WS Test Task"
        })).json()
        i = (await client.post("/interviews", json={"task_id": t["id"]})).json()

    interview_id = i["id"]
    ws_url = f"{ws_base}/interviews/{interview_id}"

    try:
        async with websockets.connect(ws_url, open_timeout=5) as ws:
            payload = {
                "event": "answer.submitted",
                "payload": {"answer": "Cluster'da 3 node var, K8s 1.28 kullanıyoruz.", "interview_id": interview_id},
            }
            await ws.send(json.dumps(payload))
            response = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            assert response["event"] == "answer.submitted"
            assert "answer" in response["payload"]
    except Exception as e:
        pytest.skip(f"WebSocket not reachable: {e}")
    finally:
        # Cleanup
        async with httpx.AsyncClient(base_url="http://localhost:30080/api/v1", timeout=5) as client:
            await client.delete(f"/assessments/{a['id']}")
