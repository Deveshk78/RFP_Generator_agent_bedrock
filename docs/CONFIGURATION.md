# Configuration

The application reads configuration from environment variables. Create a top-level `.env` for the backend and `web/.env.local` for the frontend.

Example `.env`

```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
BEDROCK_READ_TIMEOUT=600
DYNAMODB_TABLE=RfpAgent
```

Frontend (`web/.env.local`)
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

Security
- Never commit `.env` files. Add them to `.gitignore` (already recommended).
- Use IAM roles/instance profiles in production.

Secrets in CI
- Store AWS credentials in GitHub Secrets when enabling CI/CD.
