# Phase 2: Passthrough Router (No ML yet)

1. Implement the async `httpx` clients for Groq and OpenAI.
2. Build a simple passthrough that blindly forwards the incoming payload to Groq and returns the response.
3. Validate that a standard OpenAI SDK client can connect to `http://localhost:8080/v1` and get a response.
