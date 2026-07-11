from datetime import date, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field, computed_field


PrepLevel = Literal["minimal", "bronze", "silver", "gold"]
RiskType = Literal["flood", "landslide", "wind", "waterlogging", "power_outage"]
AlertType = Literal["flood", "blocked_road", "shelter", "medical", "power_outage", "other"]
SupplyCategory = Literal["medicine", "water", "food", "tools", "documents", "other"]


class Location(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class SignupRequest(BaseModel):
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    location: Location | None = None


class AuthResponse(BaseModel):
    user_id: str
    access_token: str
    token_type: str = "bearer"


class ProfileRequest(BaseModel):
    user_id: str | None = None
    family_size: int = Field(gt=0, le=30)
    age_distribution: list[int] = Field(default_factory=list)
    disabilities: list[str] = Field(default_factory=list)
    location: Location
    risks: list[RiskType] = Field(default_factory=list)
    pets: list[str] = Field(default_factory=list)
    prep_history: list[str] = Field(default_factory=list)


class ProfileResponse(BaseModel):
    user_id: str
    risk_score: int = Field(ge=0, le=100)
    recommendation_summary: str
    top_mitigations: list[str]
    recommended_prep_level: PrepLevel


class ChatContext(BaseModel):
    user_profile: dict | None = None
    location: Location | None = None
    prep_history: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)
    user_id: str = "demo-user"
    context: ChatContext = Field(default_factory=ChatContext)


class ActionButton(BaseModel):
    label: str
    endpoint: str
    icon: str


class AlertSummary(BaseModel):
    type: str
    text: str


class ChatResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid4().hex[:10]}")
    text: str
    action_buttons: list[ActionButton] = Field(default_factory=list)
    docs_to_link: list[str] = Field(default_factory=list)
    alerts: list[AlertSummary] = Field(default_factory=list)
    confidence: float = Field(default=0.75, ge=0, le=1)


class ChecklistItem(BaseModel):
    id: str
    title: str
    done: bool = False
    category: str
    cost_est: str
    time_est: str
    critical: bool = False
    notes: str | None = None


class ChecklistSection(BaseModel):
    section: str
    items: list[ChecklistItem]


class ChecklistResponse(BaseModel):
    user_id: str
    completion_pct: int = Field(ge=0, le=100)
    sections: list[ChecklistSection]
    last_regenerated_at: datetime


class ChecklistPatchRequest(BaseModel):
    done: bool | None = None
    notes: str | None = None
    cost_actual: float | None = Field(default=None, ge=0)
    time_actual_minutes: int | None = Field(default=None, ge=0)


class EmergencyContact(BaseModel):
    name: str
    phone: str
    relation: str | None = None


class EmergencyIdRequest(BaseModel):
    user_id: str
    full_name: str
    dob: date | None = None
    blood_group: str | None = None
    allergies: list[str] = Field(default_factory=list)
    meds: list[str] = Field(default_factory=list)
    emergency_contacts: list[EmergencyContact]
    insurance_details: str | None = None


class EmergencyIdResponse(BaseModel):
    id: str
    public_url: str
    qr_code_path: str
    pdf_path: str


class WeatherResponse(BaseModel):
    lat: float
    lng: float
    daily_rainfall_mm: list[float]
    max_rainfall_mm: float
    monsoon_alert_level: Literal["GREEN", "YELLOW", "RED"]
    summary: str


class CommunityAlertCreate(BaseModel):
    user_id: str = "demo-user"
    alert_type: AlertType
    title: str = Field(min_length=3, max_length=140)
    description: str = Field(min_length=3, max_length=1000)
    location: Location
    photo_url: str | None = None


class CommunityAlert(BaseModel):
    id: str
    user_id: str
    type: AlertType
    title: str
    description: str
    location: Location
    photo_url: str | None = None
    timestamp: datetime
    distance_km: float | None = None
    confidence: float = 0.7
    upvotes: int = 0


class AlertListResponse(BaseModel):
    alerts: list[CommunityAlert]


class SupplyTrackRequest(BaseModel):
    user_id: str
    item_name: str
    quantity: int = Field(gt=0)
    expiry_date: date | None = None
    category: SupplyCategory


class SupplyItem(BaseModel):
    id: str
    user_id: str
    item_name: str
    quantity: int
    expiry_date: date | None
    category: SupplyCategory
    reminder_date: date | None
    created_at: datetime

    @computed_field
    @property
    def days_to_expiry(self) -> int | None:
        if self.expiry_date is None:
            return None
        return (self.expiry_date - date.today()).days


class RecoveryReportRequest(BaseModel):
    user_id: str
    incident_date: date
    damage_description: str = Field(min_length=10, max_length=4000)
    insurance_provider: str | None = None
    photos: list[str] = Field(default_factory=list)


class RecoveryReportResponse(BaseModel):
    id: str
    damage_category: str
    severity_level: str
    repair_estimate: str
    incident_summary: str
    pdf_path: str
