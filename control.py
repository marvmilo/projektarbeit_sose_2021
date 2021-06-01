import dash_bootstrap_components as dbc
import dash_html_components as html
import requests

#load scripts
import api
import tools

#control esp content
def control_esp():
    settings = api.get_control()
    
    #function for creating column in row
    def settings_col(name, value):
        return dbc.Col(
            children = [
                html.Div(
                    name,
                    style = {
                        "font-size": 17.5,
                        "white-space": "nowrap"
                    }
                ),
                html.B(
                    value,
                    style = {
                        "font-size": 35,
                        "white-space": "nowrap"
                    }
                ),
                html.Br(),html.Br()
            ],
            width = "auto"
        )
    
    #function for Input fields in modals
    def settings_input(name, value, unit, integer = False):
        if integer:
            step = 1
        else:
            step = 0.01
        
        return dbc.Row(
            children = [
                dbc.Col(
                    html.B(name),
                    width = 4
                ),
                dbc.Col(
                    dbc.Input(
                        type = "number",
                        value = value,
                        min = 0,
                        step = step
                    )
                ),
                dbc.Col(
                    unit,
                    width = 2
                )
            ]
        )

    #return content
    return html.Div(
        children = [
            tools.page_title("Control ESP"),
            html.Br(),html.Br(),
            html.Div(
                dbc.Button(
                    children = [
                        html.Br(),
                        html.Div(
                            html.B(
                                "START",
                                style = {"font-size": 25}
                            ),
                            style = tools.flex_style
                        ),
                        html.Div(
                            html.Div(
                                "a Measurement",
                                style = {"font-size": 20}
                            ),
                            style = tools.flex_style
                        ),
                        html.Br()
                    ],
                    color = "primary",
                    id = "start-measurement-button",
                    style = {"width": "300px"}
                ),
                style = tools.flex_style
            ),
            html.Br(),html.Br(),
            html.H5(
                "ESP SETTINGS:",
                style = {"color": "black"}
            ),
            dbc.Alert(
                children = [
                    html.Br(),
                    dbc.Row(
                        children = [
                            settings_col("Interval:", f"{settings['interval']} sec"),
                            settings_col("Tolerance Acceleration:", f"{settings['tolerance_lat_acc']} m/s²"),
                            settings_col("Stable Amount:", f"{settings['stable_amount']} values"),
                            settings_col("Data Package Size:", f"{settings['data_package_size']} packages"),
                            settings_col("Standby Refresh:", f"{settings['standby_refresh']} sec"),
                        ],
                        justify = "around"
                    ),
                    html.Div(
                        dbc.Button(
                            "Change Settings",
                            color = "primary",
                            id = "change-settings-button"
                        ),
                        style = tools.flex_style
                    )
                ],
                color = "primary"
            ),
            
            #Modal for changing settings
            dbc.Modal(
                children = [
                    tools.modal_header("Change Settings"),
                    dbc.ModalBody(
                        children = [
                            settings_input("Interval:", settings['interval'], "sec"),
                            html.Br(),
                            settings_input("Tolerance Acceleration:", settings['tolerance_lat_acc'], "m/s²"),
                            html.Br(),
                            settings_input("Stable Amount:", settings['stable_amount'], "values"),
                            html.Br(),
                            settings_input("Data Package Size:", settings['interval'], "packages"),
                            html.Br(),
                            settings_input("Standby Refresh:", settings['interval'], "sec"),
                            html.Br(),
                            html.Div(
                                dbc.Button(
                                    html.Div(
                                        "Confirm",
                                        style = {"width": "150px"}
                                    ),
                                    color = "primary",
                                    id = "confirm-changes-button"
                                ),
                                style = tools.flex_style
                            )
                        ]
                    )
                ],
                centered = True,
                keyboard = True,
                size = "lg",
                id = "change_settings_modal",
                is_open = True
            )
        ]
    )

#live monotiorin content
def live_monitoring():
    return html.Div(
        children = [
            tools.page_title("Live Monitoring")
        ]
    )

#creating content
def content():
    control_data = api.communicate(requests.get, "/control")["details"]
    
    #set content
    if control_data["measurement"]:
        content = live_monitoring()
    else:
        content = control_esp()
    
    #return content
    return html.Div(
        content,
        id = "control-content"
    )