import json
import requests
import re

#api values
api_url = "https://api-projektarbeit-sose-2021.herokuapp.com"
#api_url = "http://localhost:8000"
headers = {
    'accept': 'application/json',
    'Authorization': 'Basic dXNlcjpwcm9qZWt0MTIz',
    'Content-Type': 'application/json',
}

#communciationg with api
def communicate(method, sub, data = None):
    return json.loads(
        method(
            f"{api_url}{sub}",
            headers = headers,
            data = data
        ).text
    )

#for executing any SQL command
def execute_sql(*commands):
    data = json.dumps([*commands], indent = 4)
    resp = communicate(requests.post, "/sql", data)
    #print(commands, "\n", resp)
    if len([*commands]) == 1:
        if resp["success"]:
            if resp["details"]["command_0"]["success"]:
                return resp["details"]["command_0"]["details"]
    return resp

#for getting content of table
def get_table(table_name):
    return execute_sql(f"SELECT * FROM {table_name}")

#for getting data of a measurement
def get_measurement(id):
    #get data of measurement
    data = execute_sql(f"SELECT * FROM measurement_{id}")
    try:
        if not data["details"]["command_0"]["success"]:
            return False
    except:
        pass
    
    #sort data
    data = sorted(data, key = lambda e: e[1])
    
    #get info about measurement
    columns = execute_sql("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'measurements'")
    info_keys = [k[0] for k in columns]
    
    try:
        info_data = execute_sql(f"SELECT * FROM measurements WHERE id = {id}")[0]
    except IndexError:
        info_data = ["-" for i in range(len(info_keys))]
    #create info dict
    info = {info_keys[i]: info_data[i] for i in range(len(info_keys))}
    if not info["success"] == "-":
        info["success"] = bool(info["success"])
    else:
        info["success"] = False
    
    #return vals
    return {
        "info": info,
        "data": data
    }

#for getting control json
def get_control():
    return communicate(requests.get, "/control")["details"]

#for updating control json
def update_control(payload):
    communicate(requests.put, "/control", json.dumps(payload))

#for getting control json
def get_error():
    return communicate(requests.get, "/error")["details"]

def reset_error():
    communicate(requests.put, "/error", json.dumps({"type": "none", "message": "none"}))
        
#for getting table names
def get_measurements():
    control_data = get_control()
    measurements = [m[0] for m in execute_sql("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'") if m[0].startswith("measurement_")]
    callback = [m for m in measurements if not (m == control_data["table_name"] and control_data["measurement"])]
    
    #sort callback
    def atoi(text):
        return int(text) if text.isdigit() else text
    def natural_keys(text):
        return [ atoi(c) for c in re.split(r'(\d+)', text)]
    callback.sort(key = natural_keys)
    
    return callback

#for checking if API is reachable
def heartbeat_api():
    try:
        resp = communicate(requests.get, "/heartbeat/api")
        return True
    except Exception as e:
        print(e)
        return False

#for checking if API is reachable
def heartbeat_esp():
    resp = communicate(requests.get, "/heartbeat/esp")
    return resp["heartbeat"]
    
#for setting heartbeat of ESP to false
def set_heartbeat_esp_false():
    try:
        resp = communicate(requests.put, "/heartbeat/esp/false")
        return True
    except:
        return False

#for starting measurement
def start_measurement(name):
    communicate(requests.post, f"/measurement_start?name={name}")

#for starting calibration
def start_calibration():
    communicate(requests.post, f"/calibration_start")
    