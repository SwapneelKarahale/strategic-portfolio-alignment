from tests.conftest import auth_header


def _create_demand(client, app, requestor, business_function):
    resp = client.post(
        "/api/demands",
        headers=auth_header(app, requestor),
        json={
            "title": "Customer Analytics Platform",
            "business_function_id": business_function.id,
            "problem_statement": "Manual reporting takes too long and is error-prone.",
        },
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["data"]


def test_create_demand_starts_as_draft(client, app, requestor, business_function):
    demand = _create_demand(client, app, requestor, business_function)
    assert demand["status"] == "Draft"
    assert demand["requestor_id"] == requestor.id


def test_requestor_can_submit_draft(client, app, requestor, business_function):
    demand = _create_demand(client, app, requestor, business_function)
    resp = client.patch(
        f"/api/demands/{demand['id']}", headers=auth_header(app, requestor), json={"status": "Submitted"}
    )
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["data"]["status"] == "Submitted"


def test_requestor_cannot_skip_states(client, app, requestor, business_function):
    demand = _create_demand(client, app, requestor, business_function)
    resp = client.patch(
        f"/api/demands/{demand['id']}", headers=auth_header(app, requestor), json={"status": "Approved"}
    )
    assert resp.status_code == 400
    assert "requestor" in resp.get_json()["error"].lower() or "submit" in resp.get_json()["error"].lower()


def test_full_demand_to_project_flow(client, app, requestor, project_manager, business_function, capability):
    demand = _create_demand(client, app, requestor, business_function)
    demand_id = demand["id"]

    client.patch(f"/api/demands/{demand_id}", headers=auth_header(app, requestor), json={"status": "Submitted"})

    pm_headers = auth_header(app, project_manager)
    resp = client.post(f"/api/demands/{demand_id}/review", headers=pm_headers, json={"action": "Under Review"})
    assert resp.status_code == 200, resp.get_json()

    resp = client.post(f"/api/demands/{demand_id}/review", headers=pm_headers, json={"action": "Validated"})
    assert resp.status_code == 200, resp.get_json()

    resp = client.post(f"/api/demands/{demand_id}/review", headers=pm_headers, json={"action": "Approved"})
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["data"]["status"] == "Approved"

    resp = client.post(f"/api/demands/{demand_id}/convert", headers=pm_headers)
    assert resp.status_code == 201, resp.get_json()
    project = resp.get_json()["data"]
    assert project["status"] == "Portfolio"

    resp = client.post(f"/api/demands/{demand_id}/convert", headers=pm_headers)
    assert resp.status_code == 400  # cannot convert twice


def test_cannot_convert_unapproved_demand(client, app, requestor, project_manager, business_function):
    demand = _create_demand(client, app, requestor, business_function)
    resp = client.post(f"/api/demands/{demand['id']}/convert", headers=auth_header(app, project_manager))
    assert resp.status_code == 400
    assert "approved" in resp.get_json()["error"].lower()


def test_project_cannot_start_without_roadmap(client, app, requestor, project_manager, business_function, capability):
    demand = _create_demand(client, app, requestor, business_function)
    demand_id = demand["id"]
    pm_headers = auth_header(app, project_manager)

    client.patch(f"/api/demands/{demand_id}", headers=auth_header(app, requestor), json={"status": "Submitted"})
    client.post(f"/api/demands/{demand_id}/review", headers=pm_headers, json={"action": "Under Review"})
    client.post(f"/api/demands/{demand_id}/review", headers=pm_headers, json={"action": "Validated"})
    client.post(f"/api/demands/{demand_id}/review", headers=pm_headers, json={"action": "Approved"})
    project = client.post(f"/api/demands/{demand_id}/convert", headers=pm_headers).get_json()["data"]

    # assign self as PM so the manage-permission check passes
    client.patch(f"/api/projects/{project['id']}", headers=pm_headers, json={"project_manager_id": project_manager.id})

    resp = client.patch(f"/api/projects/{project['id']}/status", headers=pm_headers, json={"status": "Planned"})
    # Planned is only reachable via roadmap scheduling (POST /api/roadmap), not a raw status PATCH
    assert resp.status_code == 400
    assert "roadmap" in resp.get_json()["error"].lower()
