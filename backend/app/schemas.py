from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str=Field(min_length=8,max_length=128)
    full_name:str=Field(min_length=2,max_length=120)
    location:str=""
    @field_validator("email")
    @classmethod
    def normalize_email(cls,value): return str(value).strip().lower()
    @field_validator("password")
    @classmethod
    def validate_password(cls,value):
        if not any(char.islower() for char in value) or not any(char.isupper() for char in value) or not any(char.isdigit() for char in value):
            raise ValueError("Password must include uppercase, lowercase, and numeric characters")
        return value
    @field_validator("full_name", "location")
    @classmethod
    def strip_text(cls,value): return value.strip()

class Login(BaseModel):
    email:EmailStr
    password:str=Field(min_length=1,max_length=128)
    @field_validator("email")
    @classmethod
    def normalize_email(cls,value): return str(value).strip().lower()

class GoogleCallback(BaseModel):
    code: str=Field(min_length=1)
    state: str=Field(min_length=1)
class UserOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; email:EmailStr; full_name:str; bio:str; location:str; avatar_url:str; created_at:datetime
class UserUpdate(BaseModel): full_name:Optional[str]=None; bio:Optional[str]=None; location:Optional[str]=None; avatar_url:Optional[str]=None
class Token(BaseModel): access_token:str; token_type:str="bearer"; user:UserOut
class SkillCreate(BaseModel): title:str=Field(min_length=2,max_length=160); type:str; category:str; description:str=Field(min_length=5); tags:str=""; level:str="Beginner"; availability:str="Flexible"
class SkillOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; owner_id:int; title:str; type:str; category:str; description:str; tags:str; level:str; availability:str; created_at:datetime; owner:Optional[UserOut]=None
class SwapCreate(BaseModel): receiver_id:int; offered_skill_id:int; requested_skill_id:int; message:str=""
class SwapStatus(BaseModel): status:str
class MessageCreate(BaseModel): receiver_id:int; body:str=Field(min_length=1,max_length=2000)
class RatingCreate(BaseModel): score:int=Field(ge=1,le=5); review:str=""

class CoachRequest(BaseModel):
    target_skill:str=Field(min_length=2,max_length=120)
    current_skills:str=""
    goal:str=Field(min_length=3,max_length=500)

class SessionCreate(BaseModel):
    participant_id:int
    topic:str=Field(min_length=2,max_length=180)
    scheduled_at:datetime
    duration_minutes:int=Field(default=60,ge=15,le=180)
    meeting_link:str=""
    swap_id:Optional[int]=None

class SessionStatus(BaseModel):
    status:str
