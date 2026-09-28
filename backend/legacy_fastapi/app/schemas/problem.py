from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

class Example(BaseModel):
    input: str
    output: str
    explanation: Optional[str] = None

class ProblemBase(BaseModel):
    title: str
    slug: str
    difficulty: str
    topics: List[str]
    patterns: List[str]
    description: str
    constraints: List[str]
    examples: List[Example]
    starter_code: Dict[str, str]

class ProblemCreate(ProblemBase):
    pass

class ProblemResponse(ProblemBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProblemListItem(BaseModel):
    id: int
    title: str
    slug: str
    difficulty: str
    topics: List[str]
    patterns: List[str]
    user_status: Optional[str] = "UNSOLVED"

    model_config = ConfigDict(from_attributes=True)
