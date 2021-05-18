import dash_bootstrap_components as dbc
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
            duration = data[4]
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
            tools.page_title("Measurements"),
            html.Br(),
            html.Div(
                dbc.Table(
                    children = [
                        html.Thead(
                            html.Tr(
                                children = [
                                    html.Th("ID"),
                                    html.Th("NAME"),
                                    html.Th("TIMESTAMP"),
                                    html.Th("DURATION"),
                                    html.Th("SUCCESS"),
                                    html.Th("")
                                ],
                                className="table-primary"
                            )
                        ),
                        html.Tbody(
                            children = table_rows
                        )
                    ]
                ),
                style= {
                    "overflowX": "scroll"
                }
            )
        ]
    )