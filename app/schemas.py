from datetime import datetime
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

class RequestModel(BaseModel):
    # Reject misspelled or unexpected request fields.
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
    )

class SessionCreate(RequestModel):
    device_id: str = Field(min_length=1, max_length=128)
    started_at: AwareDatetime | None = None
    notes: str | None = Field(default=None, max_length=1000)

class BoundingBox(RequestModel):
    # Pixel coordinates relative to the original image.
    x1: float = Field(ge=0)
    y1: float = Field(ge=0)
    x2: float = Field(gt=0)
    y2: float = Field(gt=0)

@model_validator(mode="after")
def validate_box(self):
        if self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError(
                "x2 must exceed x1, and y2 must exceed y1"
            )
        return self

class ObservationCreate(RequestModel):
    id: UUID
    session_id: UUID

    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    accuracy_m: float = Field(ge=0, le=10000)

    captured_at: AwareDatetime
    confidence: float = Field(ge=0, le=1)

    bbox: BoundingBox | None = None
    model_version: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

class ApprovalRequest(RequestModel):
    approved: bool

class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    issue_id: str
    status: str
    subject: str
    body: str
    destination: str
    created_at: datetime
    submitted_at: datetime | None
    ack_ref: str | None
