from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.database import get_db
from app.models import Issue, IssueStatus, Observation

router = APIRouter(
    prefix="/issues",
    tags=["issues"],
    dependencies=[Depends(require_api_key)],
)

def serialize_issue(issue):
    return {
        "id": issue.id,
        "lat": issue.lat,
        "lon": issue.lon,
        "location_note": "Approximate phone GPS location",
        "status": issue.status.value,
        "size_band": issue.size_band.value,
        "observation_count": issue.observation_count,
        "road_segment_id": issue.road_segment_id,
        "first_seen_at": issue.first_seen_at,
        "last_seen_at": issue.last_seen_at,
    }

def find_issue(db, issue_id):
    issue = db.get(Issue, str(issue_id))

    if issue is None:
        raise HTTPException(
            status_code=404,
            detail="Issue not found",
        )

    return issue

@router.get("")
def list_issues(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    db: Session = Depends(get_db),
):
    statement = (
        select(Issue)
        .order_by(Issue.first_seen_at.desc(), Issue.id)
        .offset(offset)
        .limit(limit)
    )

    issues = db.scalars(statement).all()

    return {
        "count": len(issues),
        "limit": limit,
        "offset": offset,
        "items": [serialize_issue(issue) for issue in issues],
    }

@router.get("/{issue_id}")
def get_issue(
    issue_id: UUID,
    db: Session = Depends(get_db),
):
    issue = find_issue(db, issue_id)

    observations = db.scalars(
        select(Observation)
        .where(Observation.issue_id == issue.id)
        .order_by(Observation.captured_at)
        .limit(100)
    ).all()

    return {
        **serialize_issue(issue),
        "observations": [
            {
                "id": item.id,
                "session_id": item.session_id,
                "accuracy_m": item.accuracy_m,
                "confidence": item.confidence,
                "captured_at": item.captured_at,
                "bbox": item.bbox,
                "model_version": item.model_version,
                "has_evidence": bool(item.image_path),
            }
            for item in observations
        ],
    }

@router.post("/{issue_id}/confirm")
def confirm_issue(
    issue_id: UUID,
    db: Session = Depends(get_db),
):
    issue = find_issue(db, issue_id)

    if issue.status not in {
        IssueStatus.open,
        IssueStatus.confirmed,
    }:
        raise HTTPException(
            status_code=409,
            detail="Only open or confirmed issues can be confirmed",
        )

    issue.status = IssueStatus.confirmed
    db.commit()

    return serialize_issue(issue)