import pytest
import asyncio
from sqlalchemy import delete
from app.db.session import AsyncSessionLocal, init_db, engine
from app.models.agent import AgentModel
from app.models.job import JobModel
from app.models.artifact import ArtifactModel
from app.models.detection import DetectionModel
from app.models.script import ScriptModel
from app.services.agent_service import AgentService
from app.services.job_service import JobService
from app.services.artifact_service import ArtifactService
from app.services.detection_service import DetectionService


@pytest.fixture(scope="session", autouse=True)
def init_test_database():
    """Ensure all database tables exist before any tests execute."""
    asyncio.run(init_db())


@pytest.fixture(autouse=True)
async def clean_database_and_singletons():
    """Wipe database tables and reset service singletons before each test."""
    AgentService.reset_state()
    JobService.reset_state()
    ArtifactService.reset_state()
    DetectionService.reset_state()

    async with AsyncSessionLocal() as session:
        await session.execute(delete(DetectionModel))
        await session.execute(delete(ArtifactModel))
        await session.execute(delete(JobModel))
        await session.execute(delete(AgentModel))
        await session.execute(delete(ScriptModel))
        await session.commit()

    yield

    AgentService.reset_state()
    JobService.reset_state()
    ArtifactService.reset_state()
    DetectionService.reset_state()
