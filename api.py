import json
import requests

#api values
api_url = "https://api-projektarbeit-sose-2021.herokuapp.com"
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
    resp = communicate(requests.post, "/sqlite3", data)
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
    #get info about measurement
    info_keys = [k[1] for k in execute_sql("PRAGMA table_info(\"measurements\")")]
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
    
    #get data of measurement
    data = execute_sql(f"SELECT * FROM measurement_{id}")
    #return vals
    return {
        "info": info,
        "data": data
    }
        
#for getting table names
def get_measurements():
    control_data = communicate(requests.get, "/control")["details"]
    measurements = [m[0] for m in execute_sql("SELECT name FROM sqlite_master WHERE type='table'") if m[0].startswith("measurement_")]
    callback = [m for m in measurements if not (m == control_data["table_name"] and control_data["measurement"])]
    return callback

#for checking if API is reachable
def heartbeat():
    try:
        resp = communicate(requests.get, "/heartbeat")
        return True
    except:
        return False
    