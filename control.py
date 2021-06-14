import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import requests

#load scripts
import api
import tools

#start measurement buttons
def start_measurement_button():
    return html.Div(
        children = [
            html.Div(
                html.Div(
                    children = [
                        html.H5("START MEASUREMENT:"),
                        dbc.InputGroup(
                            children = [
                                dbc.InputGroupAddon("NAME", addon_type = "prepend"),
                                dbc.Input(
                                    placeholder = "enter name ...",
                                    id = "measurement-name-input"
                                )
                            ],
                            className = "mb-3",
                            style = {"width": "300px"}
                        )
                    ]
                ),
                style = tools.flex_style
            ),
            html.Div(
                children = [
                    dbc.Button(
                        "START",
                        id = "start-measurement-button",
                        size  = "lg",
                        color = "primary"
                    )
                ],
                style = tools.flex_style
            )
        ]    
    )
    
#show running measurement
def measurement_running():
    return html.Div(
        children = [
            dbc.Progress(
                children = [
                    html.B(
                        "Measurement is running!",
                        style = {"font-size": 45}
                    )
                ],
                value = 100,
                striped = True,
                animated = True,
                style = {
                    "width": "600px",
                    "height": "150px"
                }
            ),
            html.Div(
                html.Div(
                    "waiting for results ...",
                    style = {"font-size": 20}
                ),
                style = tools.flex_style
            ),
            dcc.Interval(
                id = "measuring-interval",
                interval = 5*1000,
                n_intervals = 0
            ),
            html.Div(
                children = [
                    dbc.Button(id = "start-measurement-button"),
                    dbc.Input(id = "measurement-name-input"),
                ],
                style = {"display": "none"}
            ),
        ]
    )

#control esp content
def content():
    settings = api.get_control()
    
    #check if measuring is running
    if settings["measurement"]:
        measuring_content = measurement_running(),
    else:
        measuring_content = start_measurement_button()
    
    #create a table row for settings
    def settings_table_row(name, value, unit , id,  integer = False):
        if integer:
            step = 1
        else:
            step = 0.01
        
        return html.Tr(
            children = [
                html.Td(
                    html.B(name)
                ),
                html.Td(
                    dbc.Input(
                        value = value,
                        id = id
                    ),
                    style = {"width": "125px"}
                ),
                html.Td(unit)
            ]
        )

    #return content
    return html.Div(
        children = [
            #replacements IDs
            html.Div(
                children = [
                    dbc.Button(id = "rename-button"),
                    dbc.Button(id = "delete-button")
                ],
                style = {"display": "none"}
            ),
            
            #page content
            tools.page_title("Control ESP"),
            html.Br(),html.Br(),
            html.Div(
                html.Div(
                    measuring_content,
                    id = "measuring-content",
                    style = {"height": "150px"}
                ),
                style = tools.flex_style
            ),
            html.Br(),html.Br(),
            html.Div(
                html.Div(
                    children = [
                        html.H5("ESP SETTINGS:"),
                        dbc.Alert(
                            children = [
                                html.Div(
                                    dbc.Table(
                                        children = [
                                            settings_table_row("Interval:", settings['interval'], "sec", "interval"),
                                            settings_table_row("Tolerance Acceleration:", settings['tolerance_lat_acc'], "m/s²", "tolerance_lat_acc"),
                                            settings_table_row("Stable Amount:", settings['stable_amount'], "values", "stable_amount"),
                                            settings_table_row("Data Package Size:", settings['data_package_size'], "packages", "data_package_size"),
                                            settings_table_row("Standby Refresh:", settings['standby_refresh'], "sec", "standby_refresh"),
                                        ],
                                        style = {
                                            "max-width": "450px"
                                        },
                                        borderless = True
                                    ),
                                    style = tools.flex_style
                                ),
                                html.Br(),
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
                    ],
                    style= {"min-width": "60%"}
                ),
                style = tools.flex_style
            ),
            
            #modal for checking heartbeat of ESP
            dbc.Modal(
                children = [
                    tools.modal_header("Connecting to ESP"),
                    dbc.ModalBody(
                        children = [
                            html.Div(
                                "Checking if ESP 32 is reachable ...",
                                style = tools.flex_style
                            ),
                            html.Br(),
                            html.Div(
                                dbc.Spinner(),
                                style = tools.flex_style
                            ),
                            html.Br(),
                            dcc.Interval(
                                id = "heartbeat-esp-interval",
                                interval = 1*1000
                            )
                        ]
                    )
                ],
                centered = True,
                backdrop = "static",
                id = "heartbeat-esp-modal"
            ),
            
            #modal if ESP is not reachable
            dbc.Modal(
                children = [
                    tools.modal_header("Connecting to ESP"),
                    dbc.ModalBody(
                        children = [
                            html.Div(
                                "ESP 32 is not reachable.",
                                style = tools.flex_style
                            ),
                            html.Div(
                                html.B(
                                   ":(",
                                   style = {
                                       "font-size": 50,
                                       "color": tools.accent_color
                                    }
                                ),
                                style = tools.flex_style
                            ),
                            html.Br(),
                            html.Div(
                                dbc.Button(
                                    "Close",
                                    color = "primary",
                                    id = "close-esp-reachable"
                                ),
                                style = tools.flex_style
                            )
                        ]
                    )
                ],
                centered = True,
                keyboard = True, 
                id = "esp-reachable-modal"
            ),
            
            #modal if measurement is ready
            dbc.Modal(
                children = [
                    tools.modal_header("Measurement Ready!"),
                    dbc.ModalBody(
                        children = [
                            html.Div(
                                "Click on \"View\" to show results.",
                                style = tools.flex_style
                            ),
                            html.Br(),
                            dbc.Row(
                                children = [
                                    dbc.Col(
                                        html.A(
                                            dbc.Button(
                                                "View",
                                                color = "primary",
                                                id = "view-results-button",
                                                block = True
                                            ),
                                            href = "/details/0",
                                            id = "view-results-href"
                                        ),
                                        width = 3
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "Close",
                                            color = "primary",
                                            id = "close-results-button",
                                            block = True
                                        ),
                                        width = 3
                                    )
                                ],
                                justify = "center"
                            )
                        ]
                    )
                ],
                centered = True,
                backdrop = "static",
                id = "measurement-results-modal"
            ),
            
            #measurement error modal
            dbc.Modal(
                children = [
                    tools.modal_header("Measurement Aborted!"),
                    dbc.ModalBody(
                        children = [
                            html.Div(
                                "An Error accured while running measurement.",
                                style = tools.flex_style
                            ),
                            html.Div(
                                html.B(
                                   ":(",
                                   style = {
                                       "font-size": 50,
                                       "color": tools.accent_color
                                    }
                                ),
                                style = tools.flex_style
                            ),
                            html.Br(),
                            html.Div(
                                dbc.Button(
                                    "Retry",
                                    color = "primary",
                                    id = "retry-measurement-button"
                                ),
                                style = tools.flex_style
                            )
                        ]
                    )
                ],
                centered = True,
                backdrop = "static",
                id = "retry-measurement-modal"
            ),
            
            #change settings Modal
            dbc.Modal(
                children = [
                    tools.modal_header("Settings Changed!"),
                    dbc.ModalBody(
                        children = [
                            html.Div(
                                "Settings were changed.",
                                style = tools.flex_style
                            ),
                            html.Br(),
                            html.Div(
                                dbc.Button(
                                    "Ok",
                                    color = "primary",
                                    id = "close-settings-changed-button",
                                    style = {"width": "150px"}
                                ),
                                style = tools.flex_style
                            )
                        ]
                    )
                ],
                centered = True,
                keyboard = True,
                id = "settings-changed-modal"
            )
        ]
    )