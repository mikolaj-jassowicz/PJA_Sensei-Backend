# PJA_Sensei-Backend

## Usage description of AI module
### macOS

#### 1. Create an .env file in the project's root directory

#### 2. Write OpenRouter API key to .env file
```python
OPENROUTER_API_KEY=your_api_key_here
```

#### 2. Navigate to your project directory
```python
cd /path/to/your/project
```

#### 3. Create a virtual environment
```python
python3 -m venv venv
```

#### 4. Activate it
```python
source venv/bin/activate
```

#### 5. Install required dependencies
```python
pip install -r requirements.txt
```

#### 6. Run a Uvicorn ASGI server
```python
uvicorn app.main:app
```

### Windows

#### 1. Write OpenRouter API key to .env file
```python
OPENROUTER_API_KEY=your_api_key_here
```

#### 2. Navigate to your project directory
```python
cd C:\path\to\your\project
```

#### 3. Create a virtual environment
```python
python -m venv venv
```

#### 4. Activate it
###### (PowerShell)
```shell
venv\Scripts\Activate.ps1
```

###### (Command Prompt)
```python
venv\Scripts\activate.bat
```

#### 5. Install required dependencies
```python
pip install -r requirements.txt
```

#### 6. Run a Uvicorn ASGI server
```python
uvicorn app.main:app
```

### Test the endpoints via Swagger UI

1. In a web browser, go to the following address:
<your Uvicorn ASGI server's address>/docs

2. Start a conversation by sending a request with the following body to /conversation endpoint:
{
  "problem": "<problem description>",
  "progress": "<your current progress on solving the problem>"
}

In the response, you will receive a new conversation id.

3. Continue the conversation, using the conversation id, that you received in the previous step, in the conversations/{conversation_id}/messages endpoint. Send there the following request body:

{
  "question": "<question to the model concerning how to solve the problem>",
  "progress": "<your current progress on solving the problem>"
}

You can also check saved conversations by using /conversations/{conversation_id} endpoint. Note: After restarting the server, your conversations will be removed.