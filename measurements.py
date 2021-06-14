import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import datetime

#load scripts
import api
import tools

#content of measurements site
def content():
    #get data of all measurements
    measurements = api.get_table("measurements")
    
    #return error content if no measurements
    if not len(measurements):
        error_div = html.Div(
            children = [
                html.Div(
                    "Nothing here till yet :(",
                    style = tools.flex_style
                ),
                html.Br(),
                html.Div(
                    html.A(
                        dbc.Button(
                            "Start Measurement",
                            color = "primary"
                        ),
                        href = "/control"
                    ),
                    style = tools.flex_style
                )
            ]
        )
        return tools.error_page(error_div)
    
    #values
    table_rows = []
    not_known = "-"
    
    #function for creating cell
    def cell(content):
        return html.Td(
            content,
            style = {
                "white-space": "nowrap"
            }
        )
    
    #function for for creating header cell
    def header_cell(header):
        return html.Td(
            children = [
                html.B(header)
            ],
            style = {
                "background-color": tools.light_accent_color,
                "border-width": "0px",
                "position": "sticky",
                "top": 0
            }
        )
    
    #iter over measurements
    for measurement in api.get_measurements():
        #get data of current measurement
        data = None
        index = int(measurement.split("_")[1])
        for m in measurements:
            if m[0] == index:
                data = m
        
        #get name
        try:
            name = data[1]
        except:
            name = not_known
        
        #get timestamp
        try:
            timestamp = tools.pp_timestamp(data[2])
        except Exception as e:
            timestamp = not_known
        
        #get duration
        try:
            duration = tools.pp_duration(data[4])
        except:
            duration = not_known
        
        #get success badge
        try:
            if data[7]:
                success = html.H4(dbc.Badge("True", color = "success"))
            else:
                raise Exception()
        except:
            success = html.H4(dbc.Badge("False", color = "danger"))
        
        #add row
        table_rows.append(
            html.Tr(
                children=[
                    cell(index),
                    cell(name),
                    cell(timestamp),
                    cell(duration),
                    cell(success),
                    cell(
                        html.A(
                            dbc.Button(
                                "VIEW",
                                color = "primary",
                                block = True,
                                size = "sm"
                            ),
                            href = f"/details/{index}"
                        ) 
                    )
                ]
            )
        )
        
    #return content
    return html.Div(
        children = [
            #replacements IDs
            html.Div(
                children = [
                    dbc.Button(id = "start-measurement-button"),
                    dbc.Button(id = "change-settings-button"),
                    dbc.Button(id = "rename-button"),
                    dbc.Button(id = "delete-button"),
                    dbc.Button(id = "close-results-button"),
                    dbc.Input(id = "measurement-name-input"),
                    dcc.Interval(id = "heartbeat-esp-interval", max_intervals = 0),
                    dbc.Modal(id = "heartbeat-esp-modal"),
                    dbc.Modal(id = "esp-reachable-modal")
                ],
                style = {"display": "none"}
            ),
            
            #page content
            tools.page_title("Measurements"),
            html.Br(),
            html.Div(
                dbc.Table(
                    children = [
                        html.Thead(
                            html.Tr(
                                children = [
                                    header_cell("ID"),
                                    header_cell("NAME"),
                                    header_cell("TIMESTAMP"),
                                    header_cell("DURATION"),
                                    header_cell("SUCCESS"),
                                    header_cell("")
                                ]
                            )
                        ),
                        html.Tbody(
                            children = table_rows
                        )
                    ]
                ),
                style = {
                    "overflow": "auto",
                    "height": "65vh"
                }
            )
        ]
    )