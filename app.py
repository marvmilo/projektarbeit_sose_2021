import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_auth
import plotly.express as px
import pandas as pd
import os
import json
import time

#import scripts
import api
import tools
import measurements
import details
import control

#load vals
title = "Projektarbeit Sose 2021"
external_stylesheets = [dbc.themes.BOOTSTRAP]
meta_tags = [{"name": "viewport", "content": "width=device-width, initial-scale=1"}]

#init app
app = dash.Dash( 
    external_stylesheets=external_stylesheets,
    meta_tags=meta_tags,
    suppress_callback_exceptions=True
)
app.title = title
server = app.server

#init http basic auth
try:
    user_credentials = tools.get_user_credentials()
    auth = dash_auth.BasicAuth(app, user_credentials)
except:
    auth = None

#basic layout of dash app with navbar
app.layout = html.Div(
    children = [
        #Navbar
        dbc.Navbar(
            children = [
                #navbar title
                dbc.Row(
                    children = [
                        dbc.Col(
                            " ".join(word.upper()),
                            style = {
                                "font-size": "20px",
                                "color": "white",
                                "white-space": "nowrap"
                            },
                            width = "auto"
                        )
                        for word in title.split(" ")
                    ],
                    style = {
                        "width": "300px",
                        "max-width": "85%",
                        "padding": "20px 40px"
                    }
                ),
        
                #navbar toggler
                dbc.NavbarToggler(id = "nav-toggler"),
                
                #navbar interactions
                dbc.Collapse(
                    dbc.Row(
                        children = [
                            #Measurements button
                            dbc.Col(
                                dbc.Button(
                                    "Measurements",
                                    id = "measurements-navbutton",
                                    color = "primary"
                                ),
                                width = "auto"
                            ),
                            tools.navbutton_spacing,
                            #Details button
                            dbc.Col(
                                dbc.Button(
                                    "Details",
                                    id = "details-navbutton",
                                    color = "primary"
                                ),
                                width = "auto"
                            ),
                            tools.navbutton_spacing,
                            #Control button
                            dbc.Col(
                                dbc.Button(
                                    "Control",
                                    id = "control-navbutton",
                                    color = "primary"
                                ),
                                width = "auto"
                            )
                        ],
                        justify = "end",
                        no_gutters = True,
                        style = {"width": "100%"}
                    ),
                    navbar = True,
                    id = "nav-collapse"
                )
            ],
            color = "primary",
            dark = True,
            sticky = "top"
        ),
        
        #content Div
        html.Div(
            tools.content_div(),
            id = "update-content-div"
        ),
        
        #not authorized modal
        dbc.Modal(
            children = [
                tools.modal_header("Not Authorized!"),
                dbc.ModalBody(
                    children = [
                        dbc.Row(
                            children = [
                                dbc.Col(
                                    html.B(
                                        ":(",
                                        style = {
                                            "font-size": 75,
                                            "color": tools.accent_color
                                        }
                                    ),
                                    width = "auto"
                                ),
                                dbc.Col(
                                    html.Div(
                                        children = [
                                            html.Br(),
                                            "Sorry!",
                                            html.Br(),
                                            "You are unauthorized",
                                            html.Br(),
                                            "to do this!"
                                        ]
                                    ),
                                    width = "auto"
                                )
                            ],
                            justify = "center"
                        ),
                        html.Br(),
                        html.Div(
                            dbc.Button(
                                "CLOSE",
                                color = "primary",
                                id = "close-not-authorized"
                            ),
                            style = tools.flex_style
                        )
                    ]
                )
            ],
            centered = True,
            keyboard = True,
            id = "not-authorized-modal",
        ),
        
        #url location
        dcc.Location(
            id = "url",
            refresh = False
        ),
        
        #replacement inputs if some are not aviable
        html.Div(
            children = [
                dbc.Button(id = "rename-button"),
                dbc.Button(id = "delete-button"),
                dbc.Button(id = "delete-yes"),
                dbc.Button(id = "delete-no"),
                dbc.Button(id = "delete-close"),
                dbc.Button(id = "close-results-button"),
                dbc.Button(id = "start-measurement-button"),
                dbc.Button(id = "change-settings-button"),
                dbc.Button(id = "retry-measurement-button"),
                dbc.Button(id = "close-settings-changed-button"),
                dbc.Button(id = "calibrate-button"),
                dbc.Input(id = "measurement-name-input"),
                dbc.Modal(id = "delete-modal"),
                dbc.Modal(id = "heartbeat-esp-modal"),
                dbc.Modal(id = "esp-reachable-modal"),
                dbc.Modal(id = "settings-changed-modal"),
                dbc.Modal(id = "calibrate-modal"),
                html.Div(id = "delete-modal-content"),
                html.Div(id = "details-name"),
                dcc.Interval(id = "heartbeat-esp-interval", max_intervals = 0),
                dcc.Interval(id = "calibrate-interval", max_intervals = 0),
                dbc.Input(id = "interval"),
                dbc.Input(id = "tolerance_lat_acc"),
                dbc.Input(id = "stable_amount"),
                dbc.Input(id = "data_package_size"),
                dbc.Input(id = "standby_refresh")
            ],
            style = {"display": "none"}
        )
    ]
)

#navbar collapse callback
@app.callback(
    [Output("nav-collapse", "is_open")],
    [Input("nav-toggler", "n_clicks")],
    [State("nav-collapse", "is_open")]
)
def toggle_navbar_collapse(n_clicks, is_open):
    if n_clicks:
        return [not is_open]
    return [is_open]

#navbar interaction callback
@app.callback(
    [Output("url", "pathname"),
     Output("measurements-navbutton", "n_clicks"),
     Output("details-navbutton", "n_clicks"),
     Output("control-navbutton", "n_clicks"),
     Output("close-results-button", "n_clicks"),
     Output("retry-measurement-button", "n_clicks"),
     Output("update-content-div", "children")],
    [Input("url", "pathname"),
     Input("measurements-navbutton", "n_clicks"),
     Input("details-navbutton", "n_clicks"),
     Input("control-navbutton", "n_clicks"),
     Input("heartbeat-esp-interval", "n_intervals"),
     Input("close-results-button", "n_clicks"),
     Input("retry-measurement-button", "n_clicks")],
    [State("measurement-name-input", "value"),
     State("heartbeat-esp-modal", "is_open"),
     State("esp-reachable-modal", "is_open")]
)
def navbar_callback(url, n_measurements, n_details, n_control, n_heartbeat_checks, n_close_results, n_retry_measurement, measurement_name, checking_esp, not_reachable):
    #creating return list for all Output values
    def return_list(url = "/"):
        return [url, 0, 0, 0, 0, 0, tools.content_div()]
    
    #for getting details id
    def details_url():
        user = tools.get_user()
        id = tools.get_user_data(user)["details_id"]
        
        #proof if user ever visited details
        if not isinstance(id, int):
            id = max([m.split("_")[1] for m in api.get_measurements()])
        
        #update user details id
        tools.update_user_details(user, id)
        return f"/details/{id}"
    
    #get user data
    try:
        user = tools.get_user()
        user_data = tools.get_user_data(user)
        if not user_data:
            raise Exception
    except:
        return return_list(url = "/api_not_reachable")
    
    #set url to last kown if not defined
    if url == "/":
        return return_list(url = user_data["url"])
    if url == "/details":
        return return_list(url = details_url())
    
    #set url if navbutton is pressed
    if n_measurements:
        url = "/measurements"
    elif n_details:
        url = details_url()
    elif n_control:
        url = "/control"
    
    #if heartbeat of esp start measurement
    if checking_esp or not_reachable:
        if api.heartbeat_esp():
            api.reset_error()
            api.start_measurement(measurement_name)
            pass
        else:
            raise PreventUpdate
    
    #return url
    return return_list(url = url)

#callback for site content
@app.callback(
    [Output("content", "children"),
     Output("measurements-navbutton", "active"),
     Output("details-navbutton", "active"),
     Output("control-navbutton", "active")],
    [Input("url", "pathname")]
)
def update_content(url):
    #creating return list for all Output values
    def return_list(
        content = tools.not_found_page(),
        measurements_nav = False,
        details_nav = False,
        control_nav = False
    ):
        return [content, measurements_nav, details_nav, control_nav]
    
    #return API Error is not reachable
    if not api.heartbeat_api() or url == "/api_not_reachable":
        return return_list(content = tools.error_page("API not reachable!"))
    
    #restart server if no authorisation initialized
    if not auth:
        tools.restart_server()
        return return_list(content = tools.error_page("HTTP Authorization not initialized!"))
    
    #update url in user data#
    if not url == "/":
        tools.update_user_url(tools.get_user(), url)
    
    #return measurements content
    if url == "/measurements":
        return return_list(content = measurements.content(), measurements_nav = True)
    
    #return details content
    elif url.startswith("/details"):
        id = url.split("/")[2]
        tools.update_user_details(tools.get_user(), id)
        return return_list(content = details.content(id), details_nav = True)
    
    #return control content
    elif url == "/control":
        return return_list(content = control.content(), control_nav = True)
    
    #else page was not found
    else:
       return return_list()

#not authorized modal
@app.callback(
    [Output("not-authorized-modal", "is_open")],
    [Input("close-not-authorized", "n_clicks"),
     Input("rename-button", "n_clicks"),
     Input("delete-button", "n_clicks"),
     Input("start-measurement-button", "n_clicks"),
     Input("change-settings-button", "n_clicks"),
     Input("calibrate-button", "n_clicks")],
    [State("not-authorized-modal", "is_open")]
)
def open_modal(n_close, n_rename, n_delete, n_start, n_settings, n_calibrate, is_open):
    if is_open:
        return [False]
    
    try:
        if tools.get_user_data(tools.get_user())["role"] == "viewer":
            for i in [n_rename, n_delete, n_start, n_settings, n_calibrate]:
                if i:
                    return [True]
    except TypeError:
        raise PreventUpdate
    raise PreventUpdate

#renaming modal
@app.callback(
    [Output("rename-modal", "is_open"),
     Output("old-name", "children"),
     Output("new-name", "children"),
     Output("rename-input", "valid"),
     Output("rename-input", "invalid")],
    [Input("rename-button", "n_clicks")],
    [State("rename-input", "value"),
     State("details-name", "children"),
     State("url", "pathname")]
)
def rename_measurement(n_clicks, new_name, old_name, url):
    id = int(url.split("/")[2])
    if n_clicks and tools.get_user_data(tools.get_user())["role"] == "admin":
        if new_name:
            api.execute_sql(f"UPDATE measurements SET name = '{new_name}' WHERE id = {id}")
            return [True, old_name, new_name, True, False]
        else:
            return [False, "", "", False, True]
    raise PreventUpdate

#open/close delete are you sure modal
@app.callback(
    [Output("delete-modal-?", "is_open")],
    [Input("delete-button", "n_clicks"),
     Input("delete-no", "n_clicks"),
     Input("delete-yes", "n_clicks")],
    [State("delete-modal-?", "is_open")]
)
def open_delete_are_you_sure(n_open, n_close, n_yes, is_open):
    if tools.get_user_data(tools.get_user())["role"] == "admin":
        if n_open or n_close or n_yes:
            return [not is_open]
    raise PreventUpdate

#confirming deleted measurement
@app.callback(
    [Output("delete-modal-confirm", "is_open")],
    [Input("delete-yes", "n_clicks")],
    [State("delete-modal-confirm", "is_open"),
     State("url", "pathname")]
)
def delete_measurement(n_yes, is_open, url):
    time.sleep(0.5)
    id = int(url.split("/")[2])
    if tools.get_user_data(tools.get_user())["role"] == "admin":
        if n_yes:
            api.execute_sql(f"DELETE FROM measurements WHERE id = {id}")
            api.execute_sql(f"DROP TABLE measurement_{id}")
            return [not is_open]
    raise PreventUpdate

#starting checks if ESP is reachable
@app.callback(
    [Output("heartbeat-esp-modal", "is_open"),
     Output("start-measurement-button", "n_clicks"),
     Output("heartbeat-esp-interval", "n_intervals")],
    [Input("start-measurement-button", "n_clicks"),
     Input("heartbeat-esp-interval", "n_intervals")],
    [State("measurement-name-input", "value")]
)
def check_if_esp_reachable(n_start, n_check, name):
    if not n_check:
        n_check = 0
    
    #events
    if n_start and tools.get_user_data(tools.get_user())["role"] == "admin":
        if name == "" or not name:
            raise PreventUpdate
        else:
            api.set_heartbeat_esp_false()
            return [True, 0, None]
    if n_check:
        if (api.heartbeat_esp() and n_check >= 2) or n_check >= 5:
            return [False, 0, None]
    raise PreventUpdate

@app.callback(
    [Output("measurement-name-input", "invalid")],
    [Input("start-measurement-button", "n_clicks")],
    [State("measurement-name-input", "value")]
)
def check_measurement_name(n_start, name):
    if name == "" or not name:
        return [True]
    else:
        return [False]

#opening modal if ESP is nor reachable
@app.callback(
    [Output("esp-reachable-modal", "is_open"),
     Output("close-esp-reachable", "n_clicks")],
    [Input("heartbeat-esp-interval", "n_intervals"),
     Input("calibrate-interval", "n_intervals"),
     Input("close-esp-reachable", "n_clicks")]
)
def show_esp_not_reachable_modal(n_measurement, n_calibrate, n_close):
    if not n_measurement:
        n_measurement = 0
    if not n_calibrate:
        n_calibrate = 0
    n_measurement += 1
    n_calibrate += 1
    
    if n_measurement >= 5 or n_calibrate >= 5:
        return [True, 0]
    if n_close:
        return [False, 0]
    raise PreventUpdate

#checking measurement
@app.callback(
    [Output("measurement-results-modal", "is_open"),
     Output("retry-measurement-modal", "is_open"),
     Output("view-results-href", "href"),
     Output("error-type-content", "children"),
     Output("error-details-content", "children")],
    [Input("measuring-interval", "n_intervals")]
)
def check_measurement(n_intervals):
    control = api.get_control()
    error = api.get_error()
    
    if not error["type"] == "none":
        return [False, True, "/", error["type"], error["message"]]
        
    if not control["measurement"]:
        return [True, False, f"/details/{int(control['table_name'].split('_')[1])}", "", ""]
    raise PreventUpdate

#update settings per API
@app.callback(
    [Output("settings-changed-modal", "is_open"),
     Output("interval", "invalid"),
     Output("tolerance_lat_acc", "invalid"),
     Output("stable_amount", "invalid"),
     Output("data_package_size", "invalid"),
     Output("standby_refresh", "invalid"),
     Output("change-settings-button", "n_clicks"),
     Output("close-settings-changed-button", "n_clicks")],
    [Input("change-settings-button", "n_clicks"),
     Input("close-settings-changed-button", "n_clicks")],
    [State("interval", "value"),
     State("tolerance_lat_acc", "value"),
     State("stable_amount", "value"),
     State("data_package_size", "value"),
     State("standby_refresh", "value")]
)
def update_settings(n_change, n_close,  interval, tolerance_lat_acc, stable_amount, data_package_size, standby_refresh):
    #return function
    def return_list(
        modal_is_open = False,
        interval = False,
        tolerance_lat_acc = False,
        stable_amount = False,
        data_package_size = False,
        standby_refresh = False
    ):
        return [modal_is_open, interval, tolerance_lat_acc, stable_amount, data_package_size, standby_refresh, 0, 0]
    
    invalids = []
    for val in [interval, tolerance_lat_acc, stable_amount, data_package_size, standby_refresh]:
        try:
            float(val)
            invalids.append(False)
        except:
            invalids.append(True)
    
    if n_close:
        return return_list(modal_is_open = False)
    
    try:
        if tools.get_user_data(tools.get_user())["role"] == "admin":
            if any(invalids):
                return return_list(False, *invalids)    
            
            if n_change and not any(invalids):
                control_json = api.get_control()
                control_json["interval"] = interval
                control_json["tolerance_lat_acc"] = tolerance_lat_acc
                control_json["stable_amount"] = stable_amount
                control_json["data_package_size"] = data_package_size
                control_json["standby_refresh"] = standby_refresh
                api.update_control(control_json)
                return return_list(modal_is_open = True)
    except TypeError:
        raise PreventUpdate
            
    raise PreventUpdate

#open/close calibrating modal
@app.callback(
    [Output("calibrate-modal", "is_open"),
     Output("calibrate-button", "n_clicks"),
     Output("calibrate-interval", "n_intervals")],
    [Input("calibrate-button", "n_clicks"),
     Input("calibrate-interval", "n_intervals")]
)
def check_measurement_name(n_calibrate, n_check):
    if not n_check:
        n_check = 0
    
    #events
    if n_calibrate and tools.get_user_data(tools.get_user())["role"] == "admin":
        api.set_heartbeat_esp_false()
        return [True, 0, None]
    if n_check:
        if (api.heartbeat_esp() and n_check >= 2) or n_check >= 5:
            return [False, 0, None]
    raise PreventUpdate

@app.callback(
    [Output("calibration-done-modal", "is_open"),
     Output("calibration-ok-button", "n_clicks")],
    [Input("calibration-ok-button", "n_clicks"),
     Input("calibrate-interval", "n_intervals")]
)
def check_measurement_name(n_ok, n_interval):
    if not n_interval:
        n_interval = 0
    n_interval += 1
    
    if n_ok:
        return [False, 0]
    if n_interval >= 2 and api.heartbeat_esp():
        api.start_calibration()
        return [True, 0]
    raise PreventUpdate

#calibration callback
if __name__ == '__main__':
    app.run_server(debug=True, host = "0.0.0.0")