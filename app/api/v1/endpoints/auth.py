from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import bcrypt
from app.core.supabase import get_supabase_admin # Use Admin client
from typing import Optional

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    user: dict
    access_token: str

@router.post("/login", response_model=UserResponse)
async def login(request: LoginRequest):
    """
    Custom login endpoint validating against public.app_users table.
    Bypasses broken Supabase Auth schema.
    """
    print(f"Login attempt for: {request.email}")
    supabase = get_supabase_admin()
    
    # query user
    try:
        print("Querying public.app_users...")
        response = supabase.table("app_users").select("*").eq("email", request.email).execute()
        
        if not response.data:
            print("User not found in DB")
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        user = response.data[0]
        db_hash = user["password_hash"]
        
        # Verify password using bcrypt directly
        # Ensure we encode to bytes
        print("Verifying password with bcrypt...")
        password_bytes = request.password.encode('utf-8')
        
        # db_hash comes as a string ($2a$...), encode to bytes
        hash_bytes = db_hash.encode('utf-8')
        
        if not bcrypt.checkpw(password_bytes, hash_bytes):
            print("Password verification failed")
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        print("Login successful")
        # Construct response
        return {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "user_metadata": {
                    "full_name": user.get("full_name"),
                    "designation": user.get("designation")
                },
                "role": "authenticated"
            },
            "access_token": f"custom-backend-token-{user['id']}" # Dummy token for simple session
        }
        
    except Exception as e:
        # If it's the 401 we raised, re-raise it
        if isinstance(e, HTTPException):
            raise e
        # Log generic error and return 500
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")
