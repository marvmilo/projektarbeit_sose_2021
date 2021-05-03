import sqlite3

#database values
db_name = "database.db"
connection = sqlite3.connect(db_name, check_same_thread = False)
cursor = connection.cursor()

#fuction for executing any SQL command
def execute_command(command):
    cursor.execute(command)
    connection.commit()
    callback = cursor.fetchall()
    return callback

#for getting content of table
def get_table(table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    callback = cursor.fetchall()
    return callback

#for getting data of a measurement
def get_measurement(id):
    #get info about measurement
    cursor.execute("PRAGMA table_info(\"measurements\")")
    info_keys = [k[1] for k in cursor.fetchall()]
    cursor.execute(f"SELECT * FROM measurements WHERE id = {id}")
    try:
        info_data = cursor.fetchall()[0]
    except IndexError:
        info_data = ["-" for i in range(len(info_keys))]
    #create info dict
    info = {info_keys[i]: info_data[i] for i in range(len(info_keys))}
    
    #get data of measurement
    cursor.execute(f"SELECT * FROM measurement_{id}")
    data = cursor.fetchall()
    #return vals
    return {
        "info": info,
        "data": data
    }
    
#for getting table names
def get_measurements():
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    callback = [m[0] for m in cursor.fetchall() if m[0].startswith("measurement_")]
    return callback