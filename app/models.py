import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Integer, ForeignKey, Enum, DateTime,
    Boolean, JSON, Text, Index,
)
from sqlalchemy.orm import relationship
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

def new_uuid() -> str:
    return str(uuid.uuid4())

# ---- Enums = fixed sets of allowed values ----

class IssueStatus(str, enum.Enum):
    open = "open"              # detected, not yet reviewed
    confirmed = "confirmed"    # a human checked it
    reported = "reported"       # complaint submitted
    resolved = "resolved"       # authority fixed it

class SizeBand(str, enum.Enum):
    small = "small"
    medium = "medium"
    large = "large"
    unknown = "unknown"         # honest default — uncalibrated phone

class ComplaintStatus(str, enum.Enum):
    draft = "draft"             # text generated, not approved
    approved = "approved"       # user said "yes, send it"
    submitted = "submitted"     # sandbox/portal confirmed receipt
    failed = "failed"           # submission attempt failed

# ---- Tables ----

class SurveySession(Base):
    """One car journey. Created when the user taps 'Start survey'."""
    __tablename__ = "survey_sessions"
    id = Column(String, primary_key=True, default=new_uuid)
    device_id = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), default=utcnow)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

class Observation(Base):
    """One raw detection from the camera. The phone generates the ID,
    so if the upload is retried, we don't save it twice (idempotency)."""
    __tablename__ = "observations"
    id = Column(String, primary_key=True)  # CLIENT-generated UUID
    session_id = Column(String, ForeignKey("survey_sessions.id"), nullable=False)
    issue_id = Column(String, ForeignKey("issues.id"), nullable=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    accuracy_m = Column(Float, nullable=True)      # GPS accuracy from the phone
    captured_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), default=utcnow)
    confidence = Column(Float, nullable=False)     # model confidence 0..1
    size_band = Column(Enum(SizeBand), default=SizeBand.unknown)
    bbox = Column(JSON, nullable=True)             # {"x1":..,"y1":..,"x2":..,"y2":..}
    image_path = Column(String, nullable=True)     # private storage key
    model_version = Column(String, nullable=True)

__table_args__ = (Index("ix_obs_lat_lon", "lat", "lon"),)

class Issue(Base):
    """One PHYSICAL pothole on the road. Multiple observations merge into this."""
    __tablename__ = "issues"
    id = Column(String, primary_key=True, default=new_uuid)
    lat = Column(Float, nullable=False)            # merged/centroid location
    lon = Column(Float, nullable=False)
    status = Column(Enum(IssueStatus), default=IssueStatus.open, index=True)
    size_band = Column(Enum(SizeBand), default=SizeBand.unknown)
    first_seen_at = Column(DateTime(timezone=True), default=utcnow)
    last_seen_at = Column(DateTime(timezone=True), default=utcnow)
    observation_count = Column(Integer, default=1)
    road_segment_id = Column(String, ForeignKey("road_segments.id"), nullable=True)

observations = relationship("Observation", backref="issue")
road_segment = relationship("RoadSegment", backref="issues")

class RoadSegment(Base):
    """A stretch of road + who is responsible for it. YOU fill this from
    verified records. If contractor is unknown, leave it NULL — never guess."""
    __tablename__ = "road_segments"
    id = Column(String, primary_key=True, default=new_uuid)
    name = Column(String, nullable=False)
    authority = Column(String, nullable=False)          # e.g. "Municipal Corporation"
    maintenance_agency = Column(String, nullable=True)
    contractor = Column(String, nullable=True)          # ONLY if verified
    contract_ref = Column(String, nullable=True)       # tender / work-order no.
    source_ref = Column(String, nullable=True)          # document that proves it
    verified_at = Column(DateTime(timezone=True), nullable=True)
    # Road as a list of points: [[lat, lon], [lat, lon], ...]
    geometry = Column(JSON, nullable=False)

class Complaint(Base):
    """A written complaint about one issue. Draft → approved → submitted."""
    __tablename__ = "complaints"
    id = Column(String, primary_key=True, default=new_uuid)
    issue_id = Column(String, ForeignKey("issues.id"), nullable=False)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.draft)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    destination = Column(String, nullable=False)        # "sandbox" for now
    reporter_name = Column(String, nullable=True)
    reporter_contact = Column(String, nullable=True)    # minimize personal data
    created_at = Column(DateTime(timezone=True), default=utcnow)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    ack_ref = Column(String, nullable=True)            # only from real responses

issue = relationship("Issue", backref="complaints")

class SubmissionAttempt(Base):
    """History of every submit try — for debugging and honest status tracking."""
    __tablename__ = "submission_attempts"
    id = Column(String, primary_key=True, default=new_uuid)
    complaint_id = Column(
        String,
        ForeignKey("complaints.id"),
        nullable=False,
        index=True,
    )
    attempt_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    request_id = Column(String, nullable=True)
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    success = Column(Boolean, default=False, nullable=False)

