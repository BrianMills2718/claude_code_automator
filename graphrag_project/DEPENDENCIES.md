# Project Dependencies

This project requires the following external dependencies:

## API Keys (Required)
- `ANTHROPIC_API_KEY`: API key for Anthropic Claude models

## External Services
- **Chroma**: ChromaDB vector database
- **Postgres**: PostgreSQL database

## Quick Setup

1. Set environment variables:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

2. Start services:
```bash
docker-compose up -d
```

3. Run setup validation:
```bash
./setup.sh
```

## Manual Validation

Check ANTHROPIC_API_KEY: `test -n "$ANTHROPIC_API_KEY"`
