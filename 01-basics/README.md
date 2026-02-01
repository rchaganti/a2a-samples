To see this in action, you'll need both agents running:

Terminal 1 - Start the ADK Currency Agent:
```shell
uvicorn "01-basics.remote_a2a.currency_agent.agent:a2a_app" --host localhost --port 8001
```

Terminal 2 - Start ADK web:
```shell
adk web 01-basics
```

Try the following prompt:
- What travel destinations can you help me with?
- What is the exchange rate for USD and EUR?