import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
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


config = load_config()
boundaries = get_icb_boundaries(config)
icb_name_lookup = get_icb_name_lookup(boundaries)
map_colour_scale = [[0, "#ffffff"], [1, "#003087"]]


def get_dropdown_options(config):
    return [{"label": v, "value": k} for k, v in config["DROPDOWN_OPTIONS"].items()]


def get_map_range(df, col):
    if col == CAPACITY_PER_POPULATION:
        return [0, 60]
    return (0, df[col].max())


def get_hovertemplate(df, col):
    formatter = config["FORMATTERS"][col]
    template = "%{customdata[0]}: %{customdata[1]:" + formatter + "}"
    if col == OCCUPANCY:
        return np.select([df[SUPPRESSED] == False], [template], template + "*")
    return template


def get_yaxis_title(col):
    title = config["DROPDOWN_OPTIONS"][col].split("(")[0].strip()
    if col == CAPACITY_PER_POPULATION:
        return title.replace("registered ", "registered <br>")
    return title


def get_map(
    data: pd.DataFrame, col: str = CAPACITY_PER_POPULATION, date: datetime = None
):
    df = filter_date(data, date=date)
    fig = px.choropleth_mapbox(
        df,
        geojson=boundaries,
        locations=df[ICB_CODE],
        featureidkey="properties.ICB22CD",
        color=col,
        range_color=get_map_range(data, col),
        color_continuous_scale=map_colour_scale,
        mapbox_style="carto-positron",
        zoom=5.5,
        center=config["MAP_CENTRE"],
        hover_data=[ICB_NAME, col],
    )
    fig.update_coloraxes(colorbar_tickformat=config["FORMATTERS"][col])
    fig.update_layout(coloraxis_colorbar_title="", margin=dict(l=10, r=10, t=10, b=10))
    fig.update_traces(hovertemplate=get_hovertemplate(df, col))
    return fig


def get_time_series(data: pd.DataFrame, icb_code: str, col: str = OCCUPANCY):
    df = data[data[ICB_CODE] == icb_code].copy()
    formatter = config["FORMATTERS"][col]
    template = "%{x}: %{y:" + formatter + "}"
    if col == OCCUPANCY:
        template = np.select([df[SUPPRESSED] == False], [template], template + "*")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[DATE],
            y=df[col],
            mode="lines",
            name=col,
            line=dict(color="#005EB8", width=2),
            hovertemplate=template,
        )
    )
    fig.update_layout(
        title=icb_name_lookup[icb_code],
        xaxis_title="Date",
        xaxis_tickformat="%m/%y",
        yaxis_title=get_yaxis_title(col),
        yaxis_tickformat=formatter,
    )
    if col == CAPACITY_PER_POPULATION:
        fig.add_hrect(
            y0=40,
            y1=50,
            line_width=0,
            fillcolor="#41B6E6 ",
            opacity=0.2,
            annotation_position="top right",
            annotation_text='Long-term target: 40-50 virtual ward "beds" per 100,000 people',
        )
        fig.update_layout(yaxis_range=[0, max(df[col].max() + 1, 50)])
    return fig
