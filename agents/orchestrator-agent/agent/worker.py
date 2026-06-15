# S4-AA-008: Kafka consumer — assessment.interview.completed → orchestrator tetikle
import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer
from agent.config import settings
from agent.graph import create_graph

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("orchestrator-worker")

_TOPIC = "assessment.interview.completed"


async def _run_orchestrator(assessment_id: str) -> None:
    graph = await create_graph()
    initial_state = {"assessment_id": assessment_id}
    config = {"configurable": {"thread_id": f"orchestrator-{assessment_id}"}}

    log.info("Orchestrator başlatıldı: assessment=%s", assessment_id)
    async for chunk in graph.astream(initial_state, config=config):
        node_name = list(chunk.keys())[0]
        log.info("Node tamamlandı: %s", node_name)

    log.info("Orchestrator tamamlandı: assessment=%s", assessment_id)


async def main() -> None:
    consumer = AIOKafkaConsumer(
        _TOPIC,
        bootstrap_servers=settings.kafka_bootstrap,
        group_id=settings.kafka_group_id,
        value_deserializer=lambda v: json.loads(v.decode()),
        auto_offset_reset="earliest",
    )
    await consumer.start()
    log.info("Orchestrator Kafka consumer başlatıldı, topic=%s", _TOPIC)

    try:
        async for msg in consumer:
            event = msg.value
            assessment_id = event.get("assessment_id")
            if not assessment_id:
                log.warning("assessment_id eksik, event atlandı: %s", event)
                continue

            # Her assessment için ayrı task — concurrent orchestration destekli
            asyncio.create_task(_run_orchestrator(assessment_id))
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
