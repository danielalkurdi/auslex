from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import random

app = FastAPI(title="AusLex AI API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9

class ChatResponse(BaseModel):
    response: str
    tokens_used: int
    processing_time: float

# Sample legal responses for demonstration
SAMPLE_RESPONSES = [
    "In Australian tort law, the key elements of negligence are: 1) Duty of care, 2) Breach of duty, 3) Causation, and 4) Damage. The duty of care was established in Donoghue v Stevenson [1932] AC 562 and has been developed through Australian case law including the High Court decision in Sullivan v Moody (2001) 207 CLR 562.",
    
    "The process of filing a civil claim in the Federal Court of Australia involves several steps: 1) Preparation of originating application and statement of claim, 2) Filing with the Court registry, 3) Service on the defendant, 4) Case management conferences, 5) Discovery and evidence exchange, 6) Trial or settlement. The Federal Court Rules 2011 govern this process.",
    
    "Common law in Australia refers to judge-made law developed through court decisions and precedents, while statutory law is created by Parliament through legislation. Common law principles can be modified or overridden by statute, but statutes are interpreted in light of common law principles. The High Court of Australia is the ultimate authority on both common law and constitutional matters.",
    
    "The doctrine of precedent (stare decisis) in Australian law means that courts are bound by decisions of higher courts in the same hierarchy. The High Court is not bound by its own previous decisions, but generally follows them unless there are compelling reasons to depart. Lower courts must follow decisions of higher courts.",
    
    "In Australian contract law, the essential elements of a valid contract are: 1) Offer and acceptance, 2) Intention to create legal relations, 3) Consideration, 4) Capacity to contract, 5) Genuine consent, and 6) Legality of purpose. These principles are derived from both common law and statutory provisions such as the Australian Consumer Law."
]

@app.get("/")
async def root():
    return {"message": "AusLex AI API - Australian Legal Assistant"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AusLex AI API"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Simulate processing time
        processing_time = random.uniform(1.0, 3.0)
        time.sleep(processing_time)
        
        # Generate a response based on the input
        if "negligence" in request.message.lower():
            response = SAMPLE_RESPONSES[0]
        elif "filing" in request.message.lower() or "civil claim" in request.message.lower():
            response = SAMPLE_RESPONSES[1]
        elif "common law" in request.message.lower() or "statutory" in request.message.lower():
            response = SAMPLE_RESPONSES[2]
        elif "precedent" in request.message.lower():
            response = SAMPLE_RESPONSES[3]
        elif "contract" in request.message.lower():
            response = SAMPLE_RESPONSES[4]
        else:
            # Generic legal response
            response = f"I understand you're asking about Australian law. Based on your question: '{request.message}', I would need to provide specific legal guidance. However, please note that this is for educational purposes only and should not be considered as legal advice. For actual legal matters, please consult with a qualified legal professional."
        
        # Calculate approximate tokens used
        tokens_used = len(response.split()) + len(request.message.split())
        
        return ChatResponse(
            response=response,
            tokens_used=tokens_used,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 