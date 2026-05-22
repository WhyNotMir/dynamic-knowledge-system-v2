import uuid

from app.domain.source import SourceStatus
from app.workers import ingestion_worker


async def test_ingest_source_job_calls_ingestion_and_commits(monkeypatch):
    source_id = uuid.uuid4()
    calls: list[uuid.UUID] = []

    class FakeSource:
        status = SourceStatus.DONE

    class FakeSession:
        committed = False
        rolled_back = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def commit(self):
            self.committed = True

        async def rollback(self):
            self.rolled_back = True

    fake_session = FakeSession()

    def fake_session_factory():
        return fake_session

    async def fake_ingest_source(parsed_source_id, db):
        calls.append(parsed_source_id)
        assert db is fake_session
        return FakeSource()

    monkeypatch.setattr(ingestion_worker, "AsyncSessionLocal", fake_session_factory)
    monkeypatch.setattr(ingestion_worker, "ingest_source", fake_ingest_source)

    await ingestion_worker.ingest_source_job({}, str(source_id))

    assert calls == [source_id]
    assert fake_session.committed is True
    assert fake_session.rolled_back is False
