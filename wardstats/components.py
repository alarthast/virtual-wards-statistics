import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
from dash import dcc, html
from wardstats.utils import (
    get_icb_boundaries,
    load_config,
    filter_date,
    get_icb_name_lookup,
)
from wardstats.config import (
    ICB_CODE,
    CAPACITY_PER_POPULATION,
    ICB_NAME,
    OCCUPANCY,
    DATE,
    SUPPRESSED,
)
from wardstats.config import (
    HEADER,
    DROPDOWN,
    SLIDER,
    MAP,
    TIMESERIES,
    FORMATTERS,
)

config = load_config()
nhs_colours = config["NHS_COLOURS"]
boundaries = get_icb_boundaries(config)
icb_name_lookup = get_icb_name_lookup(boundaries)
map_colour_scale = [[0, "#ffffff"], [1, "#003087"]]


# Functions are pretty much self-explanatory, so docstrings are omitted.
# Instead, I have added commments in a more detailed manner.
def get_header():
    return html.H1(config[HEADER], id=HEADER)


def get_data_source_subheader():
    return html.H5(
        [
            "Data source: ",
            html.A("NHS England", href=config["VIRTUAL_WARDS_STATS_HOMEPAGE_URL"]),
        ],
        style={"text-align": "center"},
    )


def get_dropdown_options(config):
    return [{"label": v, "value": k} for k, v in config["DROPDOWN_OPTIONS"].items()]


def get_dropdown():
    return dcc.Dropdown(
        id=DROPDOWN,
        options=get_dropdown_options(config),
        value=CAPACITY_PER_POPULATION,
    )


def get_slider(dates, date_labels):
    return dcc.Slider(
        id=SLIDER,
        min=0,
        max=len(dates) - 1,
        marks={i: label for i, label in enumerate(date_labels)},
        value=len(dates) - 1,
        step=1,
        updatemode="drag",
    )


def get_template_with_asterisk_for_suppressed_values(df, og_template):
    # Add a "*" to the occupancy value if it was suppressed, in line with the raw data file
    return np.select([df[SUPPRESSED] == False], [og_template], og_template + "*")


def get_map_hovertemplate(df, col):
    # The hovertemplate is set to show the ICB name and the value of the column.
    formatter = config[FORMATTERS][col]
    template = "%{customdata[0]}: %{customdata[1]:" + formatter + "}"
    if col == OCCUPANCY:
        return get_template_with_asterisk_for_suppressed_values(df, template)
    return template


def get_map_range(df, col):
    # In general, the range is set to the min and max of the column.
    # For capacity per population, it might be particularly interesting to see the map darken/lighten over time
    # So the range is set to 0 and 60 to allow easy comparison.
    # At the point of creatiion, the max value was 40-50, so 60 is a reasonable upper limit.
    max_value = df[col].max()
    if col == CAPACITY_PER_POPULATION:
        return [0, max(max_value, 60)]
    return (0, max_value)


def get_mapbox(df, col):
    return px.choropleth_mapbox(
        df,
        geojson=boundaries,
        locations=df[ICB_CODE],
        featureidkey="properties.ICB22CD",
        color=col,
        range_color=get_map_range(df, col),
        color_continuous_scale=map_colour_scale,
        mapbox_style="carto-positron",
        zoom=5.5,
        center=config["MAP_CENTRE"],
        hover_data=[ICB_NAME, col],
    )


def get_map_figure(data: pd.DataFrame, col: str, date: datetime = None):
    df = filter_date(data, date=date)
    fig = get_mapbox(df, col)
    fig.update_coloraxes(colorbar_tickformat=config[FORMATTERS][col])
    fig.update_layout(coloraxis_colorbar_title="", margin=dict(l=10, r=10, t=10, b=10))
    fig.update_traces(hovertemplate=get_map_hovertemplate(df, col))
    return fig


def get_map(data: pd.DataFrame):
    return dcc.Graph(
        id=MAP,
        figure=get_map_figure(data, col=CAPACITY_PER_POPULATION),
        style={
            "width": "55vw",
            "height": "80vh",
            "margin": 0,
            "display": "inline-block",
        },
    )


def get_timeseries_hovertemplate(df, col):
    formatter = config[FORMATTERS][col]
    template = "%{x}: %{y:" + formatter + "}"
    if col == OCCUPANCY:
        return get_template_with_asterisk_for_suppressed_values(df, template)
    return template


def get_timeseries_scatter(df, col):
    template = get_timeseries_hovertemplate(df, col)
    return go.Scatter(
        x=df[DATE],
        y=df[col],
        mode="lines",
        name=col,
        line=dict(color=nhs_colours["BLUE"], width=2),
        hovertemplate=template,
    )


def get_timeseries_yaxis_title(col: str):
    title = config["DROPDOWN_OPTIONS"][col].split("(")[0].strip()
    if col == CAPACITY_PER_POPULATION:
        # Needs to be split into two lines for better readability
        return title.replace("registered ", "registered <br>")
    return title


def get_timeseries_layout_kwargs(icb_code, col):
    return dict(
        title=icb_name_lookup[icb_code],
        xaxis_title="Date",
        xaxis_tickformat="%m/%y",
        yaxis_title=get_timeseries_yaxis_title(col),
        yaxis_tickformat=config[FORMATTERS][col],
    )


def get_capacity_per_population_hrect_kwargs():
    # The number 40-50 is obtained from the data homepage
    return dict(
        y0=40,
        y1=50,
        line_width=0,
        fillcolor=nhs_colours["LIGHT_BLUE"],
        opacity=0.2,
        annotation_position="top right",
        annotation_text='Long-term target: 40-50 virtual ward "beds" per 100,000 people',
    )


def get_timeseries_figure(data: pd.DataFrame, icb_code: str, col: str):
    df = data[data[ICB_CODE] == icb_code].copy()
    fig = go.Figure()
    fig.add_trace(get_timeseries_scatter(df, col))
    fig.update_layout(get_timeseries_layout_kwargs(icb_code, col))
    if col == CAPACITY_PER_POPULATION:
        # Annotate the long-term target for capacity per population to track progress
        fig.add_hrect(**get_capacity_per_population_hrect_kwargs())
        fig.update_layout(yaxis_range=[0, max(df[col].max() + 1, 50)])
    return fig


def get_timeseries(data: pd.DataFrame):
    return dcc.Graph(
        id=TIMESERIES,
        figure=get_timeseries_figure(data, icb_code="QT6", col=CAPACITY_PER_POPULATION),
        style={
            "width": "35vw",
            "height": "25vw",
            "display": "inline-block",
        },
    )


def get_text_div():
    return html.Div(
        children=[
            html.P(
                [
                    "This is a dashboard created by Siu Ying Wong as part of a job application. The dashboard is kept simplistic as its main purpose is for demonstrating skills in engineering ETL pipelines, building visualisations and handling healthcare data. ",
                    "The source code for constructing the pipeline and dashboard can be found on ",
                    html.A(
                        "GitHub",
                        href=config["GITHUB_URL"],
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
    )


def get_notes_div():
    return html.Div(
        children=[
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
                                href=config["GP_POPULATION_URL"],
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
                        href=config["VIRTUAL_WARDS_INFO_URL"],
                    ),
                    ".",
                ]
            ),
        ]
    )
