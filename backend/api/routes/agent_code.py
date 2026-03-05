from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def get_agents():
    return {"message": "Agents endpoint placeholder"}
