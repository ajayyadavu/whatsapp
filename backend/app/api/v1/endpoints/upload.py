# # app/api/v1/endpoints/upload.py
# # PDF upload — ADMIN ONLY.
# # Pass the JWT token as Authorization: Bearer <token> header.
# # Regular users get 403 Forbidden.

# from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, status, Depends
# from sqlalchemy.orm import Session

# from app.services.rag_service import store_pdf
# from app.db.session import get_db
# from app.services.user_service import UserService
# from app.core.security import verify_token

# router = APIRouter()


# def _require_admin(authorization: str = Header(None), db: Session = Depends(get_db)):
#     """Dependency — raises 401/403 if caller is not an admin user."""
#     if not authorization or not authorization.startswith("Bearer "):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authentication required. Pass Authorization: Bearer <token>",
#         )
#     token = authorization.split(" ", 1)[1]
#     username = verify_token(token)
#     if not username:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token.",
#         )
#     user = UserService.get_user_by_username(db, username)
#     if not user or not user.is_admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Admin access required to upload documents.",
#         )
#     return user


# @router.post("/pdf")
# async def upload_pdf(
#     file: UploadFile = File(...),
#     session_id: str = Form(...),
#     _admin=Depends(_require_admin),
# ):
#     """
#     Chunk, embed and store a PDF into ChromaDB.
#     Only accessible by admin users.
#     session_id controls which ChromaDB collection the PDF goes into.
#     Use session_id='swaransoft_website' to add it to the global knowledge base
#     so ALL users benefit from it, or pass a user session_id for per-session docs.
#     """
#     contents = await file.read()
#     if not contents:
#         raise HTTPException(status_code=400, detail="Empty file.")

#     count = store_pdf(contents, file.filename, session_id)
#     if count == 0:
#         raise HTTPException(
#             status_code=422,
#             detail="Could not extract text from PDF. Make sure it has selectable text.",
#         )

#     return {
#         "message": f"{file.filename} uploaded successfully.",
#         "chunks_stored": count,
#         "collection": session_id,
#     }



# from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, status, Depends
# from sqlalchemy.orm import Session

# from app.services.rag_service import store_pdf
# from app.db.session import get_db
# from app.services.user_service import UserService
# from app.core.security import verify_token

# router = APIRouter()


# def _require_admin(
#     authorization: str = Header(None),
#     db: Session = Depends(get_db)
# ):
#     """Check if user is admin using JWT token"""

#     # 🔐 Check Authorization header
#     if not authorization or not authorization.startswith("Bearer "):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authentication required. Use Bearer token",
#         )

#     # 🔑 Extract token
#     token = authorization.split(" ", 1)[1]

#     # 🔍 Verify token
#     username = verify_token(token)   # ✅ returns string now

#     if not username:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token",
#         )

#     # 👤 Get user from DB
#     user = UserService.get_user_by_username(db, username)

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found",
#         )

#     # 🛑 Check admin
#     if not user.is_admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Admin access required",
#         )

#     return user


# @router.post("/pdf")
# async def upload_pdf(
#     file: UploadFile = File(...),
#     session_id: str = Form(...),
#     _admin=Depends(_require_admin),
# ):
#     """Upload PDF (Admin only)"""

#     contents = await file.read()

#     if not contents:
#         raise HTTPException(status_code=400, detail="Empty file")

#     count = store_pdf(contents, file.filename, session_id)

#     if count == 0:
#         raise HTTPException(
#             status_code=422,
#             detail="Could not extract text from PDF",
#         )

#     return {
#         "message": f"{file.filename} uploaded successfully",
#         "chunks_stored": count,
#         "collection": session_id,
#     }


from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.services.rag_service import store_pdf
from app.db.session import get_db
from app.services.user_service import UserService
from app.core.security import verify_token

router = APIRouter()


# ============================================================
# 🔐 ADMIN AUTH CHECK (FIXED VERSION)
# ============================================================
def _require_admin(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Check if user is admin using JWT token"""

    # 🔐 Check Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Use Bearer token",
        )

    # 🔑 Extract token
    token = authorization.split(" ", 1)[1]

    # 🔍 Verify token
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # ✅ HANDLE BOTH CASES (dict / string)
    if isinstance(payload, dict):
        username = payload.get("sub")
    else:
        username = payload

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    print(f"[AUTH] Token verified, username: {username}")

    # 👤 Get user from DB
    user = UserService.get_user_by_username(db, username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 🛑 Check admin
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    print(f"[AUTH] Admin verified: {username}")

    return user


# ============================================================
# 📄 PDF UPLOAD API
# ============================================================
@router.post("/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: str = Form("swaransoft_website"),  # default = global KB
    _admin=Depends(_require_admin),
):
    """Upload PDF (Admin only)"""

    print("\n================ PDF UPLOAD REQUEST ================\n")
    print(f"[UPLOAD] File: {file.filename}")
    print(f"[UPLOAD] Session ID: {session_id}")

    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    # 🚀 Store PDF in vector DB
    count = store_pdf(contents, file.filename, session_id)

    print(f"[UPLOAD RESULT] Stored chunks: {count}")

    if count == 0:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from PDF",
        )

    print("\n================ UPLOAD SUCCESS ====================\n")

    print(f"[UPLOAD SESSION] {session_id}")
    print(f"[CHAT SESSION] {session_id}")
    

    return {
        "message": f"{file.filename} uploaded successfully",
        "chunks_stored": count,
        "collection": session_id,
    }