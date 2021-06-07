import dash_bootstrap_components as dbc
import dash_html_components as html
import requests

#load scripts
import api
import tools

#control esp content
def control_esp():
    settings = api.get_control()
    
    #create a table row for settings
    def settings_table_row(name, value, unit , integer = False):
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
                        type = "number",
                        value = value,
                        min = 0,
                        step = step
                    ),
                    style = {"width": "125px"}
                ),
                html.Td(unit)
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
            html.Div(
                html.Div(
                    children = [
                        html.H5(
                            "ESP SETTINGS:",
                            style = {"color": "black"}
                        ),
                        dbc.Alert(
                            children = [
                                html.Div(
                                    dbc.Table(
                                        children = [
                                            settings_table_row("Interval:", settings['interval'], "sec"),
                                            settings_table_row("Tolerance Acceleration:", settings['tolerance_lat_acc'], "m/s²"),
                                            settings_table_row("Stable Amount:", settings['stable_amount'], "values"),
                                            settings_table_row("Data Package Size:", settings['interval'], "packages"),
                                            settings_table_row("Standby Refresh:", settings['interval'], "sec"),
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