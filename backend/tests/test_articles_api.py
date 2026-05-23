from app.domain.ingestion.types import ElementType
from app.domain.source import SourceStatus
from app.domain.structure.types import CandidateStatus, ProposalStatus
from app.models.article_candidate import ArticleCandidate, ArticleCandidateFragment
from app.models.project import Project
from app.models.source import Source
from app.models.source_fragment import SourceFragment
from app.models.structure_proposal import StructureProposal


async def test_build_articles_from_confirmed_candidates(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Confirmed Candidate", CandidateStatus.CONFIRMED),
        ],
    )

    response = await client.post(
        f"/projects/{context['project'].id}/articles/build",
        json={"proposal_id": str(context["proposal"].id)},
    )

    assert response.status_code == 201, response.text
    articles = response.json()
    assert len(articles) == 1
    assert articles[0]["title"] == "Confirmed Candidate"
    assert articles[0]["status"] == "draft"
    assert articles[0]["candidate_id"] == str(context["candidates"][0].id)


async def test_build_skips_proposed_and_rejected_candidates(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Confirmed Candidate", CandidateStatus.CONFIRMED),
            ("Proposed Candidate", CandidateStatus.PROPOSED),
            ("Rejected Candidate", CandidateStatus.REJECTED),
        ],
    )

    response = await client.post(
        f"/projects/{context['project'].id}/articles/build",
        json={"proposal_id": str(context["proposal"].id)},
    )

    assert response.status_code == 201, response.text
    assert [article["title"] for article in response.json()] == [
        "Confirmed Candidate",
    ]


async def test_build_preserves_candidate_fragment_order(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Confirmed Candidate", CandidateStatus.CONFIRMED),
        ],
        link_order=[1, 0],
    )

    build_response = await client.post(
        f"/projects/{context['project'].id}/articles/build",
        json={"proposal_id": str(context["proposal"].id)},
    )
    article_id = build_response.json()[0]["id"]

    detail_response = await client.get(
        f"/projects/{context['project'].id}/articles/{article_id}"
    )

    assert detail_response.status_code == 200
    assert [block["content"] for block in detail_response.json()["blocks"]] == [
        "Second fragment.",
        "First fragment.",
    ]


async def test_article_blocks_keep_source_fragment_reference(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Confirmed Candidate", CandidateStatus.CONFIRMED),
        ],
    )

    build_response = await client.post(
        f"/projects/{context['project'].id}/articles/build",
        json={"proposal_id": str(context["proposal"].id)},
    )
    article_id = build_response.json()[0]["id"]

    detail_response = await client.get(
        f"/projects/{context['project'].id}/articles/{article_id}"
    )

    first_block = detail_response.json()["blocks"][0]
    first_fragment = context["fragments"][0]
    assert first_block["fragment_id"] == str(first_fragment.id)
    assert first_block["source_title"] is None
    assert first_block["source_filename"] == context["source"].filename
    assert first_block["content"] == first_fragment.content
    assert first_block["element_type"] == first_fragment.element_type.value
    assert first_block["page_number"] == first_fragment.page_number
    assert first_block["heading_level"] == first_fragment.heading_level
    assert first_block["section_path"] == first_fragment.section_path
    assert first_block["meta_json"] == first_fragment.meta_json


async def test_build_marks_proposal_reviewed(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Confirmed Candidate", CandidateStatus.CONFIRMED),
        ],
    )

    response = await client.post(
        f"/projects/{context['project'].id}/articles/build",
        json={"proposal_id": str(context["proposal"].id)},
    )

    assert response.status_code == 201

    proposal_response = await client.get(
        f"/projects/{context['project'].id}/structure/proposals/{context['proposal'].id}"
    )
    assert proposal_response.json()["status"] == "reviewed"


async def test_build_same_proposal_is_idempotent(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Confirmed Candidate", CandidateStatus.CONFIRMED),
        ],
    )
    url = f"/projects/{context['project'].id}/articles/build"
    payload = {"proposal_id": str(context["proposal"].id)}

    first_response = await client.post(url, json=payload)
    second_response = await client.post(url, json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json()[0]["id"] == first_response.json()[0]["id"]

    list_response = await client.get(f"/projects/{context['project'].id}/articles")
    assert len(list_response.json()) == 1


async def test_list_articles_returns_built_articles(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Confirmed Candidate", CandidateStatus.CONFIRMED),
        ],
    )

    await client.post(
        f"/projects/{context['project'].id}/articles/build",
        json={"proposal_id": str(context["proposal"].id)},
    )

    response = await client.get(f"/projects/{context['project'].id}/articles")

    assert response.status_code == 200
    assert [article["title"] for article in response.json()] == [
        "Confirmed Candidate",
    ]


async def test_get_article_returns_ordered_blocks(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Confirmed Candidate", CandidateStatus.CONFIRMED),
        ],
    )

    build_response = await client.post(
        f"/projects/{context['project'].id}/articles/build",
        json={"proposal_id": str(context["proposal"].id)},
    )
    article_id = build_response.json()[0]["id"]

    response = await client.get(f"/projects/{context['project'].id}/articles/{article_id}")

    assert response.status_code == 200
    assert [block["position_index"] for block in response.json()["blocks"]] == [0, 1]


async def test_build_unknown_project_returns_404(client):
    response = await client.post(
        "/projects/00000000-0000-0000-0000-000000000001/articles/build",
        json={"proposal_id": "00000000-0000-0000-0000-000000000002"},
    )

    assert response.status_code == 404


async def test_build_unknown_proposal_returns_404(client, db):
    project = Project(name="Unknown Proposal Build Test")
    db.add(project)
    await db.commit()

    response = await client.post(
        f"/projects/{project.id}/articles/build",
        json={"proposal_id": "00000000-0000-0000-0000-000000000002"},
    )

    assert response.status_code == 404


async def _create_article_build_context(
    db,
    candidates: list[tuple[str, CandidateStatus]],
    link_order: list[int] | None = None,
):
    project = Project(name="Article Build Test")
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

    fragments = [
        SourceFragment(
            source_id=source.id,
            content="First fragment.",
            element_type=ElementType.HEADING,
            position_index=0,
            page_number=1,
            heading_level=1,
            section_path="First",
            meta_json={"source_label": "section_header"},
        ),
        SourceFragment(
            source_id=source.id,
            content="Second fragment.",
            element_type=ElementType.PARAGRAPH,
            position_index=1,
            page_number=1,
            heading_level=None,
            section_path="First",
            meta_json={"source_label": "text"},
        ),
    ]
    db.add_all(fragments)
    await db.flush()

    proposal = StructureProposal(
        project_id=project.id,
        status=ProposalStatus.READY,
        candidate_count=len(candidates),
    )
    db.add(proposal)
    await db.flush()

    created_candidates = []
    for candidate_index, (title, status) in enumerate(candidates):
        candidate = ArticleCandidate(
            proposal_id=proposal.id,
            title=title,
            source_section_path=title,
            status=status,
            suggested_order=candidate_index,
        )
        db.add(candidate)
        await db.flush()
        created_candidates.append(candidate)

        ordered_fragment_indexes = link_order or [0, 1]
        for position_index, fragment_index in enumerate(ordered_fragment_indexes):
            db.add(
                ArticleCandidateFragment(
                    candidate_id=candidate.id,
                    fragment_id=fragments[fragment_index].id,
                    position_index=position_index,
                )
            )

    await db.commit()
    return {
        "project": project,
        "proposal": proposal,
        "candidates": created_candidates,
        "fragments": fragments,
        "source": source,
    }
