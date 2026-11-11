from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.database import get_db
from app.models import RoadSegment

router = APIRouter(
    prefix="/roads",
    tags=["roads"],
    dependencies=[Depends(require_api_key)],
)

@router.get("")
def list_roads(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    db: Session = Depends(get_db),
):
    roads = db.scalars(
        select(RoadSegment)
        .order_by(RoadSegment.name, RoadSegment.id)
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "count": len(roads),
        "items": [
            {
                "id": road.id,
                "name": road.name,
                "authority": road.authority,
                "contractor": road.contractor,
                "source_ref": road.source_ref,
                "verified_at": road.verified_at,
            }
            for road in roads
        ],
    }
