from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.database import get_db
from app.models import (
    Issue,
    IssueStatus,
    Observation,
    SizeBand,
    SurveySession,
)
from app.schemas import ObservationCreate

router = APIRouter(
    prefix="/observations",
    tags=["observations"],
    dependencies=[Depends(require_api_key)],
)


def normalize_utc(value):
    """Ensure datetime is timezone-aware UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def matches_existing(existing, payload):
    """A reused observation ID must represent the same request."""
    submitted_bbox = (
        payload.bbox.model_dump()
        if payload.bbox is not None
        else None
    )

    return (
        existing.session_id == str(payload.session_id)
        and existing.lat == payload.lat
        and existing.lon == payload.lon
        and existing.accuracy_m == payload.accuracy_m
        and existing.confidence == payload.confidence
        and normalize_utc(existing.captured_at)
        == normalize_utc(payload.captured_at)
        and existing.bbox == submitted_bbox
        and existing.model_version == payload.model_version
    )


def retry_result(existing, payload, response):
    if not matches_existing(existing, payload):
        raise HTTPException(
            status_code=409,
            detail=(
                "This observation ID already exists with different data. "
                "Retry with the original payload or use a new ID."
            ),
        )

    response.status_code = 200

    return {
        "observation_id": existing.id,
        "issue_id": existing.issue_id,
        "duplicate": True,
    }


@router.post("", status_code=201)
def create_observation(
    payload: ObservationCreate,
    response: Response,
    db: Session = Depends(get_db),
):
    observation_id = str(payload.id)
    session_id = str(payload.session_id)

    existing = db.get(Observation, observation_id)

    if existing is not None:
        return retry_result(existing, payload, response)

    survey_session = db.get(SurveySession, session_id)

    if survey_session is None:
        raise HTTPException(
            status_code=404,
            detail="Survey session not found",
        )

    captured_at = payload.captured_at.astimezone(timezone.utc)

    issue = Issue(
        lat=payload.lat,
        lon=payload.lon,
        status=IssueStatus.open,
        size_band=SizeBand.unknown,
        first_seen_at=captured_at,
        last_seen_at=captured_at,
        observation_count=1,
    )

    try:
        db.add(issue)
        db.flush()  # Generates issue.id without committing yet.

        observation = Observation(
            id=observation_id,
            session_id=session_id,
            issue_id=issue.id,
            lat=payload.lat,
            lon=payload.lon,
            accuracy_m=payload.accuracy_m,
            captured_at=captured_at,
            confidence=payload.confidence,
            size_band=SizeBand.unknown,
            bbox=(
                payload.bbox.model_dump()
                if payload.bbox is not None
                else None
            ),
            model_version=payload.model_version,
        )

        db.add(observation)
        db.commit()

    except IntegrityError:
        db.rollback()

        # Another request might have inserted this ID at the same time.
        existing = db.get(Observation, observation_id)

        if existing is not None:
            return retry_result(existing, payload, response)

        raise HTTPException(
            status_code=409,
            detail="Could not store observation due to a data conflict",
        )

    return {
        "observation_id": observation_id,
        "issue_id": issue.id,
        "duplicate": False,
    }