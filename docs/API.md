# API Reference

This doc lists the main API endpoints exposed by the FastAPI backend (in `api/server.py`).

GET /api/health
- Health check. Returns 200 OK.

GET /api/domains
- Returns a list of supported industry domains and templates.

GET /api/rfps
- List saved RFP metadata.

POST /api/rfps/generate
- Body: { title, domain, prompt, options }
- Generates an RFP using Bedrock and returns metadata and generated docx link.

POST /api/rfps/{id}/analyze
- Runs AI analysis on the RFP content and stores analysis into DynamoDB.

POST /api/rfps/{id}/propose
- Generates a vendor proposal draft given a company profile.

POST /api/rfps/{id}/chat
- Conversational chat for an RFP. Stores chat history.

GET /api/rfps/{id}/download
- Returns the generated .docx file as attachment.

Refer to `api/server.py` for parameter and response shapes.
