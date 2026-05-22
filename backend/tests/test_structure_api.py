from app.domain.ingestion.types import ElementType
from app.domain.source import SourceStatus
from app.domain.structure.types import CandidateStatus, ProposalStatus
from app.models.article_candidate import ArticleCandidate
from app.models.project import Project
from app.models.source import Source
from app.models.source_fragment import SourceFragment
from app.models.structure_proposal import StructureProposal


async def _create_project_with_source(db, *, name: str = "Structure Test"):
    project = Project(name=name)
    db.add(project)
    await db.flush()

    source = Source(
        project_id=project.id,
        filename="source.pdf",
        storage_path="/tmp/source.pdf",
        status=SourceStatus.DONE,
    )
    db.add(source)
    await db.flush()
    return project, source


async def test_propose_creates_candidates(client, db):
    project, source = await _create_project_with_source(db)
    db.add_all(
        [
            SourceFragment(
                source_id=source.id,
                content="Introduction",
                element_type=ElementType.HEADING,
                position_index=0,
                heading_level=1,
                section_path="Introduction",
            ),
            SourceFragment(
                source_id=source.id,
                content="Intro paragraph.",
                element_type=ElementType.PARAGRAPH,
                position_index=1,
                section_path="Introduction",
            ),
            SourceFragment(
                source_id=source.id,
                content="Methods",
                element_type=ElementType.HEADING,
                position_index=2,
                heading_level=1,
                section_path="Methods",
            ),
            SourceFragment(
                source_id=source.id,
                content="Methods paragraph.",
                element_type=ElementType.PARAGRAPH,
                position_index=3,
                section_path="Methods",
            ),
        ]
    )
    await db.commit()

    response = await client.post(f"/projects/{project.id}/structure/propose")

    assert response.status_code == 201, response.text
    proposal = response.json()
    assert proposal["project_id"] == str(project.id)
    assert proposal["status"] == "ready"
    assert proposal["candidate_count"] == 2
    assert [candidate["title"] for candidate in proposal["candidates"]] == [
        "Introduction",
        "Methods",
    ]
    assert [candidate["status"] for candidate in proposal["candidates"]] == [
        "proposed",
        "proposed",
    ]
    assert [candidate["source_section_path"] for candidate in proposal["candidates"]] == [
        "Introduction",
        "Methods",
    ]

    list_response = await client.get(f"/projects/{project.id}/structure/proposals")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == proposal["id"]

    detail_response = await client.get(
        f"/projects/{project.id}/structure/proposals/{proposal['id']}"
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["candidate_count"] == 2


async def test_candidate_fragments_preserve_position_order(client, db):
    project, source = await _create_project_with_source(db, name="Order Test")
    db.add_all(
        [
            SourceFragment(
                source_id=source.id,
                content="Overview",
                element_type=ElementType.HEADING,
                position_index=0,
                heading_level=1,
                section_path="Overview",
            ),
            SourceFragment(
                source_id=source.id,
                content="First paragraph.",
                element_type=ElementType.PARAGRAPH,
                position_index=1,
                section_path="Overview",
            ),
            SourceFragment(
                source_id=source.id,
                content="Second paragraph.",
                element_type=ElementType.PARAGRAPH,
                position_index=2,
                section_path="Overview",
            ),
        ]
    )
    await db.commit()

    response = await client.post(f"/projects/{project.id}/structure/propose")

    assert response.status_code == 201, response.text
    candidate = response.json()["candidates"][0]
    assert [fragment["position_index"] for fragment in candidate["fragments"]] == [
        0,
        1,
        2,
    ]
    assert [fragment["content"] for fragment in candidate["fragments"]] == [
        "Overview",
        "First paragraph.",
        "Second paragraph.",
    ]


async def test_empty_source_gives_empty_proposal(client, db):
    project, _ = await _create_project_with_source(db, name="Empty Test")
    await db.commit()

    response = await client.post(f"/projects/{project.id}/structure/propose")

    assert response.status_code == 201, response.text
    proposal = response.json()
    assert proposal["candidate_count"] == 0
    assert proposal["candidates"] == []


async def test_blank_fragments_give_empty_proposal(client, db):
    project, source = await _create_project_with_source(db, name="Blank Test")
    db.add(
        SourceFragment(
            source_id=source.id,
            content="   ",
            element_type=ElementType.PARAGRAPH,
            position_index=0,
        )
    )
    await db.commit()

    response = await client.post(f"/projects/{project.id}/structure/propose")

    assert response.status_code == 201, response.text
    proposal = response.json()
    assert proposal["candidate_count"] == 0
    assert proposal["candidates"] == []


async def test_propose_groups_by_top_level_section_path_without_headings(client, db):
    project, source = await _create_project_with_source(db, name="Section Path Test")
    db.add_all(
        [
            SourceFragment(
                source_id=source.id,
                content="Alpha paragraph.",
                element_type=ElementType.PARAGRAPH,
                position_index=0,
                section_path="Alpha",
            ),
            SourceFragment(
                source_id=source.id,
                content="Alpha detail.",
                element_type=ElementType.PARAGRAPH,
                position_index=1,
                section_path="Alpha > Detail",
            ),
            SourceFragment(
                source_id=source.id,
                content="Beta paragraph.",
                element_type=ElementType.PARAGRAPH,
                position_index=2,
                section_path="Beta",
            ),
        ]
    )
    await db.commit()

    response = await client.post(f"/projects/{project.id}/structure/propose")

    assert response.status_code == 201, response.text
    proposal = response.json()
    assert proposal["candidate_count"] == 2
    assert [candidate["title"] for candidate in proposal["candidates"]] == [
        "Alpha",
        "Beta",
    ]
    assert [fragment["content"] for fragment in proposal["candidates"][0]["fragments"]] == [
        "Alpha paragraph.",
        "Alpha detail.",
    ]


async def test_propose_keeps_candidates_source_scoped(client, db):
    project = Project(name="Multi Source Test")
    db.add(project)
    await db.flush()

    first_source = Source(
        project_id=project.id,
        filename="first.pdf",
        storage_path="/tmp/first.pdf",
        status=SourceStatus.DONE,
    )
    second_source = Source(
        project_id=project.id,
        filename="second.pdf",
        storage_path="/tmp/second.pdf",
        status=SourceStatus.DONE,
    )
    db.add_all([first_source, second_source])
    await db.flush()

    db.add_all(
        [
            SourceFragment(
                source_id=first_source.id,
                content="Overview",
                element_type=ElementType.HEADING,
                position_index=0,
                heading_level=1,
                section_path="Overview",
            ),
            SourceFragment(
                source_id=first_source.id,
                content="First source paragraph.",
                element_type=ElementType.PARAGRAPH,
                position_index=1,
                section_path="Overview",
            ),
            SourceFragment(
                source_id=second_source.id,
                content="Overview",
                element_type=ElementType.HEADING,
                position_index=0,
                heading_level=1,
                section_path="Overview",
            ),
            SourceFragment(
                source_id=second_source.id,
                content="Second source paragraph.",
                element_type=ElementType.PARAGRAPH,
                position_index=1,
                section_path="Overview",
            ),
        ]
    )
    await db.commit()

    response = await client.post(f"/projects/{project.id}/structure/propose")

    assert response.status_code == 201, response.text
    proposal = response.json()
    assert proposal["candidate_count"] == 2
    assert [candidate["title"] for candidate in proposal["candidates"]] == [
        "Overview",
        "Overview",
    ]
    assert [candidate["fragments"][1]["content"] for candidate in proposal["candidates"]] == [
        "First source paragraph.",
        "Second source paragraph.",
    ]


async def test_update_candidate_renames_candidate(client, db):
    proposal = await _create_proposal_with_candidate(db)
    candidate = proposal.candidates[0]

    response = await client.patch(
        f"/projects/{proposal.project_id}/structure/candidates/{candidate.id}",
        json={"title": "Renamed Candidate"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["title"] == "Renamed Candidate"
    assert payload["status"] == "proposed"


async def test_update_candidate_confirms_candidate(client, db):
    proposal = await _create_proposal_with_candidate(db)
    candidate = proposal.candidates[0]

    response = await client.patch(
        f"/projects/{proposal.project_id}/structure/candidates/{candidate.id}",
        json={"status": "confirmed"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "confirmed"


async def test_update_candidate_rejects_candidate(client, db):
    proposal = await _create_proposal_with_candidate(db)
    candidate = proposal.candidates[0]

    response = await client.patch(
        f"/projects/{proposal.project_id}/structure/candidates/{candidate.id}",
        json={"status": "rejected"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "rejected"


async def test_update_candidate_from_other_project_returns_404(client, db):
    proposal = await _create_proposal_with_candidate(db)
    other_project = Project(name="Other Project")
    db.add(other_project)
    await db.commit()
    candidate = proposal.candidates[0]

    response = await client.patch(
        f"/projects/{other_project.id}/structure/candidates/{candidate.id}",
        json={"status": "confirmed"},
    )

    assert response.status_code == 404


async def test_confirm_all_confirms_only_proposed_candidates(client, db):
    proposal = await _create_proposal_with_candidates(
        db,
        [
            ("Proposed Candidate", CandidateStatus.PROPOSED),
            ("Confirmed Candidate", CandidateStatus.CONFIRMED),
            ("Rejected Candidate", CandidateStatus.REJECTED),
        ],
    )

    response = await client.post(
        f"/projects/{proposal.project_id}/structure/proposals/{proposal.id}/confirm-all"
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"updated_count": 1}

    detail_response = await client.get(
        f"/projects/{proposal.project_id}/structure/proposals/{proposal.id}"
    )
    assert detail_response.status_code == 200
    assert [candidate["status"] for candidate in detail_response.json()["candidates"]] == [
        "confirmed",
        "confirmed",
        "rejected",
    ]


async def test_confirm_all_unknown_proposal_returns_404(client, db):
    project = Project(name="Unknown Proposal Test")
    db.add(project)
    await db.commit()

    response = await client.post(
        f"/projects/{project.id}/structure/proposals/00000000-0000-0000-0000-000000000001/confirm-all"
    )

    assert response.status_code == 404


async def test_inbox_lists_ready_structure_proposals(client, db):
    proposal = await _create_proposal_with_candidate(db)

    response = await client.get(f"/projects/{proposal.project_id}/inbox")

    assert response.status_code == 200, response.text
    assert response.json() == [
        {
            "id": str(proposal.id),
            "project_id": str(proposal.project_id),
            "type": "structure_proposal",
            "status": "ready",
            "title": "Review generated article candidates",
            "candidate_count": 1,
            "created_at": proposal.created_at.isoformat().replace("+00:00", "Z"),
            "target_id": str(proposal.id),
        }
    ]


async def test_inbox_empty_when_no_proposals(client, db):
    project = Project(name="Empty Inbox Test")
    db.add(project)
    await db.commit()

    response = await client.get(f"/projects/{project.id}/inbox")

    assert response.status_code == 200
    assert response.json() == []


async def test_inbox_does_not_show_reviewed_proposals(client, db):
    proposal = await _create_proposal_with_candidate(db)
    proposal.status = ProposalStatus.REVIEWED
    await db.commit()

    response = await client.get(f"/projects/{proposal.project_id}/inbox")

    assert response.status_code == 200
    assert response.json() == []


async def _create_proposal_with_candidate(db) -> StructureProposal:
    return await _create_proposal_with_candidates(
        db,
        [("Candidate", CandidateStatus.PROPOSED)],
    )


async def _create_proposal_with_candidates(
    db,
    candidates: list[tuple[str, CandidateStatus]],
) -> StructureProposal:
    project = Project(name="Candidate Review Test")
    db.add(project)
    await db.flush()

    proposal = StructureProposal(
        project_id=project.id,
        status=ProposalStatus.READY,
        candidate_count=len(candidates),
    )
    db.add(proposal)
    await db.flush()

    for index, (title, status) in enumerate(candidates):
        db.add(
            ArticleCandidate(
                proposal_id=proposal.id,
                title=title,
                source_section_path=title,
                status=status,
                suggested_order=index,
            )
        )

    await db.commit()
    await db.refresh(proposal, ["candidates"])
    return proposal
