# """
# Database models and connection - PostgreSQL + pgvector
# """
# from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
# from sqlalchemy.orm import declarative_base
# from sqlalchemy.orm import sessionmaker, relationship
# from datetime import datetime
# import os
# from dotenv import load_dotenv

# load_dotenv()

# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "postgresql://postgres:password@localhost:5432/multitenant_rag"
# )

# # PostgreSQL engine — Supabase ke liye pool_pre_ping zaroori hai
# engine = create_engine(
#     DATABASE_URL,
#     pool_size=5,
#     max_overflow=10,
#     pool_timeout=30,
#     pool_pre_ping=True
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()


# # ============================================
# # MODELS
# # ============================================

# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String(50), unique=True, index=True, nullable=False)
#     email = Column(String(100), unique=True, index=True, nullable=False)
#     password = Column(String(255), nullable=False)
#     full_name = Column(String(100), nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)

#     documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")

#     def __repr__(self):
#         return f"<User(username='{self.username}', email='{self.email}')>"


# class Document(Base):
#     __tablename__ = "documents"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     collection_name = Column(String(100), index=True, nullable=False)
#     pdf_path = Column(String(500), nullable=False)

#     # pgvector use karega — yeh collection identifier hai
#     # format: username_collectionname
#     collection_id = Column(String(200), unique=True, nullable=False)

#     created_at = Column(DateTime, default=datetime.utcnow)

#     owner = relationship("User", back_populates="documents")

#     def __repr__(self):
#         return f"<Document(collection='{self.collection_name}', user_id={self.user_id})>"


# # ============================================
# # HELPER FUNCTIONS
# # ============================================

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# def init_db():
#     print("Connecting to PostgreSQL (Supabase)...")
#     Base.metadata.create_all(bind=engine)
#     print("✅ Tables created!")
#     print("📊 Supabase dashboard mein tables dikhenge")


# if __name__ == "__main__":
#     init_db()

# from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
# from sqlalchemy.orm import declarative_base, sessionmaker, relationship
# from datetime import datetime
# import os
# from dotenv import load_dotenv

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")

# # SSL zaroori hai Supabase ke liye — yahi fix hai
# engine = create_engine(
#     DATABASE_URL,
#     pool_size=5,
#     max_overflow=10,
#     pool_timeout=30,
#     pool_pre_ping=True,
#     connect_args={"sslmode": "require"}  # ← Yeh line missing thi!
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String(50), unique=True, index=True, nullable=False)
#     email = Column(String(100), unique=True, index=True, nullable=False)
#     password = Column(String(255), nullable=False)
#     full_name = Column(String(100), nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")

# class Document(Base):
#     __tablename__ = "documents"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     collection_name = Column(String(100), index=True, nullable=False)
#     pdf_path = Column(String(500), nullable=False)
#     collection_id = Column(String(200), unique=True, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     owner = relationship("User", back_populates="documents")

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# def init_db():
#     print("Connecting to PostgreSQL (Supabase)...")
#     Base.metadata.create_all(bind=engine)
#     print("✅ Tables created!")

# if __name__ == "__main__":

#     init_db()


from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    collection_name = Column(String(100), index=True, nullable=False)
    pdf_path = Column(String(500), nullable=False)
    collection_id = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="documents")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    print("Connecting to PostgreSQL (Supabase)...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created!")

if __name__ == "__main__":
    init_db()
