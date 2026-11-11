from datetime import datetime, timezone
from uuid import uuid4

from app.auth import require_api_key
from app.main import app

def create_session(client):
    response = client.post(
        "/sessions",
        json={"device_id": "test-phone"},
    )
    assert response.status_code == 201
    return response.json()["session_id"]

def make_observation(session_id):
    return {
        "id": str(uuid4()),
        "session_id": session_id,
        "lat": 28.6139,
        "lon": 77.2090,
        "accuracy_m": 5,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.92,
        "model_version": "test-model",
    }

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_invalid_api_key(client):
    app.dependency_overrides.pop(require_api_key, None)

    response = client.post(
        "/sessions",
        headers={"X-API-Key": ""},
        json={"device_id": "test-phone"},
    )
    assert response.status_code == 401

def test_observation_retry_and_conflict(client):
    session_id = create_session(client)
    payload = make_observation(session_id)

    first = client.post("/observations", json=payload)
    assert first.status_code == 201

    retry = client.post("/observations", json=payload)
    assert retry.status_code == 200
    assert retry.json()["duplicate"] is True
    assert retry.json()["issue_id"] == first.json()["issue_id"]

    changed = {**payload, "lat": 28.7}
    conflict = client.post("/observations", json=changed)
    assert conflict.status_code == 409

    issues = client.get("/issues").json()
    assert issues["count"] == 1

def test_validation_and_missing_session(client):
    payload = make_observation(str(uuid4()))

    invalid = client.post(
        "/observations",
        json={**payload, "lat": 200},
    )
    assert invalid.status_code == 422

    missing_session = client.post(
        "/observations",
        json=payload,
    )
    assert missing_session.status_code == 404

def test_full_complaint_workflow(client):
    session_id = create_session(client)
    payload = make_observation(session_id)

    saved = client.post("/observations", json=payload)
    assert saved.status_code == 201
    issue_id = saved.json()["issue_id"]

    # Must review the issue before drafting.
    blocked_draft = client.post(
        f"/issues/{issue_id}/complaint-draft"
    )
    assert blocked_draft.status_code == 409

    confirmed = client.post(f"/issues/{issue_id}/confirm")
    assert confirmed.status_code == 200

    draft = client.post(
        f"/issues/{issue_id}/complaint-draft"
    )
    assert draft.status_code == 201
    complaint_id = draft.json()["id"]
    assert draft.json()["status"] == "draft"

    # Must approve before submission.
    blocked_submit = client.post(
        f"/complaints/{complaint_id}/submit"
    )
    assert blocked_submit.status_code == 409

    approved = client.post(
        f"/complaints/{complaint_id}/approve",
        json={"approved": True},
    )
    assert approved.status_code == 200

    submitted = client.post(
        f"/complaints/{complaint_id}/submit"
    )
    assert submitted.status_code == 200

    result = submitted.json()
    assert result["status"] == "submitted"
    assert result["destination"] == "sandbox"
    assert result["ack_ref"].startswith("SANDBOX-")

    repeated = client.post(
        f"/complaints/{complaint_id}/submit"
    )
    assert repeated.status_code == 200
    assert repeated.json()["ack_ref"] == result["ack_ref"]

    attempts = client.get(
        f"/complaints/{complaint_id}/attempts"
    )
    assert attempts.status_code == 200
    assert attempts.json()["count"] == 1

    # Sandbox submission must not imply an official report.
    issue = client.get(f"/issues/{issue_id}")
    assert issue.json()["status"] == "confirmed"