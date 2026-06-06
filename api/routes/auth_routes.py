''' Auth routes '''
import jwt
import httpx
from fastapi import Depends, APIRouter, HTTPException, Header, Request
from sqlalchemy.orm import Session
from api.db import schemas
from api.db.database import get_db
from api.config.constants import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_TIME_MINUTES, OPA_RBAC_CONFIG_NAME, OPA_RBAC_RULE_NAME, GOOGLE_CLIENT_ID
import api.db.crud.user_crud as UserRepository
from api.db.crud.role_crud import get_roles_by_user
from api.clients.opa_client import check_policy

http_client = httpx.AsyncClient()
authRouter = APIRouter()


@authRouter.post("/login", tags=["Auth"], description="Login to get an authentication token")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    ''' Login to get an authentication token '''

    db_user = UserRepository.login(db, user=user)
    if db_user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not db_user.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")

    # Get user roles
    roles = get_roles_by_user(db, db_user)
    user_roles = {db_user.email: [role.name for role in roles]}

    # Generate JWT
    payload = {"user_id": db_user.id, "email": db_user.email,
               "roles": user_roles.get(db_user.email)}

    # Create JWT token
    access_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {"access_token":  access_token, "token_type": "bearer", "expires_in": JWT_EXPIRATION_TIME_MINUTES}


@authRouter.post("/register", tags=["Auth"], description="Register a new user")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    ''' Register a new user '''

    db_user = UserRepository.get_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    UserRepository.register(db=db, user=user)
    return {"message": "User created successfully"}


def decode_token(token: str, jwt_secret: str, jwt_algorithm: str):
    ''' Decode JWT token '''
    try:
        token = token.split(" ")[1]
        payload = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        return payload
    except jwt.exceptions.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    
@authRouter.post("/google", tags=["Auth"], description="Login using Google Access Token")
async def google_login(payload: schemas.UserLoginGoogle, db: Session = Depends(get_db)):
    ''' Valida el access_token de Google, registra o loguea al usuario, y emite un JWT propio '''
    token_info_url = f"https://oauth2.googleapis.com/tokeninfo?access_token={payload.access_token}"
    try:
        response = await http_client.get(token_info_url)
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google token")
        google_data = response.json()
        
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Could not validate Google token") from exc

    token_audience = google_data.get("aud") or google_data.get("azp")
    print ("Google token audience:", GOOGLE_CLIENT_ID, "Token audience from Google:", token_audience)
    if token_audience != GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Token target audience mismatch")

    email = google_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google token does not contain email profile info")

    db_user = UserRepository.get_by_email(db, email=email)
    if not db_user:
        import secrets
        random_password = secrets.token_hex(16)
        
        username = email.split("@")[0]
        new_user_data = schemas.UserCreate(
            email=email,
            password=random_password,
            full_name=username,
        )
        db_user = UserRepository.register(db=db, user=new_user_data)
    

    if not db_user.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")

    roles = get_roles_by_user(db, db_user)
    user_roles = {db_user.email: [role.name for role in roles]}

    jwt_payload = {
        "user_id": db_user.id, 
        "email": db_user.email,
        "roles": user_roles.get(db_user.email)
    }

    access_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "expires_in": JWT_EXPIRATION_TIME_MINUTES
    }

async def verify_jwt(request: Request, Authorization: str = Header(...), db: Session = Depends(get_db)):
    ''' Verify JWT token '''
    payload = decode_token(Authorization, JWT_SECRET, JWT_ALGORITHM)
    user_id = payload.get("user_id")
    db_user = UserRepository.get_by_id(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=401, detail="Invalid user")
    is_allowed = await verify_permissions(payload.get("roles"), request.url.path, request.method)
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Forbidden")
    return db_user


async def verify_permissions(roles: list, route: str, method: str):
    ''' Verify user permissions '''
    route = route.split("/api")[1]
    route = route.split("/")[2]
    input_data = {
        "input": {
            "roles": roles,
            "action": method,
            "object": route.upper()
        }
    }
    #OPA_RBAC_CONFIG_NAME Cambia si lo actualizamos
    print("Verificando permisos con política:", OPA_RBAC_CONFIG_NAME)
    return check_policy(OPA_RBAC_CONFIG_NAME, OPA_RBAC_RULE_NAME, input_data).get("result")
