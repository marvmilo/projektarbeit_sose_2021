import json
import requests

#api values
api_url = "https://api-projektarbeit-sose-2021.herokuapp.com/"
headers = {
    'accept': 'application/json',
    'Authorization': 'Basic dXNlcjpwcm9qZWt0MTIz',
    'Content-Type': 'application/json',
}

#fuction for executing any SQL command
def execute_sql(*commands):
    data = [*commands]
    return json.loads(
        requests.post(
            f"{api_url}/sqlite3",
            headers = headers,
            data = data
        ).text
    )

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
    
    #get data of measurement
    data = execute_sql(f"SELECT * FROM measurement_{id}")
    #return vals
    return {
        "info": info,
        "data": data
    }
        
#for getting table names
def get_measurements():
    callback = [m[0] for m in execute_sql("SELECT name FROM sqlite_master WHERE type='table'") if m[0].startswith("measurement_")]
    return callback