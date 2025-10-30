from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .database import SessionLocal, engine
from .models import Base, User, Token
from .security import verify_password, hash_password, create_sso_token, verify_sso_token

from sqlalchemy.orm import Session
from sqlalchemy import select

app = FastAPI(title=settings.SITE_NAME)
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY, https_only=False)

templates = Jinja2Templates(directory="templates")

# Create DB tables if not exists
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "site_name": settings.SITE_NAME})


@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user: Optional[User] = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.password_hash) or not user.is_active:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "site_name": settings.SITE_NAME, "error": "Invalid credentials"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Set session for UI flow
    request.session["user_id"] = user.id
    request.session["email"] = user.email

    token, jti, expires_at = create_sso_token(user_id=user.id, email=user.email)

    # Persist token for revocation/validation
    db_token = Token(jti=jti, user_id=user.id, expires_at=expires_at.replace(tzinfo=None))
    db.add(db_token)
    db.commit()

    # redirect to home with token cookie set
    response = RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        "sso_token",
        token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
    )
    return response

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # Try read token from cookie and validate; if missing/invalid, mint a fresh token
    sso_token = request.cookies.get("sso_token")
    needs_new = True
    if sso_token:
        valid, payload, _ = verify_sso_token(sso_token)
        if valid and payload and str(payload.get("sub")) == str(user_id):
            # Check revocation/expiry in DB
            from sqlalchemy import select
            db_token = db.scalar(select(Token).where(Token.jti == payload.get("jti")))
            now_ts = datetime.now(timezone.utc).timestamp()
            if db_token and not db_token.revoked and (payload.get("exp") and now_ts < float(payload.get("exp"))):
                needs_new = False

    if needs_new:
        user = db.get(User, user_id)
        new_token, jti, expires_at = create_sso_token(user_id=user.id, email=user.email)
        db_token = Token(jti=jti, user_id=user.id, expires_at=expires_at.replace(tzinfo=None))
        db.add(db_token)
        db.commit()
        sso_token = new_token

    context = {"request": request, "email": request.session.get("email"), "sso_token": sso_token}
    response = templates.TemplateResponse("home.html", context)
    if needs_new:
        response.set_cookie(
        "sso_token",
        sso_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
    )
    return response


@app.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token.split(" ", 1)[1]
    else:
        token = request.cookies.get("sso_token")

    if token:
        valid, payload, _ = verify_sso_token(token)
        if valid and payload:
            jti = payload.get("jti")
            db_token: Optional[Token] = db.scalar(select(Token).where(Token.jti == jti))
            if db_token and not db_token.revoked:
                db_token.revoked = True
                db_token.revoked_at = datetime.utcnow()
                db.commit()

    request.session.clear()
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("sso_token", domain=settings.COOKIE_DOMAIN)
    return response


@app.post("/validate_token")
async def validate_token(token: Optional[str] = None, request: Request = None, db: Session = Depends(get_db)):
    if not token:
        # Try Authorization header or cookie
        auth = request.headers.get("Authorization") if request else None
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
        else:
            token = request.cookies.get("sso_token") if request else None

    if not token:
        return JSONResponse({"active": False, "reason": "missing_token"})

    valid, payload, err = verify_sso_token(token)
    if not valid or not payload:
        return JSONResponse({"active": False, "reason": "invalid_token", "detail": err})

    # Check revocation and expiry against DB
    jti = payload.get("jti")
    exp = payload.get("exp")

    db_token: Optional[Token] = db.scalar(select(Token).where(Token.jti == jti))
    now = datetime.now(timezone.utc).timestamp()

    if not db_token:
        return JSONResponse({"active": False, "reason": "unknown_jti"})
    if db_token.revoked:
        return JSONResponse({"active": False, "reason": "revoked"})
    if exp and now > float(exp):
        return JSONResponse({"active": False, "reason": "expired"})

    user: Optional[User] = db.get(User, int(payload.get("sub")))
    if not user or not user.is_active:
        return JSONResponse({"active": False, "reason": "user_inactive"})

    return JSONResponse({
        "active": True,
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "iat": payload.get("iat"),
        "exp": payload.get("exp"),
        "jti": payload.get("jti"),
        "user": {"id": user.id, "email": user.email},
    })


# Simple setup route to create a demo user if none exists (for PoC only)
@app.post("/setup_seed")
async def setup_seed(db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == "admin@example.com"))
    if existing:
        return {"created": False}
    user = User(email="admin@example.com", password_hash=hash_password("admin123"), is_active=True)
    db.add(user)
    db.commit()
    return {"created": True, "email": user.email, "password": "admin123"}
