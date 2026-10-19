from fastapi import APIRouter

# Definition of router
router = APIRouter(prefix="/test", tags=["test"])

# Test endpoint
@router.get("/")
def test() -> dict[str, str]:
    return {"Test": "Test"}