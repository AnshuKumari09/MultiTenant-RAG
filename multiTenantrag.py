"""
Multi-Tenant RAG System
PostgreSQL + pgvector (FAISS replaced)
RAG token removed — Bearer token use hoga
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Database imports
from supabase_database import get_db, init_db, User, Document

# RAG imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

load_dotenv()

# ============================================
# CONFIGURATION
# ============================================
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 din

DATABASE_URL = os.getenv("DATABASE_URL")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ============================================
# FASTAPI APP
# ============================================
app = FastAPI(title="Multi-Tenant RAG System - pgvector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ============================================
# PYDANTIC MODELS
# ============================================
class UserRegister(BaseModel):
    username: str
    password: str
    full_name: str
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class QueryRequest(BaseModel):
    collection_name: str
    question: str

# ============================================
# AUTH FUNCTIONS
# ============================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired — please login again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ============================================
# RAG SETUP — pgvector
# ============================================
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile"
)

def get_collection_id(username: str, collection_name: str) -> str:
    """Unique collection ID — pgvector mein yahi table name hoga"""
    return f"{username}_{collection_name}"

def process_pdf_to_pgvector(pdf_path: str, collection_id: str):
    """PDF process karke pgvector mein store karo"""
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    if not docs:
        raise ValueError("PDF se content extract nahi hua. Text-based PDF honi chahiye.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    splits = splitter.split_documents(docs)

    if not splits:
        raise ValueError("PDF chunks nahi bane.")

    # pgvector mein store karo — Supabase PostgreSQL mein
    vectorstore = PGVector.from_documents(
        documents=splits,
        embedding=embedding_model,
        collection_name=collection_id,
        connection=DATABASE_URL,
        pre_delete_collection=True  # Agar same naam ka collection ho toh replace karo
    )
    return vectorstore

def load_pgvector_store(collection_id: str):
    """pgvector se existing collection load karo"""
    vectorstore = PGVector(
        embeddings=embedding_model,
        collection_name=collection_id,
        connection=DATABASE_URL,
    )
    return vectorstore

def query_rag(vectorstore, question: str) -> str:
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer ONLY from the provided context. If the answer is not in the context, say 'I don't know based on the provided document.'"),
        ("human", "Question: {question}\n\nContext:\n{context}")
    ])

    def format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)

    parallel = RunnableParallel({
        "context": retriever | RunnableLambda(format_docs),
        "question": RunnablePassthrough(),
    })
    chain = parallel | prompt | llm | StrOutputParser()
    return chain.invoke(question)

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_docs = db.query(Document).count()
    return {
        "message": "Multi-Tenant RAG System — pgvector",
        "database": "Supabase PostgreSQL + pgvector",
        "total_users": total_users,
        "total_documents": total_docs,
        "endpoints": {
            "1": "POST /register",
            "2": "POST /token",
            "3": "POST /upload  (Bearer token required)",
            "4": "POST /query   (Bearer token required)",
            "5": "GET  /me      (Bearer token required)",
            "6": "GET  /my-collections (Bearer token required)"
        }
    }


@app.post("/register", status_code=201)
async def register_user(user: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        username=user.username,
        email=user.email,
        password=pwd_context.hash(user.password),
        full_name=user.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully!",
        "username": new_user.username,
        "user_id": new_user.id
    }


@app.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/upload")
async def upload_pdf(
    collection_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validation
    if " " in collection_name:
        raise HTTPException(status_code=400, detail="Collection name mein spaces nahi — use underscore: my_doc")

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    collection_id = get_collection_id(current_user.username, collection_name)

    # Same collection already exists?
    if db.query(Document).filter(Document.collection_id == collection_id).first():
        raise HTTPException(status_code=400, detail="Collection name already exists. Choose a different name.")

    # PDF save karo locally (processing ke liye)
    pdf_path = UPLOAD_DIR / f"{collection_id}.pdf"
    with open(pdf_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # PDF process karke pgvector mein store karo
    try:
        process_pdf_to_pgvector(str(pdf_path), collection_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")

    # Document record save karo
    new_doc = Document(
        user_id=current_user.id,
        collection_name=collection_name,
        pdf_path=str(pdf_path),
        collection_id=collection_id
    )
    db.add(new_doc)
    db.commit()

    return {
        "message": "PDF processed successfully!",
        "collection_name": collection_name,
        "collection_id": collection_id
    }


@app.post("/query")
async def query_document(
    query: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    collection_id = get_collection_id(current_user.username, query.collection_name)

    # Document exists?
    doc = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.collection_name == query.collection_name
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail=f"Collection '{query.collection_name}' not found. Pehle PDF upload karo.")

    # pgvector se load karo
    try:
        vectorstore = load_pgvector_store(collection_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load vectorstore: {str(e)}")

    # Query karo
    try:
        answer = query_rag(vectorstore, query.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    return {
        "question": query.question,
        "answer": answer,
        "collection": query.collection_name
    }


@app.get("/my-collections")
async def get_my_collections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User ke saare uploaded collections dekho"""
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    return {
        "username": current_user.username,
        "total_collections": len(docs),
        "collections": [
            {
                "collection_name": d.collection_name,
                "created_at": d.created_at
            } for d in docs
        ]
    }


@app.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "registered_at": current_user.created_at,
        "total_documents": len(docs),
        "documents": [
            {
                "collection_name": d.collection_name,
                "created_at": d.created_at
            } for d in docs
        ]
    }


@app.on_event("startup")
async def startup():
    init_db()
    print("\n" + "="*55)
    print("Multi-Tenant RAG System — pgvector + Supabase")
    print("="*55)
    print("Vector Store: pgvector (Supabase PostgreSQL)")
    print("No more FAISS local files!")
    print("\nWorkflow:")
    print("1. Register: POST /register")
    print("2. Login:    POST /token  → Bearer token milega")
    print("3. Upload:   POST /upload  (Bearer token + collection_name)")
    print("4. Query:    POST /query   (Bearer token + collection_name + question)")
    print("\nDocs: http://127.0.0.1:8000/docs")

    print("="*55 + "\n")
