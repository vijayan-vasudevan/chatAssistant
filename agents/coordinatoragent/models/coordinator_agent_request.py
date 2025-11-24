from pydantic import BaseModel

class CoordinatorAgentRequest(BaseModel):
    user_input: str
    user_id:str