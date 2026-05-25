from app.domain.ingestion.types import ElementType
from app.domain.source import SourceStatus
from app.domain.structure.types import CandidateStatus, ProposalStatus
from app.domain.articles.topic_path import article_topic_path
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


async def test_article_blocks_keep_table_and_image_metadata(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Rich Candidate", CandidateStatus.CONFIRMED),
        ],
        fragments=[
            {
                "content": "Metric | Value\nBLEU | 27.5",
                "element_type": ElementType.TABLE,
                "meta_json": {
                    "table": {
                        "rows": [["Metric", "Value"], ["BLEU", "27.5"]],
                        "display_mode": "grid",
                    },
                    "caption_group_id": "caption-1-0",
                    "caption": {"target_kind": "table", "text": "Table 1: Results."},
                },
            },
            {
                "content": "Figure 1: Model architecture.",
                "element_type": ElementType.IMAGE,
                "meta_json": {
                    "image_base64": "ZmFrZS1pbWFnZQ==",
                    "image_ext": "png",
                    "image_width": 8,
                    "image_height": 6,
                    "image": {"has_payload": True},
                    "caption_group_id": "caption-2-1",
                    "caption": {"target_kind": "image", "text": "Figure 1: Model architecture."},
                },
            },
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

    blocks = detail_response.json()["blocks"]
    assert [block["element_type"] for block in blocks] == ["table", "image"]
    assert blocks[0]["meta_json"]["table"]["rows"] == [["Metric", "Value"], ["BLEU", "27.5"]]
    assert blocks[0]["meta_json"]["caption"]["text"] == "Table 1: Results."
    assert blocks[1]["meta_json"]["image_base64"] == "ZmFrZS1pbWFnZQ=="
    assert blocks[1]["meta_json"]["caption"]["text"] == "Figure 1: Model architecture."


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


async def test_list_articles_returns_topic_and_counts(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Confirmed Candidate", CandidateStatus.CONFIRMED),
        ],
        fragments=[
            {
                "content": "3 Model Architecture",
                "element_type": ElementType.HEADING,
                "heading_level": 1,
                "section_path": "Attention Is All You Need > 3 Model Architecture",
                "meta_json": {"source_label": "section_header"},
            },
            {
                "content": "The Transformer follows an encoder-decoder structure.",
                "element_type": ElementType.PARAGRAPH,
                "section_path": "Attention Is All You Need > 3 Model Architecture",
                "meta_json": {"source_label": "text"},
            },
        ],
    )

    await client.post(
        f"/projects/{context['project'].id}/articles/build",
        json={"proposal_id": str(context["proposal"].id)},
    )

    response = await client.get(f"/projects/{context['project'].id}/articles")

    assert response.status_code == 200
    [article] = response.json()
    assert article["topic_path"] == ["Attention Is All You Need", "Model Architecture"]
    assert article["block_count"] == 2
    assert article["source_count"] == 1


async def test_article_topic_path_nests_flat_document_sections():
    assert article_topic_path(
        title="Scaled Dot-Product Attention",
        section_paths=["Scaled Dot-Product Attention"],
    ) == ["Scaled Dot-Product Attention"]
    assert article_topic_path(
        title="Confirmed Candidate",
        section_paths=["3 Model Architecture > 3.2 Attention"],
    ) == ["Model Architecture", "Attention"]


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


async def test_get_article_infers_numbered_heading_levels(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Model Architecture", CandidateStatus.CONFIRMED),
        ],
        fragments=[
            {
                "content": "3 Model Architecture",
                "element_type": ElementType.HEADING,
                "heading_level": 1,
                "section_path": "3 Model Architecture",
            },
            {
                "content": "3.2 Attention",
                "element_type": ElementType.HEADING,
                "heading_level": 1,
                "section_path": "3.2 Attention",
            },
            {
                "content": "3.2.1 Scaled Dot-Product Attention",
                "element_type": ElementType.HEADING,
                "heading_level": 1,
                "section_path": "Scaled Dot-Product Attention",
            },
        ],
        link_order=[0, 1, 2],
    )

    build_response = await client.post(
        f"/projects/{context['project'].id}/articles/build",
        json={"proposal_id": str(context["proposal"].id)},
    )
    article_id = build_response.json()[0]["id"]

    response = await client.get(f"/projects/{context['project'].id}/articles/{article_id}")

    assert response.status_code == 200
    assert [block["heading_level"] for block in response.json()["blocks"]] == [1, 2, 3]


async def test_get_article_marks_duplicate_visual_heading_as_not_displayed(client, db):
    context = await _create_article_build_context(
        db,
        [
            ("Model Architecture", CandidateStatus.CONFIRMED),
        ],
        fragments=[
            {
                "content": "3.2 Attention",
                "element_type": ElementType.HEADING,
                "heading_level": 1,
                "section_path": "3.2 Attention",
            },
            {
                "content": "Scaled Dot-Product Attention",
                "element_type": ElementType.HEADING,
                "heading_level": 1,
                "section_path": "Scaled Dot-Product Attention",
            },
            {
                "content": "Figure 2.",
                "element_type": ElementType.IMAGE,
                "section_path": "Scaled Dot-Product Attention",
            },
            {
                "content": "3.2.1 Scaled Dot-Product Attention",
                "element_type": ElementType.HEADING,
                "heading_level": 1,
                "section_path": "3.2.1 Scaled Dot-Product Attention",
            },
        ],
        link_order=[0, 1, 2, 3],
    )

    build_response = await client.post(
        f"/projects/{context['project'].id}/articles/build",
        json={"proposal_id": str(context["proposal"].id)},
    )
    article_id = build_response.json()[0]["id"]

    response = await client.get(f"/projects/{context['project'].id}/articles/{article_id}")

    assert response.status_code == 200
    blocks = response.json()["blocks"]
    assert [block["content"] for block in blocks] == [
        "3.2 Attention",
        "Scaled Dot-Product Attention",
        "Figure 2.",
        "3.2.1 Scaled Dot-Product Attention",
    ]
    assert blocks[1]["include_in_article"] is False
    assert blocks[1]["include_in_outline"] is False
    assert blocks[3]["include_in_article"] is True
    assert blocks[3]["include_in_outline"] is True


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
    fragments: list[dict] | None = None,
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

    fragment_defaults = fragments or [
        {
            "content": "First fragment.",
            "element_type": ElementType.HEADING,
            "heading_level": 1,
            "meta_json": {"source_label": "section_header"},
        },
        {
            "content": "Second fragment.",
            "element_type": ElementType.PARAGRAPH,
            "heading_level": None,
            "meta_json": {"source_label": "text"},
        },
    ]
    created_fragments = [
        SourceFragment(
            source_id=source.id,
            content=str(fragment["content"]),
            element_type=fragment["element_type"],
            position_index=position_index,
            page_number=fragment.get("page_number", 1),
            heading_level=fragment.get("heading_level"),
            section_path=fragment.get("section_path", "First"),
            meta_json=fragment.get("meta_json"),
        )
        for position_index, fragment in enumerate(fragment_defaults)
    ]
    db.add_all(created_fragments)
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
                    fragment_id=created_fragments[fragment_index].id,
                    position_index=position_index,
                )
            )

    await db.commit()
    return {
        "project": project,
        "proposal": proposal,
        "candidates": created_candidates,
        "fragments": created_fragments,
        "source": source,
    }
