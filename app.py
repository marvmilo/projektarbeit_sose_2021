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
        tools.replacments_ids()
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
     Output("update-content-div", "children")],
    [Input("url", "pathname"),
     Input("measurements-navbutton", "n_clicks"),
     Input("details-navbutton", "n_clicks"),
     Input("control-navbutton", "n_clicks")]
)
def navbar_callback(url, n_measurements, n_details, n_control):
    #creating return list for all Output values
    def return_list(url = "/"):
        return [url, 0, 0, 0, tools.content_div()]
    
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
    except:
        return return_list(url = "/api_not_reachable")
    
    #set url to last kown if not defined
    print(user_data["url"])
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
    
    #return url
    return return_list(url = url)
    
    raise PreventUpdate

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
    if not api.heartbeat():
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
     Input("delete-button", "n_clicks")],
    [State("not-authorized-modal", "is_open")]
)
def open_modal(n_close, n_rename, n_delete, is_open):
    if is_open:
        return [False]
    elif tools.get_user_data(tools.get_user())["role"] == "viewer":
        for i in [n_rename, n_delete]:
            if i:
                return [True]
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
    [Input("delete-yes", "n_clicks"),
     Input("delete-close", "n_clicks")],
    [State("delete-modal-confirm", "is_open"),
     State("url", "pathname")]
)
def delete_measurement(n_yes, n_close, is_open, url):
    time.sleep(0.5)
    id = int(url.split("/")[2])
    if tools.get_user_data(tools.get_user())["role"] == "admin":
        if n_yes or n_close:
            print(api.execute_sql(f"DELETE FROM measurements WHERE id = {id}"))
            print(api.execute_sql(f"DROP TABLE measurement_{id}"))
            return [not is_open]
    raise PreventUpdate

if __name__ == '__main__':
    app.run_server(debug=True, host = "0.0.0.0")