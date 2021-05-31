import dash_bootstrap_components as dbc
import dash_html_components as html
import requests

#load scripts
import api
import tools

#control esp content
def control_esp():
    return html.Div(
        children = [
            tools.page_title("Control ESP32"),
            html.Br(),html.Br(),
            html.Div(
                dbc.Button(
                    children = [
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
                        )
                    ],
                    color = "primary",
                    id = "start-measurement-button",
                    style = {"width": "300px"}
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