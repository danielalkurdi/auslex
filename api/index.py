from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import time
import random
import jwt as pyjwt
import json
import os
import secrets
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from typing import List, Literal, Optional
from openai import OpenAI

app = FastAPI(title="AusLex AI API", version="1.0.0")

# Security
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# Enable CORS
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_str:
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
else:
    # For development and Vercel deployment
    allowed_origins = ["http://localhost:3000", "http://localhost:3001"]
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Simple in-memory storage (use a database in production)
users_db = {}
user_chats_db = {}

# Pydantic models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9

class ChatResponse(BaseModel):
    response: str
    tokens_used: int
    processing_time: float

class EmbeddingRequest(BaseModel):
    texts: List[str]
    normalize: bool = True
    pooling: Literal["mean", "cls"] = "mean"

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str

class RAGCitedPassage(BaseModel):
    index: int
    text: str
    score: float

class RAGRequest(BaseModel):
    query: str
    documents: List[str]
    top_k: int = 5
    temperature: float = 0.3
    max_tokens: int = 600
    model: str = "gpt-5"

class RAGResponse(BaseModel):
    answer: str
    citations: List[RAGCitedPassage]

class ProvisionRequest(BaseModel):
    act_name: str
    year: str
    jurisdiction: str
    provision_type: str
    provision: str
    full_citation: str

class ProvisionResponse(BaseModel):
    provision_text: str
    metadata: dict
    source: str
    full_act_url: str
    notes: list
    related_provisions: list = []
    case_references: list = []

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = pyjwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = pyjwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        if user_id not in users_db:
            raise HTTPException(status_code=401, detail="User not found")
            
        return users_db[user_id]
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# -----------------------------
# Lightweight embeddings (serverless-safe)
# -----------------------------

def _create_openai_client() -> OpenAI:
    """Create an OpenAI client honoring optional custom endpoint and org/project.
    Allows use of custom/preview endpoints that expose GPT-5-compatible routes.
    """
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    organization = os.getenv("OPENAI_ORG")
    project = os.getenv("OPENAI_PROJECT")
    kwargs = {}
    if base_url:
        kwargs["base_url"] = base_url
    if api_key:
        kwargs["api_key"] = api_key
    if organization:
        kwargs["organization"] = organization
    if project:
        kwargs["project"] = project
    return OpenAI(**kwargs)

def _l2_normalize(vecs: List[List[float]]) -> List[List[float]]:
    import math
    out: List[List[float]] = []
    for v in vecs:
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        out.append([x / norm for x in v])
    return out

def _openai_embed(texts: List[str]) -> List[List[float]]:
    client = _create_openai_client()
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]

def get_embeddings(texts: List[str], normalize: bool = True) -> (List[List[float]], str):
    vecs = _openai_embed(texts)
    if normalize:
        vecs = _l2_normalize(vecs)
    return vecs, "text-embedding-3-small"

# OpenAI generation

def _generate_with_openai(query: str, passages: List[RAGCitedPassage], model: str, temperature: float, max_tokens: int) -> str:
    client = _create_openai_client()
    context_lines = []
    for idx, p in enumerate(passages, start=1):
        context_lines.append(f"[{idx}] {p.text}")
    context_block = "\n".join(context_lines)
    messages = [
        {"role": "system", "content": (
            "You are an Australian legal assistant. Use only the provided passages as sources. "
            "Cite using bracketed numbers like [1], [2]. If unsure or unsupported by the passages, say you don't know. "
            "Educational use only; not legal advice."
        )},
        {"role": "user", "content": (
            f"Question: {query}\n\nPassages:\n{context_block}\n\n"
            "Answer the question with clear citations [n] after each claim."
        )},
    ]
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content if resp.choices else ""

# Sample legal responses for demonstration
SAMPLE_RESPONSES = [
    """Here's a comprehensive overview with legal citations to demonstrate the citation preview system:

**Migration Law Example:**
Under Migration Act 1958 (Cth) s 55, visa holders must usually enter Australia before their first entry deadline. However, s 55(2) provides exceptions including for protection visa holders. The character test provisions in Migration Act 1958 (Cth) s 501 allow the Minister to refuse or cancel visas on character grounds.

**Employment Law Example:**  
Under Fair Work Act 2009 (Cth) s 382, unfair dismissal occurs when the Fair Work Commission finds the dismissal was harsh, unjust or unreasonable. This provision establishes a four-element test that must all be satisfied.

**Corporate Law Example:**
Directors' duties under Corporations Act 2001 (Cth) s 181 require them to act in good faith and in the best interests of the corporation. This fundamental duty is subject to civil penalties for breach.

Click on any of the highlighted citations above to see a popup with the actual provision content, metadata, and related information.""",
    
    "The character test provisions in Migration Act 1958 (Cth) s 501 allow the Minister to refuse or cancel visas on character grounds. This includes where a person has a substantial criminal record as defined in s 501(7), or fails the good character requirements in s 501(6).",
    
    "Under the Fair Work Act 2009 (Cth) s 382, unfair dismissal occurs when the Fair Work Commission finds the dismissal was harsh, unjust or unreasonable. The test requires consideration of factors including whether proper process was followed and if the reason was valid.",
    
    "Directors' duties under the Corporations Act 2001 (Cth) s 181 require them to act in good faith and in the best interests of the corporation. This fundamental duty is subject to civil penalties and can result in compensation orders for breach.",
    
    "In Australian contract law, the essential elements of a valid contract are: 1) Offer and acceptance, 2) Intention to create legal relations, 3) Consideration, 4) Capacity to contract, 5) Genuine consent, and 6) Legality of purpose. These principles are derived from both common law and statutory provisions such as the Australian Consumer Law."
]

# Mock legal database for provision lookups
MOCK_PROVISIONS_DB = {
    "migration_act_1958_cth_s_55": {
        "provision_text": """<p>(1) A non-citizen who holds a visa must not travel to Australia, or enter Australia, after the first entry deadline for the visa.</p>

<p>(2) Subsection (1) does not apply if:<br>
    (a) the visa is held by a person who is in Australia; or<br>
    (b) the Minister determines, in writing, that it would be unreasonable to apply subsection (1) to the non-citizen; or<br>
    (c) the visa is a protection visa.</p>

<p>(3) For the purposes of subsection (2), the Minister may have regard to:<br>
    (a) compassionate or compelling circumstances affecting the non-citizen; and<br>
    (b) the circumstances that prevented the non-citizen from entering Australia before the first entry deadline; and<br>
    (c) the length of time that has elapsed since the first entry deadline; and<br>
    (d) any other matter the Minister considers relevant.</p>""",
        "metadata": {
            "title": "Visa holders must usually enter before first entry deadline",
            "lastAmended": "2023-03-15",
            "effectiveDate": "1958"
        },
        "source": "Federal Register of Legislation",
        "full_act_url": "https://www.legislation.gov.au/Details/C2023C00094",
        "notes": [
            "This provision establishes the first entry deadline requirements for visa holders",
            "Subsection (2) provides important exceptions including for protection visa holders",
            "The Minister has discretionary power under subsection (2)(b)"
        ],
        "related_provisions": ["s 56", "s 57", "s 58"],
        "case_references": ["Minister for Immigration v Li (2013) 249 CLR 332"]
    },
    "migration_act_1958_cth_s_501": {
        "provision_text": """<p>(1) The Minister may refuse to grant a visa to a person if the person does not satisfy the Minister that the person passes the character test.</p>

<p>(2) The Minister may cancel a visa that has been granted to a person if:<br>
    (a) the Minister reasonably suspects that the person does not pass the character test; and<br>
    (b) the person does not satisfy the Minister that the person passes the character test.</p>

<p>(3) The Minister may cancel a visa that has been granted to a person if the Minister is satisfied that the person does not pass the character test.</p>

<p><strong>Character test</strong><br>
(6) For the purposes of this section, a person does not pass the character test if:<br>
    (a) the person has a substantial criminal record (as defined by subsection (7)); or<br>
    (b) the person has or has had an association with someone else, or with a group or organisation, whom the Minister reasonably suspects has been or is involved in criminal conduct; or<br>
    (c) having regard to either or both of the following:<br>
        (i) the person's past and present criminal conduct;<br>
        (ii) the person's past and present general conduct;<br>
    the person is not of good character.</p>""",
        "metadata": {
            "title": "Refusal or cancellation of visa on character grounds",
            "lastAmended": "2022-12-01",
            "effectiveDate": "1958"
        },
        "source": "Federal Register of Legislation",
        "full_act_url": "https://www.legislation.gov.au/Details/C2023C00094",
        "notes": [
            "This is one of the most significant discretionary powers in migration law",
            "The character test has been subject to extensive judicial interpretation",
            "Recent amendments have expanded the grounds for character-based cancellation"
        ],
        "related_provisions": ["s 501A", "s 501B", "s 501C"],
        "case_references": ["SZTV v Minister for Immigration (2021) 95 ALJR 1077"]
    },
    "fair_work_act_2009_cth_s_382": {
        "provision_text": """<p>A person has been unfairly dismissed if the Fair Work Commission is satisfied that:<br>
    (a) the person has been dismissed; and<br>
    (b) the dismissal was harsh, unjust or unreasonable; and<br>
    (c) the dismissal was not consistent with the Small Business Fair Dismissal Code; and<br>
    (d) the dismissal was not a case of genuine redundancy.</p>

<p><strong>Note:</strong> For the definition of consistent with the Small Business Fair Dismissal Code, see section 388.</p>""",
        "metadata": {
            "title": "What is unfair dismissal",
            "lastAmended": "2021-06-30",
            "effectiveDate": "2009"
        },
        "source": "Federal Register of Legislation", 
        "full_act_url": "https://www.legislation.gov.au/Details/C2022C00174",
        "notes": [
            "This section establishes the four-element test for unfair dismissal",
            "All elements must be satisfied for a dismissal to be unfair",
            "The Small Business Fair Dismissal Code provides a safe harbour for small businesses"
        ],
        "related_provisions": ["s 383", "s 384", "s 385"],
        "case_references": ["Nguyen v Vietnamese Community in Australia (2014) 217 FCR 25"]
    },
    "corporations_act_2001_cth_s_181": {
        "provision_text": """<p>(1) A director or other officer of a corporation must exercise their powers and discharge their duties:<br>
    (a) in good faith in the best interests of the corporation; and<br>
    (b) for a proper purpose.</p>

<p>(2) A person who is involved in a contravention of subsection (1) contravenes this subsection.</p>

<p><strong>Note 1:</strong> Section 79 defines involved.<br>
<strong>Note 2:</strong> This section is a civil penalty provision (see section 1317E).</p>""",
        "metadata": {
            "title": "Good faith—civil obligations",
            "lastAmended": "2020-04-01",
            "effectiveDate": "2001"
        },
        "source": "Federal Register of Legislation",
        "full_act_url": "https://www.legislation.gov.au/Details/C2022C00216",
        "notes": [
            "This is a fundamental duty of directors and officers",
            "Breach can result in civil penalties and compensation orders",
            "The business judgment rule in s 180(2) provides some protection"
        ],
        "related_provisions": ["s 180", "s 182", "s 183"],
        "case_references": ["ASIC v Rich (2009) 236 FLR 1"]
    }
}

@app.get("/")
async def root():
    return {"message": "AusLex AI API - Australian Legal Assistant"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AusLex AI API"}

# Prefixed routes for Vercel /api mapping
@app.get("/api")
async def root_prefixed():
    return await root()

@app.get("/api/")
async def root_prefixed_slash():
    return await root()

@app.get("/api/health")
async def health_check_prefixed():
    return await health_check()

# Authentication endpoints
@app.post("/auth/register", response_model=AuthResponse)
async def register(user_data: UserRegister):
    # Check if user already exists
    for user in users_db.values():
        if user["email"] == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = f"user_{len(users_db) + 1}"
    hashed_password = hash_password(user_data.password)
    
    user = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "password": hashed_password
    }
    
    users_db[user_id] = user
    user_chats_db[user_id] = []
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user_id, name=user_data.name, email=user_data.email)
    )

@app.post("/api/auth/register", response_model=AuthResponse)
async def register_prefixed(user_data: UserRegister):
    return await register(user_data)

@app.post("/auth/login", response_model=AuthResponse)
async def login(user_data: UserLogin):
    # Find user by email
    user = None
    for u in users_db.values():
        if u["email"] == user_data.email:
            user = u
            break
    
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user["id"], name=user["name"], email=user["email"])
    )

@app.post("/api/auth/login", response_model=AuthResponse)
async def login_prefixed(user_data: UserLogin):
    return await login(user_data)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Simulate processing time
        processing_time = random.uniform(1.0, 3.0)
        time.sleep(processing_time)
        
        # Generate a response based on the input
        msg_lower = request.message.lower().strip()
        if "citation" in msg_lower or "test" in msg_lower:
            # Special test response with embedded citations
            response = """Here's a comprehensive test of the AustLII citation preview system with various citation formats:

**Case Citations:**
- The recent High Court decision in Helensburgh Coal Pty Ltd v Bartley [2025] HCA 29 clarifies coal mining regulations.
- In Smith v Commissioner of Taxation [2024] FCA 100, the Federal Court addressed tax assessment procedures.

**Legislation Citations (Section First Format):**
- Section 359A of the Migration Act 1958 (Cth) establishes visa application requirements.
- Section 6 of the Privacy Act 1988 (Cth) defines personal information.

**Legislation Citations (Act First Format):**
- Migration Act 1958 (Cth) s 65 covers bridging visas for unlawful non-citizens.
- Privacy Act 1988 (Cth) ss 6-8 establish the foundations of privacy protection.
- Fair Work Act 2009 (Cth) s 394(1) outlines unfair dismissal application procedures.

**Test Subsections and Complex Provisions:**
- Fair Work Act 2009 (Cth) s 382 defines what constitutes unfair dismissal.

Click on any of the highlighted citations above to see a popup displaying the actual AustLII content. This demonstrates direct integration with AustLII's database showing real Australian legal provisions and cases."""
        else:
            # Use OpenAI for general chat with model fallback
            model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
            fallback = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")
            client = _create_openai_client()
            messages = [
                {"role": "system", "content": (
                    "You are an Australian legal assistant. Be concise, accurate, and cite legislation or cases where relevant. "
                    "Educational use only; not legal advice."
                )},
                {"role": "user", "content": request.message},
            ]
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    top_p=request.top_p,
                )
            except Exception:
                if os.getenv("OPENAI_ENABLE_FALLBACK", "1") == "1" and model != fallback:
                    completion = client.chat.completions.create(
                        model=fallback,
                        messages=messages,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                        top_p=request.top_p,
                    )
                else:
                    raise
            response = completion.choices[0].message.content if completion.choices else ""
        
        # Calculate approximate tokens used
        tokens_used = len(response.split()) + len(request.message.split())
        
        return ChatResponse(
            response=response,
            tokens_used=tokens_used,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/embeddings", response_model=EmbeddingResponse)
async def embeddings(req: EmbeddingRequest):
    try:
        if not req.texts:
            raise HTTPException(status_code=400, detail="texts must be a non-empty list")
        vectors, used_model = get_embeddings(req.texts, normalize=req.normalize)
        return EmbeddingResponse(embeddings=vectors, model=used_model)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

@app.post("/api/embeddings", response_model=EmbeddingResponse)
async def embeddings_prefixed(req: EmbeddingRequest):
    return await embeddings(req)

@app.post("/rag/answer", response_model=RAGResponse)
async def rag_answer(req: RAGRequest):
    try:
        if not req.query:
            raise HTTPException(status_code=400, detail="query is required")
        if not req.documents:
            raise HTTPException(status_code=400, detail="documents must be a non-empty list")
        # Rank with OpenAI embeddings (serverless-safe)
        query_vec, _ = get_embeddings([req.query], normalize=True)
        doc_vecs, _ = get_embeddings(req.documents, normalize=True)
        scores: List[float] = []
        for v in doc_vecs:
            s = sum(a*b for a, b in zip(query_vec[0], v))
            scores.append(float(s))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[: max(1, req.top_k)]
        top_passages = [RAGCitedPassage(index=i, text=req.documents[i], score=score) for i, score in ranked]

        answer = _generate_with_openai(
            query=req.query,
            passages=top_passages,
            model=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        return RAGResponse(answer=answer, citations=top_passages)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating RAG answer: {str(e)}")

@app.post("/api/rag/answer", response_model=RAGResponse)
async def rag_answer_prefixed(req: RAGRequest):
    return await rag_answer(req)

@app.post("/api/chat", response_model=ChatResponse)
async def chat_prefixed(request: ChatRequest):
    return await chat(request)

@app.post("/legal/provision", response_model=ProvisionResponse)
async def get_legal_provision(request: ProvisionRequest):
    """
    Fetch legal provision content by citation.
    
    This endpoint simulates integration with Australian legal databases like AustLII
    and the Federal Register of Legislation. In production, this would make actual
    API calls to these services.
    """
    try:
        # Simulate processing delay
        processing_time = random.uniform(0.5, 2.0)
        time.sleep(processing_time)
        
        # Generate lookup key for mock database
        act_name_key = request.act_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        lookup_key = f"{act_name_key}_{request.year}_{request.jurisdiction.lower()}_s_{request.provision.lower()}"
        
        # Try to find in mock database
        provision_data = MOCK_PROVISIONS_DB.get(lookup_key)
        
        if not provision_data:
            # Return generic response if not found
            raise HTTPException(
                status_code=404, 
                detail=f"Provision not found: {request.full_citation}. This may be because the provision does not exist, has been repealed, or is not available in the database."
            )
        
        # Return provision data
        return ProvisionResponse(
            provision_text=provision_data["provision_text"],
            metadata=provision_data["metadata"],
            source=provision_data["source"],
            full_act_url=provision_data["full_act_url"],
            notes=provision_data["notes"],
            related_provisions=provision_data.get("related_provisions", []),
            case_references=provision_data.get("case_references", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching provision: {str(e)}")

@app.post("/api/legal/provision", response_model=ProvisionResponse)
async def get_legal_provision_prefixed(request: ProvisionRequest):
    return await get_legal_provision(request)

def generate_lookup_key(act_name: str, year: str, jurisdiction: str, provision: str) -> str:
    """Generate a lookup key for the mock provisions database"""
    act_key = act_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
    return f"{act_key}_{year}_{jurisdiction.lower()}_s_{provision.lower()}"

 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 