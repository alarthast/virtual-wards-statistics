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
    CAPACITY_PER_POPULATION,
    DATE,
)
from wardstats.components import get_map, get_dropdown_options, get_time_series


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
        html.H1("NHS Virtual Wards Statistics", id="header"),
        html.H5(
            [
                "Data source: ",
                html.A("NHS England", href=config["VIRTUAL_WARDS_STATS_HOMEPAGE"]),
            ],
            style={"text-align": "center"},
        ),
        html.Hr(),
        html.Div(
            [
                dcc.Dropdown(
                    id="dropdown",
                    options=get_dropdown_options(config),
                    value=CAPACITY_PER_POPULATION,
                ),
                dcc.Slider(
                    id="slider",
                    min=0,
                    max=len(dates) - 1,
                    marks={i: label for i, label in enumerate(date_labels)},
                    value=len(dates) - 1,
                    step=1,
                    updatemode="drag",
                ),
            ],
            style={"width": "50vw"},
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(
                        id="map",
                        figure=get_map(data),
                        style={
                            "width": "55vw",
                            "height": "80vh",
                            "margin": 0,
                            "display": "inline-block",
                        },
                    ),
                    className="left",
                ),
                html.Div(
                    [
                        dcc.Graph(
                            id="time_series",
                            figure=get_time_series(data, "QYG"),
                            style={
                                "width": "35vw",
                                "height": "25vw",
                                "display": "inline-block",
                            },
                        ),
                        html.Div(
                            children=[
                                html.P(
                                    [
                                        "This is a dashboard created by Siu Ying Wong as part of a job application. The dashboard is kept simplistic as its main purpose is for demonstrating skills in engineering ETL pipelines, building visualisations and handling healthcare data. ",
                                        "The source code for constructing the pipeline and dashboard can be found on ",
                                        html.A(
                                            "GitHub",
                                            href="https://github.com/alarthast/virtual-wards-statistics/tree/main",
                                        ),
                                        ".",
                                        html.Br(),
                                        html.Br(),
                                        "The dashboard uses publicly available data on the NHS England website and shows the capacity, usage and occupancy of virtual wards across the 42 Intergrated Care Boards (ICBs) in England.",
                                        html.Br(),
                                        "Both graphs are updated by the dropdown. The slider updates the data shown on the map. Clicking on an ICB on the map updates the chart on the right.",
                                        html.Br(),
                                        html.Br(),
                                        "The definitions and notes accompanying the raw data are provided below.",
                                    ]
                                )
                            ],
                            style={
                                "width": "35vw",
                                "height": "30vh",
                                "display": "inline-block",
                                "align": "justify",
                            },
                        ),
                    ],
                    className="right",
                ),
            ],
            className="container",
        ),
        html.Div(
            [
                html.H5("Introduction:"),
                html.P(
                    "The Virtual Ward Capacity and Occupancy statistics are Management Information. The data is reported by lead virtual ward providers in England. Data is collected by NHS England via the Virtual Ward sitrep which was launched in April 2022. "
                ),
                html.H5("Definitions:"),
                html.P(
                    "Where the monthly figure is reported, this represents the last sitrep data submitted in the relevant calendar month. For example, monthly published data for February 2024 is taken from the last sitrep submission of the calendar month, which was on 23rd February 2024. "
                ),
                html.H5("Notes:"),
                html.Ol(
                    [
                        html.Li(
                            "Virtual Ward Capacity (number) which is also referred to as Virtual Ward 'bed' Capacity. This is the data reported in the final sitrep data submission by providers in the calendar month. (See also definitions.)"
                        ),
                        html.Li(
                            [
                                "Virtual Ward Capacity per 100,000 GP registered population aged 16 years and over. A calculation where: Virtual Ward Capacity per 100,000 GP registered population = (Virtual Ward Capacity/Patients registered at a GP Practice) x 100,000. ",
                                "The ",
                                html.A(
                                    "GP registered population",
                                    href="https://digital.nhs.uk/data-and-information/publications/statistical/patients-registered-at-a-gp-practice",
                                ),
                                " was for April 2023. ",
                            ]
                        ),
                        html.Li(
                            "The number of patients on a virtual ward, at 8am Thursday prior to the sitrep submission period. For example, 8am Thursday 15th February 2024 for February 2024 published data."
                        ),
                        html.Li(
                            "Virtual Ward Occupancy as a percentage of Virtual Ward Capacity. A calculation where: Occupancy =  Patients in a Virtual Ward / Virtual Ward Capacity (%)"
                        ),
                    ]
                ),
                html.H5("Data Quality:"),
                html.P(
                    "As a 'sitrep' data collection, there are likely to be some data quality issues in what is submitted. NHS England routinely monitors and reviews data quality which includes, for example: coverage of the provider return; capacity data; and occupancy levels. In taking a snapshot of virtual ward occupancy at one point within the month, this figure in particular can be considered indicative and where reported occupancy exceeds 100% - likely as a result of data quality issues - these figures have been shown as '100%*' when hovered over on the dashboard."
                ),
                html.H5("Data Context:"),
                html.P(
                    [
                        "More information regarding virtual wards can be found on the ",
                        html.A(
                            "NHS England website",
                            href="https://www.england.nhs.uk/virtual-wards/",
                        ),
                        ".",
                    ]
                ),
            ],
        ),
    ]
)


@app.callback(
    [Output("map", "figure"), Output("time_series", "figure", allow_duplicate=True)],
    Input("dropdown", "value"),
    prevent_initial_call="initial_duplicate",
)
def update_metric_shown(col):
    return get_map(data, col=col), get_time_series(data, icb_code="QYG", col=col)


@app.callback(
    Output("map", "figure", allow_duplicate=True),
    [Input("slider", "value"), Input("dropdown", "value")],
    prevent_initial_call="initial_duplicate",
)
def update_date_shown(slider, col):
    date = date_lookup[date_labels[slider]]
    return get_map(data, col=col, date=date)


@app.callback(
    Output("time_series", "figure", allow_duplicate=True),
    [Input("map", "clickData"), Input("dropdown", "value")],
    prevent_initial_call="initial_duplicate",
)
def update_icb_shown(clickData, col):
    if clickData is not None:
        location = clickData["points"][0]["location"]
        return get_time_series(data, icb_code=location, col=col)
    return no_update


if __name__ == "__main__":
    app.run(debug=False)
