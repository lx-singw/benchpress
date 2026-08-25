# Local Development, Offline Mocking & Turborepo Workflow

> **Document ID:** `BP-IMP-004`  
> **Status:** Approved / Production Standard  
> **Target Track:** Best Architectural Design & The Taskmaster • Google Cloud Hackathon (2026)

---

## 1. Local Monorepo Quickstart

Developers can spin up the full 2-service development environment locally in under 60 seconds with zero cloud dependencies:

```bash
# 1. Clone repository and install monorepo dependencies
git clone https://github.com/lx-singw/benchpress.git
cd benchpress
pnpm install

# 2. Start local GCP emulators (Firestore, Redis) via Docker Compose
docker compose -f docker-compose.dev.yml up -d

# 3. Launch Turborepo full-stack local server (Next.js 15 + Python Worker)
pnpm dev
```

---

## 2. Docker Compose Local Emulators: `docker-compose.dev.yml`

```yaml
version: "3.8"

services:
  firestore-emulator:
    image: google/cloud-sdk:emulators
    container_name: benchpress-firestore-emulator
    command: gcloud beta emulators firestore start --host-port=0.0.0.0:8085
    ports:
      - "8085:8085"

  redis-emulator:
    image: redis:7.2-alpine
    container_name: benchpress-redis-emulator
    ports:
      - "6379:6379"

  vertex-ai-mock:
    image: python:3.12-slim
    container_name: benchpress-vertex-mock
    volumes:
      - ./tests/mocks/vertex_mock_server.py:/app/mock_server.py
    command: python /app/mock_server.py
    ports:
      - "8000:8000"
```

---

## 3. Offline Vertex AI Gemini Stubs

To enable offline testing without consuming API credits, Benchpress includes an **in-memory Vertex AI mock server** that returns realistic multi-turn tool calling and code diff outputs:

```python
# File: tests/mocks/vertex_mock_server.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MockVertexAIHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        req_body = json.loads(self.rfile.read(content_length))

        # Simulated response for Gemini 2.5 Pro / 3.5 Flash
        response_payload = {
            "candidates": [{
                "content": {
                    "role": "model",
                    "parts": [{
                        "functionCall": {
                            "name": "edit_file",
                            "args": {
                                "path": "django/core/validators.py",
                                "instruction": "Fix regex null byte validation",
                                "target_content": "r'^[a-zA-Z0-9_]+$'",
                                "replacement_content": "r'^[a-zA-Z0-9_\x00]+$'"
                            }
                        }
                    }]
                }
            }]
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_payload).encode())

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 8000), MockVertexAIHandler)
    print("Mock Vertex AI Server listening on port 8000...")
    server.serve_forever()
```
