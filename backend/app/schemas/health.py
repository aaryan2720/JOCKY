from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service health status")
    service: str = Field(default="jocky-backend", description="Service identifier")
