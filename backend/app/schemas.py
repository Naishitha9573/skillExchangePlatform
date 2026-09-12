from datetime import datetime
from typing import Optional
from typing import Literal
from uuid import UUID
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
    @field_validator("full_name", "location", mode="before")
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
class UserUpdate(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True)
    full_name:Optional[str]=Field(default=None,min_length=2,max_length=120)
    bio:Optional[str]=Field(default=None,max_length=2000)
    location:Optional[str]=Field(default=None,max_length=120)
    avatar_url:Optional[str]=Field(default=None,max_length=500,pattern=r"^(https://\S+)?$")
class Token(BaseModel): access_token:str; token_type:str="bearer"; user:UserOut
class SkillCreate(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True)
    title:str=Field(min_length=2,max_length=160)
    type:Literal['Offering','Requesting']
    category:str=Field(min_length=2,max_length=60)
    description:str=Field(min_length=5,max_length=10000)
    tags:str=Field(default="",max_length=500)
    level:Literal['Beginner','Intermediate','Advanced']="Beginner"
    availability:str=Field(default="Flexible",max_length=120)
class SkillOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; owner_id:int; title:str; type:str; category:str; description:str; tags:str; level:str; availability:str; created_at:datetime; owner:Optional[UserOut]=None
class SwapCreate(BaseModel): receiver_id:int; offered_skill_id:int; requested_skill_id:int; message:str=""
class SwapStatus(BaseModel): status:str
class MessageCreate(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True)
    receiver_id:int=Field(gt=0)
    body:str=Field(min_length=1,max_length=2000)
    client_id:Optional[UUID]=None

class ConversationCreate(BaseModel):
    participant_id:int=Field(gt=0)

class ConversationRead(BaseModel):
    through_id:int=Field(gt=0)

class RatingCreate(BaseModel): score:int=Field(ge=1,le=5); review:str=Field(default="",max_length=2000)

class CoachRequest(BaseModel):
    target_skill:str=Field(min_length=2,max_length=120)
    current_skills:str=""
    goal:str=Field(min_length=3,max_length=500)

class SessionCreate(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True)
    participant_id:int
    topic:str=Field(min_length=2,max_length=180)
    scheduled_at:datetime
    duration_minutes:int=Field(default=60,ge=15,le=180)
    meeting_link:str=Field(default="",max_length=500,pattern=r"^(https://\S+)?$")
    swap_id:Optional[int]=None

class SessionStatus(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True)
    status:Optional[Literal['scheduled','completed','cancelled']]=None
    topic:Optional[str]=Field(default=None,min_length=2,max_length=180)
    scheduled_at:Optional[datetime]=None
    duration_minutes:Optional[int]=Field(default=None,ge=15,le=180)
