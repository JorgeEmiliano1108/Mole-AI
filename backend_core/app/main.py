from fastapi import FastAPI

app = FastAPI()

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.get('/')
async def root():
    return {'message': 'backend_core stub running'}
