"""MongoDB data models and schemas."""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
        )

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema):
        schema.update(type="string")
        return schema


# ─── Auth Models (NEW) ──────────────────────────────────────────────────────

class UserRole:
    USER  = "user"
    ADMIN = "admin"


class User(BaseModel):
    """User account model."""
    id:          Optional[PyObjectId] = Field(alias="_id", default=None)
    name:        str
    email:       str
    password:    bytes                    # bcrypt hashed – never expose in responses
    role:        str = UserRole.USER
    is_active:   bool = True
    created_at:  datetime = Field(default_factory=datetime.utcnow)
    updated_at:  datetime = Field(default_factory=datetime.utcnow)
    last_login:  Optional[datetime] = None

    class Config:
        populate_by_name  = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserPublic(BaseModel):
    """Safe user representation (no password)."""
    user_id:    str
    name:       str
    email:      str
    role:       str
    created_at: str


class RegisterRequest(BaseModel):
    """Register request body."""
    name:     str
    email:    str
    password: str


class LoginRequest(BaseModel):
    """Login request body."""
    email:    str
    password: str


class AuthResponse(BaseModel):
    """Successful auth response."""
    token:   str
    user_id: str
    name:    str
    email:   str
    role:    str


# ─── Existing Models (unchanged) ────────────────────────────────────────────

class UserContributedName(BaseModel):
    """User-contributed name for plant or disease."""
    name:       str
    language:   str = "en"
    votes:      int = 0
    added_by:   Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Plant(BaseModel):
    """Plant model."""
    id:                     Optional[PyObjectId] = Field(alias="_id", default=None)
    canonical_name:         str
    scientific_name:        Optional[str] = None
    names:                  Dict[str, List[str]] = {}
    user_contributed_names: List[UserContributedName] = []
    care_instructions:      Dict[str, str] = {}
    description:            Dict[str, str] = {}
    created_at:             datetime = Field(default_factory=datetime.utcnow)
    updated_at:             datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name        = True
        arbitrary_types_allowed = True
        json_encoders           = {ObjectId: str}


class Disease(BaseModel):
    """Disease model."""
    id:                     Optional[PyObjectId] = Field(alias="_id", default=None)
    canonical_name:         str
    model_class:            str
    plant_id:               PyObjectId
    names:                  Dict[str, List[str]] = {}
    user_contributed_names: List[UserContributedName] = []
    description:            Dict[str, str] = {}
    symptoms:               Dict[str, List[str]] = {}
    cure:                   Dict[str, str] = {}
    prevention:             Dict[str, str] = {}
    created_at:             datetime = Field(default_factory=datetime.utcnow)
    updated_at:             datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name        = True
        arbitrary_types_allowed = True
        json_encoders           = {ObjectId: str}


class ModelClass(BaseModel):
    """Model class mapping."""
    id:         Optional[PyObjectId] = Field(alias="_id", default=None)
    class_name: str
    plant_id:   PyObjectId
    disease_id: Optional[PyObjectId] = None
    is_healthy: bool = False

    class Config:
        populate_by_name        = True
        arbitrary_types_allowed = True
        json_encoders           = {ObjectId: str}


class PredictionRequest(BaseModel):
    """Prediction request."""
    language: str = "en"


class PredictionResponse(BaseModel):
    """Prediction response."""
    plant_name:        str
    plant_id:          str
    is_healthy:        bool
    confidence:        float
    disease_name:      Optional[str] = None
    disease_id:        Optional[str] = None
    description:       Optional[str] = None
    symptoms:          Optional[List[str]] = None
    cure:              Optional[str] = None
    prevention:        Optional[str] = None
    care_instructions: Optional[str] = None