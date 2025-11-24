from pydantic import BaseModel

class SynthesizerAgentRequest(BaseModel):
    user_query: str
    is_sensitive_data_exists: bool = False
    ingestion_context: str|None = None
