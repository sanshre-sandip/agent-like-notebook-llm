from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from .service import get_google_auth_flow, verify_google_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def login(request: Request):
    # Use the base URL of the request as the redirect URI
    redirect_uri = f"{request.base_url}auth/callback"
    flow = get_google_auth_flow(redirect_uri)
    authorization_url, state = flow.authorization_url()
    
    # Store state in session to prevent CSRF
    request.session["state"] = state
    return RedirectResponse(authorization_url)

@router.get("/callback")
async def callback(request: Request):
    state = request.session.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="State not found in session.")
    
    redirect_uri = f"{request.base_url}auth/callback"
    flow = get_google_auth_flow(redirect_uri)
    
    try:
        flow.fetch_token(authorization_response=str(request.url))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch token: {str(e)}")
    
    credentials = flow.credentials
    id_info = verify_google_token(credentials.id_token)
    
    # Store user info in session
    request.session["user_email"] = id_info.get("email")
    request.session["user_name"] = id_info.get("name")
    request.session["user_id"] = id_info.get("sub")
    
    # Redirect to frontend (adjust as needed for production)
    return RedirectResponse(url="http://localhost:5173")

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_me(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "email": user_email,
        "name": request.session.get("user_name"),
        "id": request.session.get("user_id")
    }
