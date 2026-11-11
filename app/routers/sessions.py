from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.database import get_db
from app.models import SurveySession, utcnow
from app.schemas import SessionCreate

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    dependencies=[Depends(require_api_key)],
)

@router.post("", status_code=201)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
):
    session = SurveySession(
        device_id=payload.device_id,
        started_at=payload.started_at or utcnow(),
        notes=payload.notes,
    )

    db.add(session)
    db.commit()
    db.refresh(session)
    return{
        "session_id": session.id,
        "device_id": session.device_id,
        "started_at": session.started_at,
    }
