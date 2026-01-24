''' Auth routes '''
import jwt
from fastapi import Depends, APIRouter, HTTPException, Header, Request
from sqlalchemy.orm import Session
from api.db import schemas
from api.db.database import get_db
from api.config.constants import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_TIME_MINUTES, OPA_RBAC_CONFIG_NAME, OPA_RBAC_RULE_NAME
import api.db.crud.user_crud as UserRepository
from api.db.crud.role_crud import get_roles_by_user
from api.clients.opa_client import check_policy

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
