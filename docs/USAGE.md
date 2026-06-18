# Usage Guide

This guide covers the main workflows: generate an RFP, analyze it, generate a proposal, and use the chat.

CLI examples

- Create an RFP from a sample file

```bash
./rfp-agent create --title "New RFP" --file samples/rfp.txt
```

- Analyze an RFP

```bash
./rfp-agent analyze --rfp-id <uuid>
```

- Generate a proposal

```bash
./rfp-agent propose --rfp-id <uuid> --company "ACME Corp" --profile-file samples/company_profile.txt
```

Web UI
- Open http://localhost:3000
- Use the Generate page to create a new RFP and download the .docx
- Open an RFP to view Analysis, Proposal, and Chat

Output
- Generated Word documents are saved to `output/rfps/` by default.
