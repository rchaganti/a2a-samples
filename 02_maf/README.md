Microsoft Agent Framework (MAF) Shopping Assistant - Consumes ADK Currency Agent via A2A

This example demonstrates cross-framework A2A communication:
- A Microsoft Agent Framework agent acts as the A2A client
- It connects to the Google ADK Currency Agent running on port 8001
- Combines local shopping tools with remote currency conversion

Prerequisites:
1. Install Microsoft Agent Framework:
   ```bash
   pip install agent-framework --pre httpx a2a
   ```

2. Start the Google ADK Currency Agent (from the repository root):
   ```bash
   uvicorn "01-basics.remote_a2a.currency_agent.agent:a2a_app" --host localhost --port 8001
   ```

3. Run the MAF Shopping Assistant:

    ```bash
    python -m 02_maf.shopping_assistant
    ```