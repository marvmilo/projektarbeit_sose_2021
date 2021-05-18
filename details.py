import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.subplots as sp

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
                html.Br(),
                html.Div(
                    html.H3(
                        value,
                        style = {"color": tools.accent_color}
                    ),
                    style = tools.flex_style
                ),
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
        time_delta = tools.load_datetime(d[1]) - tools.load_datetime(data["info"]["timestamp"])
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
        weight_color = "#0068FF"
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
                    x = time_data[-10:],
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
            measurement_start = tools.load_datetime(data["info"]["timestamp"])
            begin = tools.timedelta_to_seconds(phase[0] - measurement_start)
            end = tools.timedelta_to_seconds(phase[1] - measurement_start)
            
            #add to fig
            fig.add_vrect(
                x0 = begin - data["info"]["interval"],
                x1 = end +  data["info"]["interval"],
                fillcolor = tools.accent_color[0],
                opacity = 0.15,
                line_width = 0
            )
            
        #add figure title
        fig.update_layout(
            title = {
                "text": "VOLTAGE/WEIGHT TREND",
                "font": {
                    "size": 20,
                    "color": "black" 
                }
            }
        )
        
        #set legend position
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
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
    
    #content div
    return html.Div(
        children = [
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
                    style = {"color": tools.accent_color}
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
                        info_card("DURATION", data["info"]["duration"])
                    )
                ],
                style = {"marginBottom": 8}
            ),
            
            #second info row
            dbc.Row(
                children = [
                    dbc.Col(
                        info_card("INTERVAL", data["info"]["interval"])
                    ),
                    dbc.Col(
                        info_card("ACCELERATION TOLERANCE", data["info"]["tolerance_latacc"])
                    ),
                    dbc.Col(
                        info_card("STABLE AMOUNT", data["info"]["stable_amount"])
                    ),
                ]
            ),
            html.Br(),
            html.Br(),
            
            #calculated weight
            html.Div(
                html.H5("CALCULATED WEIGHT"),
                style = tools.flex_style
            ),
            weight_div,
            html.Br(),
            html.Br(),
            
            #voltage/weight graph
            dcc.Graph(figure = build_voltage_weight(data))
        ]
    )