/**
 * Mock Service Worker (MSW) Handlers
 * 
 * Provides realistic API responses for testing legal AI functionality.
 * Uses authentic legal content for accuracy testing.
 */

import { rest } from 'msw';

// Mock legal responses with real Australian legal citations
const MOCK_LEGAL_RESPONSES = {
  'migration act 359a': {
    response: `Section 359A of the Migration Act 1958 (Cth) requires the Refugee Review Tribunal to provide an applicant with particulars of any information that:

1. Would be the reason, or a part of the reason, for affirming the decision under review; and
2. Is specifically about the applicant or another person and is not just about a class of persons of which the applicant or other person is a member; and  
3. Was not given by the applicant for the purpose of the application for review.

The Tribunal must also ensure that the applicant understands why the information is relevant to the review and invite the applicant to comment on it. This requirement is fundamental to procedural fairness in migration decisions.

Key cases that have interpreted section 359A include SZBEL v Minister for Immigration and Multicultural and Indigenous Affairs [2006] HCA 63 and SZLTC v Minister for Immigration and Citizenship [2017] FCAFC 94.`,
    citations: [
      {
        type: 'legislation',
        citation: 'Migration Act 1958 (Cth) s 359A',
        url: 'https://www.austlii.edu.au/au/legis/cth/consol_act/ma1958118/s359a.html'
      },
      {
        type: 'case',
        citation: 'SZBEL v Minister for Immigration and Multicultural and Indigenous Affairs [2006] HCA 63',
        url: 'https://www.austlii.edu.au/au/cases/cth/HCA/2006/63.html'
      }
    ]
  },
  
  'privacy act': {
    response: `The Privacy Act 1988 (Cth) is the principal piece of Australian legislation protecting the privacy of individuals. The Act includes 13 Australian Privacy Principles (APPs) that govern how personal information is collected, used, disclosed and stored.

Key provisions include:
- Section 6 defines "personal information" broadly
- Section 13 outlines the Australian Privacy Principles
- Part IIIC establishes the notifiable data breaches scheme

The Privacy Act applies to agencies and organisations with an annual turnover of more than $3 million, as well as all health service providers and some small businesses.`,
    citations: [
      {
        type: 'legislation',
        citation: 'Privacy Act 1988 (Cth)',
        url: 'https://www.austlii.edu.au/au/legis/cth/consol_act/pa1988108/'
      }
    ]
  },

  'procedural fairness': {
    response: `Procedural fairness, also known as natural justice, is a fundamental principle of Australian administrative law. It requires that:

1. **The hearing rule (audi alteram partem)**: A person affected by a decision must be given a fair opportunity to present their case
2. **The bias rule (nemo judex in sua causa)**: The decision-maker must be unbiased and act fairly

In the context of migration law, procedural fairness obligations are codified in Division 4 of Part 7 of the Migration Act 1958 (Cth), particularly sections 359A, 360, and 424A.

The High Court in Kioa v West (1985) 159 CLR 550 established that procedural fairness is implied in administrative decision-making unless expressly excluded by statute.`,
    citations: [
      {
        type: 'case',
        citation: 'Kioa v West (1985) 159 CLR 550',
        url: 'https://www.austlii.edu.au/au/cases/cth/HCA/1985/81.html'
      },
      {
        type: 'legislation',
        citation: 'Migration Act 1958 (Cth) ss 359A, 360, 424A',
        url: 'https://www.austlii.edu.au/au/legis/cth/consol_act/ma1958118/'
      }
    ]
  }
};

export const handlers = [
  // Authentication endpoints
  rest.post('http://localhost:8000/auth/register', (req, res, ctx) => {
    const { email, password, name } = req.body;
    
    // Simulate email already exists
    if (email === 'existing@test.com') {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'Email already registered' })
      );
    }
    
    // Simulate validation errors
    if (!email || !password || !name) {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'All fields are required' })
      );
    }
    
    if (password.length < 6) {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'Password must be at least 6 characters' })
      );
    }
    
    // Successful registration
    return res(
      ctx.status(201),
      ctx.json({
        access_token: 'mock-jwt-token-' + Date.now(),
        user: {
          id: 'user-' + Date.now(),
          email,
          name,
          created_at: new Date().toISOString()
        }
      })
    );
  }),

  rest.post('http://localhost:8000/auth/login', (req, res, ctx) => {
    const { email, password } = req.body;
    
    // Simulate invalid credentials
    if (email === 'wrong@test.com' || password === 'wrongpassword') {
      return res(
        ctx.status(401),
        ctx.json({ detail: 'Invalid email or password' })
      );
    }
    
    // Simulate server error
    if (email === 'error@test.com') {
      return res(
        ctx.status(500),
        ctx.json({ detail: 'Internal server error' })
      );
    }
    
    // Successful login
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock-jwt-token-' + Date.now(),
        user: {
          id: 'user-123',
          email,
          name: 'Test User',
          created_at: '2023-01-01T00:00:00Z'
        }
      })
    );
  }),

  // Chat endpoint with legal AI responses
  rest.post('http://localhost:8000/chat', async (req, res, ctx) => {
    const { message, max_tokens, temperature } = await req.json();
    
    // Simulate various response scenarios
    
    // Simulate server error
    if (message.includes('server error')) {
      return res(
        ctx.status(500),
        ctx.json({ detail: 'Internal server error' })
      );
    }
    
    // Simulate timeout (for timeout testing)
    if (message.includes('timeout test')) {
      return res(
        ctx.delay(35000),
        ctx.json({ response: 'This response took too long' })
      );
    }
    
    // Find matching legal response
    const queryLower = message.toLowerCase();
    let matchedResponse = null;
    
    for (const [key, response] of Object.entries(MOCK_LEGAL_RESPONSES)) {
      if (queryLower.includes(key)) {
        matchedResponse = response;
        break;
      }
    }
    
    // Default response if no specific match
    if (!matchedResponse) {
      matchedResponse = {
        response: `I understand you're asking about "${message}". This appears to be a legal question that would benefit from specific research into Australian law. 

For the most accurate and up-to-date information, I recommend consulting:
1. The Australian Legal Information Institute (AustLII) database
2. Current legislation on the Federal Register of Legislation
3. A qualified legal practitioner familiar with this area of law

Please note that this AI assistant provides general information only and should not be considered legal advice.`,
        citations: []
      };
    }
    
    // Simulate processing delay
    return res(
      ctx.delay(1000 + Math.random() * 2000), // 1-3 second delay
      ctx.json({
        response: matchedResponse.response,
        citations: matchedResponse.citations || [],
        processing_time: Math.round(1000 + Math.random() * 2000),
        model: 'auslex-20b',
        parameters: {
          max_tokens,
          temperature
        }
      })
    );
  }),

  // Embeddings endpoint
  rest.post('http://localhost:8000/embeddings', (req, res, ctx) => {
    return res(
      ctx.json({
        embeddings: Array.from({ length: 1536 }, () => Math.random() - 0.5),
        model: 'text-embedding-ada-002'
      })
    );
  }),

  // RAG endpoint for legal research
  rest.post('http://localhost:8000/rag_answer', async (req, res, ctx) => {
    const { query } = await req.json();
    
    return res(
      ctx.json({
        answer: `Based on my analysis of Australian legal sources, regarding "${query}":

This query relates to established Australian legal principles. The relevant authorities include both statute law and case law that provide guidance on this matter.

For comprehensive analysis, I recommend reviewing the primary sources and considering recent developments in this area of law.`,
        cited_passages: [
          {
            content: "Relevant legal principle from Australian jurisprudence...",
            source: "Migration Act 1958 (Cth) s 359A",
            url: "https://www.austlii.edu.au/au/legis/cth/consol_act/ma1958118/s359a.html",
            relevance_score: 0.89
          }
        ],
        processing_time: 2340
      })
    );
  }),

  // Legal provision lookup
  rest.get('http://localhost:8000/legal-provision/:actName/:section', (req, res, ctx) => {
    const { actName, section } = req.params;
    
    return res(
      ctx.json({
        act_name: actName,
        section: section,
        title: `Section ${section} of the ${actName}`,
        content: `This is the content of section ${section} from the ${actName}. The provision establishes important legal requirements and obligations.`,
        url: `https://www.austlii.edu.au/au/legis/cth/consol_act/${actName.toLowerCase().replace(/\s+/g, '')}/${section}.html`,
        last_updated: "2023-12-01"
      })
    );
  }),

  // Health check endpoint
  rest.get('http://localhost:8000/health', (req, res, ctx) => {
    return res(
      ctx.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      })
    );
  }),

  // Catch-all for unhandled requests
  rest.get('*', (req, res, ctx) => {
    console.warn(`Unhandled GET request to ${req.url.toString()}`);
    return res(
      ctx.status(404),
      ctx.json({ error: 'Endpoint not found' })
    );
  }),

  rest.post('*', (req, res, ctx) => {
    console.warn(`Unhandled POST request to ${req.url.toString()}`);
    return res(
      ctx.status(404),
      ctx.json({ error: 'Endpoint not found' })
    );
  })
];

// Export specific handlers for individual test customization
export const authHandlers = handlers.filter(handler => 
  handler.info?.path?.includes('auth')
);

export const chatHandlers = handlers.filter(handler => 
  handler.info?.path?.includes('chat') || handler.info?.path?.includes('rag')
);

export const errorHandlers = [
  rest.post('http://localhost:8000/chat', (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({ detail: 'Simulated server error' })
    );
  }),

  rest.post('http://localhost:8000/auth/login', (req, res, ctx) => {
    return res(
      ctx.status(401),
      ctx.json({ detail: 'Invalid credentials' })
    );
  })
];

export default handlers;