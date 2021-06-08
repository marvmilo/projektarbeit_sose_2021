from fastapi import FastAPI, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel
import traceback
import uvicorn
import json
#import sqlite3
import psycopg2
import base64
import os

#files
control_file = "./control.json"
error_file = "./error.json"

#global vals
ESP_online = False
control_data = json.loads(open(control_file).read())

#sqlite database values
try:
    db_url = os.environ["DATABASE_URL"]
except KeyError:
    db_url = "postgres://sjoacfsfjabdso:fe07a1f2881e242d0e1d92c80b9fd6b92acf96ad4abe42efc2cef2d498ce11e9@ec2-54-228-139-34.eu-west-1.compute.amazonaws.com:5432/d8ti1roti36c1h"
db_connection = psycopg2.connect(db_url)
db_cursor = db_connection.cursor()

#init API app
app = FastAPI(
    title = "Projektarbeit SoSe 2021 API", 
    description = "API for communicating between database and GUI/ESP32",
)
security = HTTPBasic()

#format for control json
class Control(BaseModel):
    measurement: bool
    name: str
    table_name: str
    data_package_size: int
    standby_refresh: float
    interval: float
    stable_amount: int
    tolerance_lat_acc: float
    
    class Config:
        schema_extra = {
            "example": control_data
        }

#format for posting an error message
class Error(BaseModel):
    type: str
    message: str
    
#fuction for executing any SQL command
def execute_sql(command):
    try:
        db_cursor.execute(command)
    except:
        execute_sql("ROLLBACK")
        db_cursor.execute(command)   
    db_connection.commit()
    try:
        return db_cursor.fetchall()
    except:
        return None

#function for getting control file
def get_control():
    with open(control_file, "r") as rd:
        return json.loads(rd.read())

#function for executing other function only if the right credentials are given by API user
def safe(credentials, function, args = [], direct = False):
    #check for credentials
    if credentials.username == "user" and credentials.password == "projekt123":
        #return cases
        try:
            if not direct:
                return {
                    "success": True,
                    "details": function(*args)
                }
            else:
                return function(*args)
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
@app.post("/sql")
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

#PUT for updating control json
@app.put("/control")
def update_control_data(control: Control, credentials: HTTPBasicCredentials = Depends(security)):
    def callback(control):
        with open(control_file, "w") as wd:
            wd.write(control.json())
        return control.dict()
    return safe(credentials = credentials, function = callback, args = [control])

#GET for downloading control json
@app.get("/control")
def get_control_data(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        return get_control()
    return safe(credentials = credentials, function = callback)

#GET for downloading control json and updating heartbeat of esp
@app.get("/control/esp")
def get_control_data_ESP(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        global ESP_online
        ESP_online = True
        return get_control()
    return safe(credentials = credentials, function = callback)

#POST function for starting measurement with saved control json
@app.post("/measurement_start")
def start_measurement(name: str, credentials: HTTPBasicCredentials = Depends(security)):
    def callback(name):
        #create table name
        readout = execute_sql("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'")
        measurements = [m[0] for m in readout if m[0].startswith("measurement_")]
        indices = [int(m.split("_")[1]) for m in measurements]
        try:
            table_name = f"measurement_{max(indices)+1}"
        except ValueError:
            table_name = "measurement_0"
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

#GET for downloading control json
@app.get("/error")
def get_error_json(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        with open(error_file, "r") as rd:
            return json.loads(rd.read())
    return safe(credentials = credentials, function = callback)

#PUT function for returing error form ESP
@app.put("/error")
def upload_error_json(error: Error, credentials: HTTPBasicCredentials = Depends(security)):
    def callback(error):
        with open(error_file, "w") as wd:
            wd.write(error.json())
        return error.dict()
    return safe(credentials = credentials, function = callback, args = [error])

#GET for checking heartbeat of API
@app.get("/heartbeat/api")
def heartbeat_api(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        return {"heartbeat": True}
    return safe(credentials = credentials, function = callback, direct = True)

#GET for checking heartbeat of ESP
@app.get("/heartbeat/esp")
def heartbeat_esp(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        return {"heartbeat": ESP_online}
    return safe(credentials = credentials, function = callback, direct = True)

#PUT for setting heartbeat of ESP to False
@app.put("/heartbeat/esp/false")
def set_heartbeat_esp_to_false(credentials: HTTPBasicCredentials = Depends(security)):
    def callback():
        global ESP_online
        ESP_online = False
        return {"heartbeat": ESP_online}
    return safe(credentials = credentials, function = callback)

#for debugging
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)