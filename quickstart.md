# Quickstart

1. Create & activate venv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```

2. Install deps:

```powershell
pip install -r requirements.txt
```

3. Run dev server:

```powershell
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```


4. Docker Deployment Steps

```powershell
# Build the image
docker build -t fastapi-app .

# Run the container
docker run -p 8000:8000 fastapi-app
```