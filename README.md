# 🤖 Multi-Tenant RAG System

> **Ask AI questions about your own private documents — securely and separately for every user!**

---

## 📖 What is this? (Simply explained)

Imagine you have an important PDF — like a resume, company policy, research paper, or any document. Now you want to **ask AI questions about that document** — without sharing it with ChatGPT or any external AI service.

**That's exactly what this system does!**

- 📄 Upload your own PDF
- 🔐 Only you can see your data — no one else
- 💬 Ask questions directly from your document
- ☁️ Everything stored securely in the cloud

---

## 🧠 What is RAG? (Beginner friendly)

**RAG = Retrieval Augmented Generation**

In simple words:
```
Normal AI  →  Answers only from its training data
RAG AI     →  First reads YOUR document, THEN gives the answer
```

**Example:**
- You have your company's HR policy PDF
- You ask: "How many sick leaves do I get?"
- Normal ChatGPT: "I don't know your company's policy"
- RAG System: "According to your policy, you get 12 sick leaves per year" ✅

---

## 🏗️ System Architecture

```
User
  ↓
FastAPI Backend (Python)
  ↓              ↓
Supabase DB    pgvector
(Users &       (PDF
Documents)      Vectors)
  ↑
Groq AI (LLaMA 70B model)
```

### Tech Stack

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Backend API (Python web framework) |
| **PostgreSQL** | Database (storing users and documents) |
| **Supabase** | Cloud database hosting |
| **pgvector** | Storing PDF embeddings/vectors |
| **LangChain** | Building the RAG pipeline |
| **HuggingFace** | Converting text to vectors (embeddings) |
| **Groq + LLaMA 70B** | AI model for generating answers |
| **JWT** | Secure authentication system |
| **bcrypt** | Password hashing |

---

## 📁 Project Structure

```
MultiTenant-RAG/
│
├── multiTenantrag.py        # Main FastAPI app — all API endpoints
├── superbase_database.py    # Database models and connection
├── .env                     # Secret keys (never push to GitHub!)
├── requirements.txt         # Python dependencies
├── Procfile                 # For deployment (Render/Railway)
│
├── uploads/                 # PDFs temporarily saved here during processing
│   └── (after processing, vectors go to Supabase — local file not needed)
│
└── README.md                # This file!
```

---

## ⚙️ Local Setup (Step by Step)

### Step 1: Prerequisites

Make sure these are installed:
- [Python 3.10+](https://python.org)
- [Git](https://git-scm.com)

### Step 2: Clone the Repository

```bash
git clone https://github.com/AnshuKumari09/MultiTenant-RAG.git
cd MultiTenant-RAG
```

### Step 3: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Create Required Accounts (All Free!)

**1. Supabase** (Database) → [supabase.com](https://supabase.com)
   - Create a new project
   - Go to SQL Editor and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
   - Copy the connection string from Settings → Database

**2. Groq** (AI Model) → [console.groq.com](https://console.groq.com)
   - Create a free account
   - Generate an API key

**3. HuggingFace** (Embeddings) → [huggingface.co](https://huggingface.co)
   - Create a free account
   - Go to Settings → Access Tokens → Create new token

### Step 6: Create .env File

Create a `.env` file in the project root:

```env
DATABASE_URL="postgresql://postgres.YOUR_PROJECT:YOUR_PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
SECRET_KEY="any-long-random-string-here"
GROQ_API_KEY="gsk_your_groq_api_key"
HF_TOKEN="hf_your_huggingface_token"
```

> ⚠️ **IMPORTANT:** Never push the `.env` file to GitHub — it contains secret keys!

### Step 7: Start the Server

```bash
uvicorn multiTenantrag:app --reload
```

Open in browser: **http://127.0.0.1:8000/docs**

---

## 🚀 How to Use

### Using Swagger UI (Easiest Way)

Open `http://127.0.0.1:8000/docs` in your browser — you can test everything interactively.

### Step-by-Step Flow

**1️⃣ Register**
```json
POST /register
{
  "username": "john",
  "password": "john123",
  "full_name": "John Doe",
  "email": "john@example.com"
}
```

**2️⃣ Login → Get Token**
```
POST /token
username: john
password: john123

→ You will receive an access_token in response (keep it safe!)
```

**3️⃣ Upload PDF**
```
POST /upload
Authorization: Bearer {your_token}
collection_name: my_resume   (no spaces — use underscore)
file: [select your PDF]
```

**4️⃣ Ask Questions!**
```json
POST /query
Authorization: Bearer {your_token}
{
  "collection_name": "my_resume",
  "question": "What is the candidate name?"
}
```

**5️⃣ View Your Collections**
```
GET /my-collections
Authorization: Bearer {your_token}
```

---

## 🔐 What is Multi-Tenant?

**Multi-Tenant** = One system, many users — but everyone's data stays completely separate!

```
User: Alice
  → alice_resume (PDF)
  → alice_policy (PDF)

User: Bob
  → bob_contract (PDF)
  → bob_notes (PDF)

Alice cannot see Bob's data ✅
Bob cannot see Alice's data ✅
```

This architecture is used by real companies — like Google Drive, Dropbox, Notion, etc.

---

## 📊 Where is Data Stored?

| Data | Location |
|------|----------|
| User details (name, email, password) | Supabase → `users` table |
| Document metadata | Supabase → `documents` table |
| PDF vectors (AI readable format) | Supabase → `langchain_pg_embedding` table |
| PDF file (original) | Local `uploads/` folder (temporary only) |

> **Note:** Passwords are never stored as plain text — bcrypt hashing is used. Your actual password is never in the database, only its encrypted version.

---

## 🛠️ API Endpoints

| Method | Endpoint | Purpose | Auth Required? |
|--------|----------|---------|----------------|
| GET | `/` | System info & stats | ❌ |
| POST | `/register` | Create new user | ❌ |
| POST | `/token` | Login → get token | ❌ |
| POST | `/upload` | Upload PDF | ✅ |
| POST | `/query` | Ask question from document | ✅ |
| GET | `/my-collections` | View all your PDFs | ✅ |
| GET | `/me` | View your profile | ✅ |

---

## ❓ Common Issues & Fixes

**Issue:** `collection_id does not exist` error
```sql
-- Run this in Supabase SQL Editor:
ALTER TABLE documents ADD COLUMN IF NOT EXISTS collection_id VARCHAR(200) UNIQUE;
```

**Issue:** Space error on upload
```
collection_name cannot have spaces
❌ "my resume"
✅ "my_resume"
```

**Issue:** Token expired
```
Solution: Login again via /token to get a new token
```

**Issue:** Database not connecting
```python
# Make sure this is in superbase_database.py:
connect_args={"sslmode": "require"}
```

---

## 🌐 Real World Use Cases

- 🏢 **Company HR Chatbot** — "What is our leave policy?"
- ⚖️ **Law Firm** — Query legal documents with AI
- 🏥 **Hospital** — Query patient records securely
- 📚 **Education** — Ask questions from study material
- 💼 **Resume Screener** — Analyze candidate resumes

---

## 🎓 What I Learned Building This

- ✅ **REST API Development** — Building production-ready APIs with FastAPI
- ✅ **JWT Authentication** — Secure stateless login system
- ✅ **RAG Pipeline** — Document-based AI using LangChain
- ✅ **Vector Database** — Storing and querying embeddings with pgvector
- ✅ **Multi-tenant Architecture** — Keeping user data isolated
- ✅ **Cloud Database** — Using Supabase PostgreSQL
- ✅ **Password Security** — bcrypt hashing

---

## 👩‍💻 Developer

**Anshu Kumari**
- GitHub: [@AnshuKumari09](https://github.com/AnshuKumari09)

---

## 📄 License

MIT License — free to use!

---

> 💡 **Tip:** Go to `/docs` endpoint for interactive API documentation where you can test everything directly!
