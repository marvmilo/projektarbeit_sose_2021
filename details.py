import dash_bootstrap_components as dbc
import dash_html_components as html

#load scripts
import api
import tools

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
            ],
        ),
        color = "primary",
        style = {"height": "90%"}
    )

#content of measurements site
def content(id):
    data = api.get_measurement(id)
    
    #content div
    return html.Div(
        children = [
            #page title
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
        ]
    )