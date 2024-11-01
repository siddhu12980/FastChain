from pydantic import BaseModel

class TransactionRequest(BaseModel):
    sender: str
    receiver: str
    amount: float

class BalanceRequest(BaseModel):
    receiver: str
    amount: float