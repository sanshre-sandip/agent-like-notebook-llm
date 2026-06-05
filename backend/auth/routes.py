from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from .google_oauth import get_google_auth_flow, verify_google_token
from ..utils.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def login(request: Request):
    flow = get_google_auth_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )
    request.session["state"] = state
    return RedirectResponse(authorization_url)

@router.get("/callback")
async def callback(request: Request):
    state = request.session.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="Missing state")
    
    flow = get_google_auth_flow()
    try:
        flow.fetch_token(authorization_response=str(request.url))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {str(e)}")
    
    credentials = flow.credentials
    id_info = verify_google_token(credentials.id_token)
    
    # Store in session
    request.session["user_id"] = id_info["email"]
    request.session["user_name"] = id_info.get("name", "User")
    request.session["is_authenticated"] = True
    
    return RedirectResponse(url=settings.FRONTEND_URL)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}

@router.get("/user")
async def get_user(request: Request):
    if not request.session.get("is_authenticated"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "email": request.session["user_id"],
        "name": request.session["user_name"]
    }
