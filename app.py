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

#import scripts
import api
import tools
import measurements
import details

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
user_credentials = tools.get_user_credentials()
auth = dash_auth.BasicAuth(app, user_credentials)

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
                        "max-width": "85%"
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
                            #Details button
                            dbc.Col(
                                dbc.Button(
                                    "Details",
                                    id = "details-navbutton",
                                    color = "primary"
                                ),
                                width = "auto"
                            ),
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
            style = {"padding": "20px 40px"}
        ),
        
        #content Div
        html.Div(
            tools.content_div(),
            id = "update-content-div"
        ),
        
        #url location
        dcc.Location(
            id = "url",
            refresh = False
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
    
    if not api.heartbeat():
        return return_list(url = "/API_error")
    
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
    user = tools.get_user()
    user_data = tools.get_user_data(user)
    
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
    
    #return API is not reachable
    if url == "/API_error":
        return return_list(content = tools.error_page("API not reachable!"))
    
    #update url in user data
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
        return return_list(content = "control content", control_nav = True)
    
    #else page was not found
    else:
       return return_list()

if __name__ == '__main__':
    app.run_server(debug=True, host = "0.0.0.0")