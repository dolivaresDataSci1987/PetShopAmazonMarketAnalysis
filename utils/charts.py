import plotly.express as px


def bar_chart(df, x, y, title, color=None, height=450):
    fig = px.bar(df, x=x, y=y, title=title, color=color)
    fig.update_layout(height=height)
    return fig


def scatter_chart(df, x, y, title, color=None, size=None, hover_data=None, height=500):
    fig = px.scatter(
        df,
        x=x,
        y=y,
        title=title,
        color=color,
        size=size,
        hover_data=hover_data
    )
    fig.update_layout(height=height)
    return fig


def histogram_chart(df, x, title, nbins=30, height=450):
    fig = px.histogram(df, x=x, nbins=nbins, title=title)
    fig.update_layout(height=height)
    return fig
