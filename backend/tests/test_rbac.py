from tests.conftest import auth_header


def test_login_returns_token(client, requestor):
    resp = client.post("/api/auth/login", json={"email": requestor.email, "password": "Password123!"})
    assert resp.status_code == 200, resp.get_json()
    assert "access_token" in resp.get_json()["data"]


def test_login_rejects_wrong_password(client, requestor):
    resp = client.post("/api/auth/login", json={"email": requestor.email, "password": "wrong"})
    assert resp.status_code == 401


def test_unauthenticated_request_is_rejected(client):
    resp = client.get("/api/demands")
    assert resp.status_code == 401


def test_requestor_only_sees_own_demands(client, app, requestor, project_manager, business_function):
    other_headers = auth_header(app, project_manager)
    client.post(
        "/api/demands",
        headers=other_headers,
        json={"title": "PM's own demand", "business_function_id": business_function.id, "problem_statement": "Some problem statement here."},
    )
    req_headers = auth_header(app, requestor)
    client.post(
        "/api/demands",
        headers=req_headers,
        json={"title": "Requestor's demand", "business_function_id": business_function.id, "problem_statement": "Another problem statement."},
    )

    resp = client.get("/api/demands", headers=req_headers)
    assert resp.status_code == 200
    titles = [d["title"] for d in resp.get_json()["data"]]
    assert titles == ["Requestor's demand"]


def test_requestor_cannot_review_demand(client, app, requestor, business_function):
    create = client.post(
        "/api/demands",
        headers=auth_header(app, requestor),
        json={"title": "Test Demand", "business_function_id": business_function.id, "problem_statement": "Problem statement text."},
    )
    demand_id = create.get_json()["data"]["id"]

    resp = client.post(f"/api/demands/{demand_id}/review", headers=auth_header(app, requestor), json={"action": "Approved"})
    assert resp.status_code == 403


def test_requestor_cannot_convert_demand(client, app, requestor, business_function):
    create = client.post(
        "/api/demands",
        headers=auth_header(app, requestor),
        json={"title": "Test Demand", "business_function_id": business_function.id, "problem_statement": "Problem statement text."},
    )
    demand_id = create.get_json()["data"]["id"]

    resp = client.post(f"/api/demands/{demand_id}/convert", headers=auth_header(app, requestor))
    assert resp.status_code == 403


def test_requestor_cannot_view_other_requestor_demand(client, app, requestor, business_function, db):
    from app.models.enums import Role
    from tests.conftest import make_test_user

    other_requestor = make_test_user(db, "Other Requestor", "other@test.example", Role.REQUESTOR, business_function)
    create = client.post(
        "/api/demands",
        headers=auth_header(app, other_requestor),
        json={"title": "Other's demand", "business_function_id": business_function.id, "problem_statement": "Problem statement text."},
    )
    demand_id = create.get_json()["data"]["id"]

    resp = client.get(f"/api/demands/{demand_id}", headers=auth_header(app, requestor))
    assert resp.status_code == 403
