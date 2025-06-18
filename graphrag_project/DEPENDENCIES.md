# Project Dependencies

This project requires the following external dependencies:

## API Keys (Required)
- `OPENAI_API_KEY`: API key for langchain integration

## External Services
- **Chroma**: Chroma database/service

## Quick Setup

1. Set environment variables:
```bash
export OPENAI_API_KEY="your-key-here"
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

Check OPENAI_API_KEY: `test -n "$OPENAI_API_KEY"`
