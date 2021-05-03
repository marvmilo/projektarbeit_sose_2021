from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def hello():
    return {"message":"Hello World!"}

@app.get("/hello")
def world():
    return {"message":"world!"}