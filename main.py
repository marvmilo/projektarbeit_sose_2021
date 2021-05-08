from fastapi import FastAPI, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel
import traceback
import json
import sqlite3
import base64
import os
import uvicorn

#files
control_file = "./control.json"
error_file = "./error.json"

#global vals
ESP_online = False

#sqlite database values 
db_name = "database.db"
db_connection = sqlite3.connect(db_name, check_same_thread = False)
db_cursor = db_connection.cursor()

#init API app
app = FastAPI(
    title = "Projektarbeit SoSe 2021 API", 
    description = "API for communicating between database and GUI/ESP32",
)
security = HTTPBasic()

#format for posting an error message
class Error(BaseModel):
    type: str
    message: str
    
#fuction for executing any SQL command
def execute_sql(command):
    db_cursor.execute(command)
    db_connection.commit()
    return db_cursor.fetchall()

#function for getting control file
def get_control():
    with open(control_file, "r") as rd:
        return json.loads(rd.read())

#function for executing other function only if the right credentials are given by API user
def safe(credentials, function, args = []):
    #check for credentials
    if credentials.username == "user" and credentials.password == "projekt123":
        #return cases
        try:
            return {
                "success": True,
                "details": function(*args)
            }
        except:
            return {
                "success": False,
                "error": "An error occured while running function!",
                "details": traceback.format_exc()
            }
    else:
        return {
            "success": False,
            "error": "Authetication failed!"
        }

#POST for executing SQL commands in database
@app.post("/sqlite3")
def execute_sql_command(commands: list, credentials: HTTPBasicCredentials = Depends(security)):
    def callback(commands):
        callbacks = dict()
        with open(control_file, "r") as rd:
            callbacks["control"] = json.loads(rd.read())
        for i, command in enumerate(commands):
            try:
                success = True
                details = execute_sql(command)
            except:
                success = False
                details = traceback.format_exc()
            callbacks[f"command_{i}"] = {
                "success": success,
                "details": details
            }
        return callbacks
    return safe(credentials = credentials, function = callback, args = [commands])

#GET for downloading control json
@app.get("/control")
def get_control_data(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        return get_control()
    return safe(credentials = credentials, function = callback)

#GET for downloading control json and updating heartbeat of esp
@app.get("/control/esp")
def get_control_data(credentials: HTTPBasicCredentials = Depends(security)):
    global ESP_online
    ESP_online = True
    def callback():
        return get_control()
    return safe(credentials = credentials, function = callback)

#POST function for starting measurement with saved control json
@app.post("/measurement_start")
def start_measurement(name: str, credentials: HTTPBasicCredentials = Depends(security)):
    def callback(name):
        #create table name
        readout = execute_sql("SELECT name FROM sqlite_master WHERE type='table'")
        measurements = [m[0] for m in readout if m[0].startswith("measurement_")]
        indices = [int(m.split("_")[1]) for m in measurements]
        table_name = f"measurement_{max(indices)+1}"
        #create table in database
        sql_command = "CREATE TABLE {} (val_id INTEGER UNIQUE, timestamp TEXT, accx REAL,accy REAL,accz REAL,stable INTEGER,bridge_circuit_voltage REAL,PRIMARY KEY(val_id));"
        execute_sql(sql_command.format(table_name))
        #edit control.json
        control = json.loads(open(control_file, "r").read())
        control["measurement"] = True
        control["name"] = name
        control["table_name"] = table_name
        open(control_file, "w").write(json.dumps(control, indent = 4))
        return control
    return safe(credentials = credentials, function = callback, args = [name])

#POST funcion for stopping measurement in control.json
@app.post("/measurement_stop")
def stop_measurement(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        control = json.loads(open(control_file, "r").read())
        control["measurement"] = False
        open(control_file, "w").write(json.dumps(control, indent = 4))
        return control
    return safe(credentials = credentials, function = callback)

#PUT function for returing error form ESP
@app.put("/error")
def upload_error(error: Error, credentials: HTTPBasicCredentials = Depends(security)):
    def callback(error):
        with open(error_file, "w") as wd:
            wd.write(error.json())
        return error.dict()
    return safe(credentials = credentials, function = callback, args = [error])

#GET for checking heartbeat of API
@app.get("/heartbeat/api")
def heartbeat_api(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        return {"heartbeat": False}
    return safe(credentials = credentials, function = callback)

#GET for checking heartbeat of ESP
@app.get("/heartbeat/esp")
def heartbeat_esp(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        return {"heartbeat": ESP_online}
    return safe(credentials = credentials, function = callback)

#PUT for setting heartbeat of ESP to False
@app.put("/heartbeat/esp/false")
def set_heartbeat_esp_to_false(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        global ESP_online
        ESP_online = False
        return {"heartbeat": ESP_online}
    return safe(credentials = credentials, function = callback)

#GET database for debugging
@app.get("/database_file")
def download_database_file(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        return FileResponse(path = "./database.db", media_type="application/db",filename="./database.db")
    return safe(credentials = credentials, function = callback)

#for debugging
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)