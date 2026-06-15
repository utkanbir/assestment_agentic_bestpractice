"""Kafka consumer entry point for the Kubernetes Assessment Agent.

Topics consumed:
  - interview.answer.submitted  → resumes graph with human answer (slow path)
  - assessment.task.created     → starts a new interview graph

Topic produced:
  - assessment.finding.detected  (via kg_writer → API)
"""
import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agent.config import settings
from agent.graph import build_graph

log = logging.getLogger(__name__)


async def _handle_task_created(graph, event: dict) -> None:
    """Start a new graph run when a task is created."""
    thread_id = f"task-{event['task_id']}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "assessment_id": event["assessment_id"],
        "task_id": event["task_id"],
        "interview_id": event.get("interview_id", ""),
        "task_scope": event.get("scope", "Kubernetes Assessment"),
        "covered_areas": [],
        "existing_findings": [],
        "messages": [],
        "current_question": "",
        "last_answer": "",
        "answer_count": 0,
        "pending_evidence": [],
        "pending_findings": [],
        "phase": "PRE_INTERVIEW",
        "should_end_interview": False,
        "human_approval_required": False,
        "approved_finding_ids": [],
        "report_markdown": "",
        "error": None,
    }

    async for _ in graph.astream(initial_state, config=config):
        pass  # graph pauses at answer_processor interrupt; WebSocket sends question to frontend


async def _handle_answer_submitted(graph, event: dict) -> None:
    """Resume a paused graph with the human's answer."""
    thread_id = f"task-{event['task_id']}"
    config = {"configurable": {"thread_id": thread_id}}

    resume_state = {
        "last_answer": event["answer"],
        "answer_count": event.get("answer_count", 0),
    }

    async for _ in graph.astream(resume_state, config=config):
        pass


async def run() -> None:
    consumer = AIOKafkaConsumer(
        "interview.answer.submitted",
        "assessment.task.created",
        bootstrap_servers=settings.kafka_bootstrap,
        group_id=settings.kafka_group_id,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    async with AsyncPostgresSaver.from_conn_string(settings.postgres_url) as checkpointer:
        await checkpointer.setup()
        graph = build_graph(checkpointer)

        await consumer.start()
        log.info("K8s agent worker started, consuming Kafka topics…")
        try:
            async for msg in consumer:
                topic = msg.topic
                event = msg.value
                log.info("Received %s: task=%s", topic, event.get("task_id"))
                try:
                    if topic == "assessment.task.created":
                        await _handle_task_created(graph, event)
                    elif topic == "interview.answer.submitted":
                        await _handle_answer_submitted(graph, event)
                except Exception as exc:
                    log.exception("Error processing %s: %s", topic, exc)
        finally:
            await consumer.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
