from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class WorkExperience(BaseModel):
    job_title: Optional[str] = Field(None, description="Candidate job title")
    company: Optional[str] = Field(None, description="Company name")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date or Present")
    description: Optional[str] = Field(None, description="Responsibilities")

class Education(BaseModel):
    degree: Optional[str] = Field(None, description="Degree name")
    institution: Optional[str] = Field(None, description="University name")
    graduation_year: Optional[str] = Field(None, description="Graduation year")

class ParsedResume(BaseModel):
    candidate_id: Optional[str] = Field(None, description="Unique Vector DB ID")
    candidate_name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    raw_text: str = Field(..., description="Unmodified extracted text")