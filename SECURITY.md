# Security

Security guidance for running this project safely.

- Do not commit AWS credentials or other secrets to the repository.
- Use environment-specific configuration stores (AWS Secrets Manager, GitHub Secrets).
- Use least-privilege IAM roles for Bedrock and DynamoDB access in production.
- Rotate API keys and credentials regularly.
- Review third-party dependencies for vulnerabilities (dependabot / npm audit / pip-audit).
