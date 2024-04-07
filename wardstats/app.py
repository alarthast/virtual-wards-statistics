from dash import Dash, dcc, html, Input, Output, callback, no_update
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from wardstats.utils import (
    get_data_path,
    load_config,
    get_icb_boundaries,
    get_icb_name_lookup,
)

from wardstats.config import (
    PROCESSED,
    ICB_CODE,
    ICB_NAME,
    DATE,
    DROPDOWN,
    SLIDER,
    MAP,
    TIMESERIES,
)

from wardstats.components import (
    get_header,
    get_data_source_subheader,
    get_dropdown,
    get_slider,
    get_map,
    get_timeseries,
    get_notes_div,
    get_text_div,
    get_map_figure,
    get_timeseries_figure,
)

config = load_config()
icb_name_lookup = get_icb_name_lookup(get_icb_boundaries(config))
data = pd.read_csv(get_data_path(PROCESSED, "virtual_ward_statistics.csv"))
data[ICB_NAME] = data.replace({ICB_CODE: icb_name_lookup})[ICB_CODE]
dates = np.sort(data[DATE].unique())
date_labels = [pd.to_datetime(date).strftime("%m/%Y") for date in dates]
date_lookup = dict(zip(date_labels, dates))

app = Dash(__name__)
server = app.server
app.layout = html.Div(
    children=[
        get_header(),
        get_data_source_subheader(),
        html.Hr(),
        html.Div(
            [
                get_dropdown(),
                get_slider(dates, date_labels),
            ],
            style={"width": "50vw"},
        ),
        html.Div(
            [
                html.Div(
                    get_map(data),
                    className="left",
                ),
                html.Div(
                    [
                        get_timeseries(data),
                        get_text_div(),
                    ],
                    className="right",
                ),
            ],
            className="container",
        ),
        get_notes_div(),
    ]
)


@app.callback(
    [Output(MAP, "figure"), Output(TIMESERIES, "figure", allow_duplicate=True)],
    [Input(DROPDOWN, "value"), Input(MAP, "clickData")],
    prevent_initial_call="initial_duplicate",
)
def update_metric_shown(col, clickData=None):
    if clickData is not None:
        icb = clickData["points"][0]["location"]
    else:
        icb = "QT6"
    return get_map_figure(data, col=col), get_timeseries_figure(
        data, icb_code=icb, col=col
    )


@app.callback(
    Output(MAP, "figure", allow_duplicate=True),
    [Input(SLIDER, "value"), Input(DROPDOWN, "value")],
    prevent_initial_call="initial_duplicate",
)
def update_date_shown(slider, col):
    date = date_lookup[date_labels[slider]]
    return get_map_figure(data, col=col, date=date)


@app.callback(
    Output(TIMESERIES, "figure", allow_duplicate=True),
    [Input(MAP, "clickData"), Input(DROPDOWN, "value")],
    prevent_initial_call="initial_duplicate",
)
def update_icb_shown(clickData, col):
    if clickData is not None:
        icb = clickData["points"][0]["location"]
        return get_timeseries_figure(data, icb_code=icb, col=col)
    return no_update


if __name__ == "__main__":
    app.run(debug=True)
