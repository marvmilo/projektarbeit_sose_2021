import json
import flask
import datetime
import dash_html_components as html
import dash_bootstrap_components as dbc

#get sql script
import api

#values
udf = "./GUI/user_data.json"
user_table = "user_data"
flex_style = {
    "display": "flex",
    "justify-content": "center",
    "align-items": "center"
}
accent_color = "#007BFF",
navbutton_spacing = html.Div(style = {"width": "5px"})

#for getting current user
def get_user():
    return flask.request.authorization["username"]

#for getting user data
def get_user_data(user = None):
    user_data = api.get_table("user_data")
    user_data = {
        u[0]: {
            "password": u[1],
            "role": u[2],
            "url": u[3],
            "details_id": u[4]
        }
        for u in user_data
    }
    if user:
        if user in user_data:
            return user_data[user]
        else:
            return None
    else:
        return user_data

#for getting credentials of all users
def get_user_credentials():
    user_data = get_user_data()
    return {user : user_data[user]["password"] for user in user_data}

#update current positon of user
def update_user_url(user, url):
    api.execute_sql(f"UPDATE user_data SET cur_url = \"{url}\" WHERE name = \"{user}\"")

#update current details id of user
def update_user_details(user, id):
    api.execute_sql(f"UPDATE user_data SET cur_details_id = \"{id}\" WHERE name = \"{user}\"")

#creates 404 page
def not_found_page():
    flex_style["height"] = "100%"
    return html.Div(
        children = [
            html.H1("404"),
            html.H3("not found!")
        ],
        style = flex_style
    )

#creates API not reachable page
def error_page(error_msg):
    return html.Div(
        children = [
            html.Div(html.H1("ERROR"), style = flex_style),
            html.Div(html.H3(error_msg), style = flex_style)
        ]
    )

#creates page title
def page_title(title, color = "black"):
    return html.Div(
        html.H3(
            title,
            style = {"color": color}
        ),
        style = flex_style
    )

#creates div for page content:
def content_div():
    return html.Div(
        html.Div(
            children = [
                html.Div(style = {"height": "200px"}),
                html.Div(
                    dbc.Spinner(),
                    style = flex_style
                )
            ]
        ),
        id = "content",
        style = {
            "padding": "2% 5%"
        }
    )

#loads a datetime from a timestamp
def load_datetime(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y_%m_%dT%H_%M_%S_%f")

#function for pretty printing timestamp
def pp_timestamp(timestamp):
    if timestamp == "-":
        return "-"
    return load_datetime(timestamp).strftime("%a,  %d.%b.%Y, %H:%M")