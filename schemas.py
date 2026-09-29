from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = None
    role: str = "Field Reporter"
    location: str | None = None
    organization: str | None = None
    avatar_url: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)
    latitude: float
    longitude: float
    push_notifications: bool = True
    sms_alerts: bool = True


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = None
    role: str | None = None
    location: str | None = None
    organization: str | None = None
    avatar_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    reports_count: int | None = Field(default=None, ge=0)
    push_notifications: bool | None = None
    sms_alerts: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    latitude: float | None = None
    longitude: float | None = None


class LocationPayload(BaseModel):
    latitude: float
    longitude: float


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    latitude: float | None = None
    longitude: float | None = None
    last_risk_score: float | None = None
    last_risk_severity: str | None = None
    last_alert_at: datetime | None = None
    reports_count: int
    push_notifications: bool
    sms_alerts: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RiskCheckResult(BaseModel):
    latitude: float
    longitude: float
    risk: float
    severity: str
    rainfall_24h: float
    soil_moisture: float
    temperature: float | None = None
    susceptibility: float | None = None
    sms_sent: bool = False
    sms_message: str | None = None
    predicted_rainfall_24h: float | None = None
    predicted_rainfall_48h: float | None = None
    predicted_risk: float | None = None
    predicted_severity: str | None = None
    district: str | None = None
    weather_condition: str | None = None
    weather_code: int | None = None
    weather_trend: str | None = None



class AuthResponse(BaseModel):
    message: str
    user: UserOut
    risk_check: RiskCheckResult | None = None


class ReportMediaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_path: str
    media_type: str
    mime_type: str
    file_size: int
    created_at: datetime


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    reporter_name: str | None = None
    title: str
    description: str | None = None
    location_text: str | None = None
    latitude: float
    longitude: float
    severity: str
    status: str
    risk_score: float | None = None
    h3: str | None = None
    created_at: datetime
    media: list[ReportMediaOut] = []


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    report_id: int | None = None
    title: str
    message: str | None = None
    location_text: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    severity: str
    risk_score: float | None = None
    source: str
    is_read: bool
    created_at: datetime


class AlertReadUpdate(BaseModel):
    is_read: bool = True
