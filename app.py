# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from datetime import date

import dash_bootstrap_components as dbc
import dash_daq as daq
import finnhub
import plotly.express as px
from dash import Dash, Input, Output, dcc, html

from utils.chart import Chart


def prepare_symbols(symbols: list):
    for symbol in symbols:
        del symbol["currency"]
        del symbol["displaySymbol"]
        del symbol["figi"]
        del symbol["isin"]
        del symbol["mic"]
        del symbol["shareClassFIGI"]
        del symbol["symbol2"]
        del symbol["type"]


app = Dash(__name__)

f = finnhub.Client(api_key="cdfl83iad3i8a4q95080cdfl83iad3i8a4q9508g")
data = f.stock_symbols(
    "US", mic="XNYS", security_type="Common Stock"
) + f.stock_symbols("US", mic="XNAS", security_type="Common Stock")

prepare_symbols(data)

symbols = {}

for detailed_data in data:
    symbols[detailed_data["symbol"]] = detailed_data["description"]


print(len(list(symbols.keys())))
# nasdaq_symbols = []
# nyse_symbols = []

nav = dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink("Active", active=True, href="#")),
        dbc.NavItem(dbc.NavLink("A link", href="#")),
        dbc.NavItem(dbc.NavLink("Another link", href="#")),
        dbc.NavItem(dbc.NavLink("Disabled", disabled=True, href="#")),
        dbc.DropdownMenu(
            [dbc.DropdownMenuItem("Item 1"), dbc.DropdownMenuItem("Item 2")],
            label="Dropdown",
            nav=True,
        ),
    ]
)

app.layout = html.Div(
    [
        html.Div(
            children=[
                html.Label("Stocks"),
                dcc.Dropdown(
                    options=symbols, value="TSLA", id="symbol-dropdown"
                ),
                html.Div(
                    children=[
                        dcc.DatePickerRange(
                            id="date-picker-range",
                            display_format="Y-M-D",
                            min_date_allowed=date(2000, 1, 1),
                            max_date_allowed=date.today(),
                            initial_visible_month=date(2023, 1, 1),
                            start_date=date(2023, 1, 1),
                            end_date=date.today(),
                        ),
                        daq.BooleanSwitch(
                            id="trend-switch",
                            on=True,
                            label="Trend",
                            labelPosition="bottom",
                            color="#1520A6",
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justify-content": "space-between",
                        "padding-top": 10,
                    },
                ),
            ],
            style={"padding": 10, "flex": 1},
        ),
        html.Div(
            dcc.Graph(
                id="graph",
                figure={
                    "layout": {
                        "height": 1000,  # px
                    },
                },
            )
        ),
    ],
    style={"display": "flex", "flex-direction": "column"},
)


@app.callback(
    Output("graph", "figure"),
    Input(component_id="symbol-dropdown", component_property="value"),
    Input(component_id="date-picker-range", component_property="start_date"),
    Input(component_id="date-picker-range", component_property="end_date"),
    Input(component_id="trend-switch", component_property="on"),
)
def my_func(symbol, start_date, end_date, trend):

    start_date += " 00:00:00"
    end_date += " 00:00:00"

    # print("gege")
    resolution = "D"

    cmp = Chart(symbol, resolution, start_date, end_date)

    chart = cmp.get_chart(trend=trend, window=20)

    return chart


if __name__ == "__main__":
    app.run_server(debug=True)
