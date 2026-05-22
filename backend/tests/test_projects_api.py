async def test_project_crud_flow(client):
    create_response = await client.post(
        "/projects",
        json={
            "name": "Test Project",
            "description": "First rebuild project",
        },
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()

    assert created["name"] == "Test Project"
    assert created["description"] == "First rebuild project"
    assert created["id"]

    project_id = created["id"]

    list_response = await client.get("/projects")
    assert list_response.status_code == 200, list_response.text
    projects = list_response.json()
    assert any(project["id"] == project_id for project in projects)

    get_response = await client.get(f"/projects/{project_id}")
    assert get_response.status_code == 200, get_response.text
    loaded = get_response.json()
    assert loaded["id"] == project_id
    assert loaded["name"] == "Test Project"

    delete_response = await client.delete(f"/projects/{project_id}")
    assert delete_response.status_code == 204, delete_response.text

    missing_response = await client.get(f"/projects/{project_id}")
    assert missing_response.status_code == 404
