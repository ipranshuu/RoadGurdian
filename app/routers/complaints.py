import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.config import settings
from app.database import get_db
from app.models import (
    Complaint,
    ComplaintStatus,
    Issue,
    IssueStatus,
    SubmissionAttempt,
    utcnow,
)
from app.schemas import ApprovalRequest, ComplaintResponse
from app.services.complaint_generator import generate_complaint
from app.services.portal_adapter import submit_to_sandbox

router = APIRouter(
    tags=["complaints"],
    dependencies=[Depends(require_api_key)],
)

def find_complaint(db, complaint_id):
    complaint = db.get(Complaint, str(complaint_id))

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    return complaint

@router.post(
    "/issues/{issue_id}/complaint-draft",
    response_model=ComplaintResponse,
    status_code=201,
)
def create_draft(
    issue_id: UUID,
    db: Session = Depends(get_db),
):
    issue = db.get(Issue, str(issue_id))

    if issue is None:
        raise HTTPException(
            status_code=404,
            detail="Issue not found",
        )

    if issue.status != IssueStatus.confirmed:
        raise HTTPException(
            status_code=409,
            detail="Confirm the issue before generating a complaint",
        )

    existing = db.scalar(
        select(Complaint)
        .where(Complaint.issue_id == issue.id)
        .order_by(Complaint.created_at.desc())
        .limit(1)
    )

    if existing is not None:
        return existing

    subject, body = generate_complaint(issue)

    complaint = Complaint(
        issue_id=issue.id,
        status=ComplaintStatus.draft,
        subject=subject,
        body=body,
        destination="sandbox",
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return complaint

@router.get(
    "/complaints/{complaint_id}",
    response_model=ComplaintResponse,
)
def get_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    return find_complaint(db, complaint_id)

@router.post(
    "/complaints/{complaint_id}/approve",
    response_model=ComplaintResponse,
)
def approve_complaint(
    complaint_id: UUID,
    payload: ApprovalRequest,
    db: Session = Depends(get_db),
):
    if not payload.approved:
        raise HTTPException(
            status_code=400,
            detail="Explicit approval is required",
        )

    complaint = find_complaint(db, complaint_id)

    # Idempotency check: if already approved, just return it (200 OK)
    if complaint.status == ComplaintStatus.approved:
        return complaint

    if complaint.status != ComplaintStatus.draft:
        raise HTTPException(
            status_code=409,
            detail="Only draft complaints can be approved",
        )

    complaint.status = ComplaintStatus.approved
    db.commit()
    db.refresh(complaint)

    return complaint

@router.post(
    "/complaints/{complaint_id}/submit",
    response_model=ComplaintResponse,
)
def submit_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    complaint = find_complaint(db, complaint_id)

    if settings.portal_mode != "sandbox":
        raise HTTPException(
            status_code=503,
            detail="Only sandbox submission is implemented",
        )

    if complaint.destination != "sandbox":
        raise HTTPException(
            status_code=409,
            detail="This endpoint accepts sandbox complaints only",
        )

    if complaint.status == ComplaintStatus.submitted:
        return complaint

    if complaint.status != ComplaintStatus.approved:
        raise HTTPException(
            status_code=409,
            detail="Approve the complaint before submitting",
        )

    result = submit_to_sandbox(complaint.id)

    # Atomically change approved -> submitted.
    transition = db.execute(
        update(Complaint)
        .where(
            Complaint.id == complaint.id,
            Complaint.status == ComplaintStatus.approved,
        )
        .values(
            status=ComplaintStatus.submitted,
            submitted_at=utcnow(),
            ack_ref=result["ack_ref"],
        )
        .execution_options(synchronize_session=False)
    )

    # INDENTATION FIXED HERE: 
    # This block now strictly handles failed updates.
    if transition.rowcount != 1:
        db.rollback()
        db.refresh(complaint)

        if complaint.status == ComplaintStatus.submitted:
            return complaint

        raise HTTPException(
            status_code=409,
            detail="Complaint status changed; reload and try again",
        )

    db.add(
        SubmissionAttempt(
            complaint_id=complaint.id,
            request_id=complaint.id,
            response_code=200,
            response_body=json.dumps(result),
            success=True,
        )
    )

    # Do NOT mark the road issue as officially reported.
    # A sandbox submission is not a real government report.
    db.commit()
    db.refresh(complaint)

    return complaint

@router.get("/complaints/{complaint_id}/attempts")
def list_attempts(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    complaint = find_complaint(db, complaint_id)

    attempts = db.scalars(
        select(SubmissionAttempt)
        .where(SubmissionAttempt.complaint_id == complaint.id)
        .order_by(SubmissionAttempt.attempt_at.desc())
        .limit(100)
    ).all()

    return {
        "count": len(attempts),
        "items": [
            {
                "id": attempt.id,
                "attempt_at": attempt.attempt_at,
                "request_id": attempt.request_id,
                "response_code": attempt.response_code,
                "success": attempt.success,
            }
            for attempt in attempts
        ],
    }
