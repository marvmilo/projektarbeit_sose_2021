import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objects as go
import plotly.subplots as sp
import numpy as np
import datetime as dt
import math

#load scripts
import api
import tools

#for calculating weight
def calculate_weight(voltage):
    return voltage**4

#for creating info card
def info_card(header, value):
    return dbc.Alert(
        html.Div(
            children = [
                html.Div(
                    html.H5(
                        header,
                        style = {"color": "black"}
                    ),
                    style = tools.flex_style
                ),
                html.Br(),html.Br(),
                html.Div(
                    html.H2(
                        value,
                        style = {"color": tools.accent_color}
                    ),
                    style = tools.flex_style
                ),
                html.Br(),html.Br(),
                html.Div(style = {"width": "300px"})
            ],
        ),
        color = "primary",
        style = {"height": "90%"}
    )

#content of measurements site
def content(id):
    data = api.get_measurement(id)
    
    #if no data return Error message
    if not data:
        error_div = html.Div(
            children = [
                html.Div(
                    f"No Data at ID: {id}",
                    style = tools.flex_style
                ),
                html.Br(),
                html.Div(
                    html.A(
                        dbc.Button(
                            "View Measurements",
                            color = "primary"
                        ),
                        href = "/measurements"
                    ),
                    style = tools.flex_style
                )
            ]
        )
        return tools.error_page(error_div)
    
    #set success badge
    if data["info"]["success"]:
        success_badge = dbc.Badge(
            str(True),
            color = "success"
        )
    else:
        success_badge = dbc.Badge(
            str(False),
            color = "danger"
        )
    
    #building graph data
    accuracy = 2
    time_data = []
    for d in data["data"]:
        time_delta = tools.load_datetime(d[1]) - tools.load_datetime(data["data"][0][1])
        seconds = round(tools.timedelta_to_seconds(time_delta), accuracy)
        time_data.append(seconds)
    
    #for calculating final weight
    def calculate_final_weight():
        stable_vals = [d[-1] for d in data["data"][-data["info"]["stable_amount"]:]]
        avg = sum(stable_vals) / len(stable_vals)
        return float(round(calculate_weight(avg), accuracy))
    
    #calculate final weight
    if data["info"]["success"]:
        #create weight div
        weight_div = html.Div(
            dbc.Row(
                children = [
                    dbc.Col(
                        html.Div(
                            html.B(calculate_final_weight()),
                            style = {
                                "font-size": 100,
                                "color": tools.accent_color
                            }
                        ),
                        width = "auto"
                    ),
                    dbc.Col(
                        html.Div(
                            children = [
                                html.Br(),
                                html.B("kg")
                            ],
                            style = {
                                "font-size": 40
                            }
                        ),
                        width = "auto"
                    )
                ],
                no_gutters = True
            ),
            style = tools.flex_style
        )
    else:
        weight_div = html.Div(
            children = [
                dbc.Row(
                    children = [
                        dbc.Col(
                            html.Div(
                                children = [
                                    html.Br(),
                                    html.B("NOT"),
                                    html.Br(),
                                    html.B("STABLE :(")
                                ],
                                style = {
                                    "font-size": 25,
                                    "color": tools.accent_color
                                }
                            ),
                            width = "auto"
                        ),
                        dbc.Col(
                            html.Div(
                                children = [
                                    html.Br(),
                                    "Could not calculate weight.",html.Br(),
                                    "Due to interruption of the",html.Br(),
                                    "measurement, the measured data",html.Br(),
                                    "is not stable enough!",html.Br()
                                ]
                            )
                        )
                    ]
                )
            ],
            style = tools.flex_style
        )
    
    #for creating voltage/weight graph
    def build_voltage_weight(data):
        fig = sp.make_subplots(specs = [[{"secondary_y": True}]])
        
        #colors
        voltage_color = "#004B9B"
        weight_color = "#007BFF"
        #calculate data
        voltage_data = [round(d[-1], accuracy) for d in data["data"]]
        weight_data = [round(calculate_weight(v), accuracy) for v in voltage_data]
        
        #add weight data
        fig.add_trace(
            go.Bar(
                x = time_data,
                y = weight_data,
                name = "Weight",
                #mode = "lines+markers",
                marker_color = weight_color
            ),
            secondary_y = False
        )
        
        #add voltage data
        fig.add_trace(
            go.Scatter(
                x = time_data,
                y = voltage_data,
                name = "Voltage",
                line_shape = "spline",
                marker_color = voltage_color
            ),
            secondary_y = True
        )
        
        #add line of final weight
        if data["info"]["success"]:
            fig.add_trace(
                go.Scatter(
                    x = time_data[-data["info"]["stable_amount"]:],
                    y = [round(calculate_final_weight(), accuracy) for i in range(data["info"]["stable_amount"])],
                    name = "Final Weight",
                    mode = "lines",
                    marker_color = "black"
                ),
                secondary_y = False
            )
        
        #add stable phase
        i = 0
        stable_phases = []
        for u, d in enumerate(data["data"]):
            if d[-2]:
                i += 1
            
                #detect begin of stable phase
                if i == 1:
                    begin = tools.load_datetime(d[1])
                
                #detect end of measurement
                if i == data["info"]["stable_amount"]:
                    end = tools.load_datetime(data["data"][u][1])
                    stable_phases.append([begin,end])
            else:
                #detect end of stable phase
                if i > 1:
                    end = tools.load_datetime(data["data"][u-1][1])
                    stable_phases.append([begin,end])
                    
                i = 0
        
        for phase in stable_phases:
            measurement_start = tools.load_datetime(data["data"][0][1])
            begin = tools.timedelta_to_seconds(phase[0] - measurement_start)
            end = tools.timedelta_to_seconds(phase[1] - measurement_start)
            
            #add to fig
            try:
                fig.add_vrect(
                    x0 = begin - data["info"]["interval"]/2,
                    x1 = end +  data["info"]["interval"]/2,
                    fillcolor = tools.accent_color[0],
                    opacity = 0.15,
                    line_width = 0
                )
            except TypeError:
                pass
                
        #add figure title
        fig.update_layout(
            title = tools.graph_title("VOLTAGE/WEIGHT COURSE")
        )
        
        #update hovermode
        fig.update_layout(hovermode="x unified")
        
        # Set x-axis title
        fig.update_xaxes(title_text="<b>Runtime</b> in seconds")
        
        # Set y-axes titles
        fig.update_yaxes(title_text=f"<b style=\"color:{voltage_color}\">Voltage</b> in V", secondary_y=True)
        fig.update_yaxes(title_text=f"<b style=\"color:{weight_color}\">Weight</b> in kg", secondary_y=False)
                
        #return figure
        return fig

    def build_acceleration(data):
        #get data
        accx = [d[2] for d in data["data"]]
        accy = [d[3] for d in data["data"]]
        accz = [d[4] for d in data["data"]]
        
        #create figure
        fig = go.Figure()
        
        #add stable cicle
        try:
            phi = np.linspace(0, 2*math.pi, 100)
            x = data["info"]["tolerance_latacc"] * np.cos(phi)
            y = data["info"]["tolerance_latacc"] * np.sin(phi)
            r = np.sqrt(x**2 + y**2)
            J = np.where(y<0)
            theta  = np.arctan2(y, x)
            theta[J]= theta[J] + 2*math.pi
            #add to figure
            fig.add_trace(
                go.Scatterpolar(
                    r=r,
                    theta=theta *180 / np.pi,
                    mode='lines', 
                    fill='toself', 
                    name='<b>Stable</b> Area',
                    opacity = 0.75,
                    line = dict(
                        color = "#004B9B"
                    )
                )
            )
        except np.core._exceptions._UFuncNoLoopError:
            pass
        
        #calculate polar cordinates
        try:
            range_i = range(len(accx))
            r = [math.sqrt(accx[i]**2 + accy[i]**2) for i in range_i]
            theta = [math.atan(accy[i] / accx[i]) for i in range_i]
            
            #create figure
            fig.add_trace(
                go.Scatterpolar(
                    r = r,
                    theta = theta,
                    thetaunit = "radians",
                    mode="markers",
                    name = "<b>Acceleration</b> in m/s²",
                    marker = dict(
                        size=7.5, 
                        color = "#007BFF"
                    )
                )
            )
        except ZeroDivisionError:
            pass
        
        #update ticks
        fig.update_polars(
            angularaxis = dict(
                tickmode = "array",
                tickvals = [0, 90, 180, 270],
                ticktext = ["postive<br><b>X-Acc</b>", "postive<br><b>Y-Acc</b>", "negative<br><b>X-Acc</b>", "negative<br><b>Y-Acc</b>"]
            )
        )
        
        #update range
        try:
            if max(r) > data["info"]["tolerance_latacc"]:
                radial_range = max(r)
            else:
                radial_range = data["info"]["tolerance_latacc"]
            radial_range += radial_range/10
        except:
            radial_range = 0
        
        fig.update_polars(
            radialaxis = dict(
                range = [0, radial_range]
            )
        )
        
        #upoate title
        fig.update_layout(
            title = tools.graph_title("X/Y - ACCELERATION")
        )
        
        return fig
    
    #for building table
    def build_table(data):
        table_rows = []
        
        #function for creating cell
        def cell(content):
            return html.Td(
                content
            )
        
        #function for for creating header cell
        def header_cell(header, unit):
            return html.Td(
                children = [
                    html.B(header),
                    html.Br(),
                    unit  
                ],
                style = {
                    "background-color": tools.light_accent_color,
                    "border-width": "0px",
                    "position": "sticky",
                    "top": 0
                }
            )
        
        #iter over data
        for row in data["data"]:
            
            #calculate runtime
            runtime = tools.load_datetime(row[1]) - tools.load_datetime(data["data"][0][1])
            second = tools.timedelta_to_seconds(runtime)    
            
            #success badge
            if row[-2]:
                success = html.H5(dbc.Badge("True", color = "success"))
            else:
                success = html.H5(dbc.Badge("False", color = "danger"))
            
            table_rows.append(
                html.Tr(
                    children=[
                        cell(row[0]),
                        cell(round(second, 2)),
                        cell(round(row[-1], 2)),
                        cell(round(calculate_weight(row[-1]), 2)),
                        cell(round(row[2], 2)),
                        cell(round(row[3], 2)),
                        cell(round(row[4], 2)),
                        cell(success)
                    ]
                )
            )
        
        return html.Div(
            dbc.Table(
                children = [
                    html.Thead(
                        html.Tr(
                            children = [
                                header_cell("ID", ""),
                                header_cell("RUNTIME", "in seconds"),
                                header_cell("VOLTAGE", "in V"),
                                header_cell("WEIGHT", "in kg"),
                                header_cell("ACC. X", "in m/s²"),
                                header_cell("ACC. Y", "in m/s²"),
                                header_cell("ACC. Z", "in m/s²"),
                                header_cell("STABLE", "status")
                            ]
                        )
                    ),
                    html.Tbody(
                        children = table_rows,
                    )
                ]
            ),
            style = {
                "overflow": "auto",
                "height": "500px"
            }
        )
    
    #content div
    return html.Div(
        children = [
            #replacements IDs
            html.Div(
                children = [
                    dbc.Button(id = "start-measurement-button"),
                    dbc.Button(id = "change-settings-button"),
                    dbc.Input(id = "measurement-name-input"),
                    dcc.Interval(id = "heartbeat-esp-interval", max_intervals = 0),
                    dbc.Modal(id = "heartbeat-esp-modal"),
                    dbc.Modal(id = "esp-reachable-modal")
                ],
                style = {"display": "none"}
            ),
            
            #page title
            dbc.Row(
                children = [
                    dbc.Col(
                        "Success: ",
                        width = "auto"
                    ),
                    dbc.Col(
                        style = {"width": "10px"},
                        width = "auto"
                    ),
                    dbc.Col(
                        success_badge,
                        width = "auto"
                    )
                ],
                justify = "end",
                no_gutters = True,
                style = {"font-size": "20px"} 
            ),
            html.Br(),
            tools.page_title(f"Details Measurement"),
            html.Div(
                html.H1(
                    data["info"]["name"],
                    style = {"color": tools.accent_color},
                    id = "details-name"
                ),
                style = tools.flex_style
            ),
            html.Br(),
            
            #first info row
            dbc.Row(
                children = [
                    dbc.Col(
                        info_card("TIMESTAMP", tools.pp_timestamp(data["info"]["timestamp"]))
                    ),
                    dbc.Col(
                        info_card("DURATION", tools.pp_duration(data["info"]["duration"]))
                    )
                ],
                style = {"marginBottom": 8}
            ),
            
            #second info row
            dbc.Row(
                children = [
                    dbc.Col(
                        info_card("INTERVAL", f"{data['info']['interval']} sec")
                    ),
                    dbc.Col(
                        info_card("ACCELERATION TOLERANCE", f"{data['info']['tolerance_latacc']} m/s²")
                    ),
                    dbc.Col(
                        info_card("STABLE AMOUNT", f"{data['info']['stable_amount']} vals")
                    ),
                ]
            ),
            html.Br(),
            html.Br(),
            
            #calculated weight
            html.Div(
                html.H5("FINAL WEIGHT"),
                style = tools.flex_style
            ),
            weight_div,
            html.Br(),
            html.Br(),
            
            #voltage/weight graph
            dcc.Graph(figure = build_voltage_weight(data)),
            
            #acceleration and edit row
            dbc.Row(
                children = [
                    dbc.Col(
                        children = [
                            dcc.Graph(figure = build_acceleration(data)),
                            html.Div(style = {"width": "350px"})
                        ]
                    ),
                    dbc.Col(
                        children = [
                            html.Br(),
                            dbc.Alert(
                                children = [
                                    html.H5(
                                        "EDIT MEASUREMENT",
                                        style = {"color": "black"}
                                    ),
                                    html.Br(),
                                    "Rename Measurement:",
                                    html.Br(),html.Br(),
                                    dbc.Input(
                                        id = "rename-input",
                                        placeholder = "Enter new name ..."
                                    ),
                                    html.Br(),
                                    dbc.Button(
                                        "RENAME",
                                        id = "rename-button",
                                        color = "primary",
                                        block = True
                                    ),
                                    html.Br(),html.Br(),
                                    "Delete Measurement:",
                                    html.Br(),html.Br(),
                                    dbc.Button(
                                        "DELETE",
                                        id = "delete-button",
                                        color = "primary",
                                        block = True
                                    ),
                                    html.Br(),
                                    html.Div(style = {"width": "300px"})
                                ],
                                color = "primary"
                            )
                        ]
                    )
                ]
            ),
            html.Br(),
            
            #table at end of page
            build_table(data),
            
            #rename Modal
            dbc.Modal(
                children = [
                    tools.modal_header("Measurement renamed!"),
                    dbc.ModalBody(
                        children = [
                            html.Br(),
                            dbc.Row(
                                children = [
                                    dbc.Col(
                                        html.B(
                                            "",
                                            style = {
                                                "font-size": 30,
                                                "color": tools.accent_color
                                            },
                                            id = "old-name"
                                        ),
                                        width = "auto"
                                    ),
                                    dbc.Col(
                                        html.B(
                                            "➞",
                                            style = {
                                                "font-size": 30
                                            }
                                        ),
                                        width = "auto"
                                    ),
                                    dbc.Col(
                                        html.B(
                                            "",
                                            style = {
                                                "font-size": 30,
                                                "color": tools.accent_color
                                            },
                                            id = "new-name"
                                        ),
                                        width = "auto"
                                    )
                                ],
                                justify = "center"
                            ),
                            html.Br(),
                            html.Div(
                                "Reload page for displaying new name.",
                                style = tools.flex_style
                            ),
                            html.Br()
                        ]
                    )
                ],
                centered = True,
                keyboard = True,
                size = "lg",
                id = "rename-modal"
            ),
            
            #delete Modal are you Sure
            dbc.Modal(
                children = [
                    tools.modal_header("Delete Measurment?"),
                    dbc.ModalBody(
                        children = [
                            html.Div(
                                f"Are You sure to delete this measurement?",
                                style = tools.flex_style
                            ),
                            html.Br(),
                            dbc.Row(
                                children = [
                                    dbc.Col(
                                        dbc.Button(
                                            "YES",
                                            color = "primary",
                                            id = "delete-yes"
                                        ),
                                        width = "auto"
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "NO",
                                            color = "primary",
                                            id = "delete-no"
                                        ),
                                        width = "auto"
                                    )
                                ],
                                justify = "center"
                            ),
                            html.Br()
                        ]
                    )
                ],
                centered = True,
                keyboard = True,
                id = "delete-modal-?"
            ),
            
            #delete confirm mdodal
            dbc.Modal(
                children = [
                    tools.modal_header("Measurment deleted!"),
                    dbc.ModalBody(
                        children = [
                            html.Div(
                                "This measurement was deleted!",
                                style = tools.flex_style
                            ),
                            html.Br(),
                            html.Div(
                                html.A(
                                    dbc.Button(
                                        "CLOSE",
                                        color = "primary"
                                    ),
                                    href = "/measurements"
                                ),
                                style = tools.flex_style,
                            ),
                            html.Br()
                        ]
                    )
                ],
                centered = True,
                keyboard = True,
                id = "delete-modal-confirm"
            )
        ]
    )