
#Load Libraries
import sys
print(sys.executable)
import dash_mantine_components as dmc
import dash
from dash import Dash, html, dcc, callback, Output, Input, dash_table, State,_dash_renderer
from datetime import date
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import requests
import folium
import io
from io import BytesIO
import base64

# Explicitly set React version; MUST BE PLACED IN ORDER
_dash_renderer._set_react_version("18.2.0")

# Load data
#df = pd.read_csv(
#    "https://raw.githubusercontent.com/sustainabu/311Traffic__Dash/main/data.csv.gz"
#)

# GitHub raw link to your parquet file
url = "https://raw.githubusercontent.com/sustainabu/311Traffic__Dash/main/311trafficQ.parquet"

# Fetch the file and load as DataFrame
response = requests.get(url)
df = pd.read_parquet(BytesIO(response.content), engine='pyarrow')

# Data type adjustments
df["dateTime"] = pd.to_datetime(df["dateTime"]).dt.date
df["index_"] = df["index_"].astype(int)
df["MinutesElapsed"] = df["MinutesElapsed"].astype(float)
update_date = date(2025, 6, 11) #Update Date

# Dropdown options
board_options = ["All"] + sorted(df["cboard_expand"].dropna().unique().astype(str))

# Request Dropdown option
request_options = sorted(df["descriptor"].dropna().unique().astype(str))

# Initialize Dash app
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=dmc.styles.ALL,
           meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])
server = app.server

app.title = "311 Traffic Enforcement Dashboard" 


# App layout
app.layout = dmc.MantineProvider(
    forceColorScheme="light",
    children=[
        html.Div([
            # Burger button with a drawer
            dmc.Group([
                dmc.Burger(id="burger-menu", opened=False,color="purple"),
                dmc.Text("2025 Queens 311 Traffic Enforcement Dashboard", size="xl")
            ], style={"alignItems": "center", "marginBottom": "20px", "backgroundColor": "#DABC94"}),

            # Drawer for navigation menu
            dmc.Drawer(
                id="drawer",
                title="Navigation Menu",
                padding="md",
                size="sm",
                children=[
                    dmc.Menu(
                        children=[
                            dmc.MenuItem("Dashboard", id="drawer-tab-1"),
                            dmc.MenuItem("About", id="drawer-tab-2"),
                        ]
                    )
                ],
                style={"backgroundColor": "#f8f9fa"},
                withCloseButton=True
            ),

            # Main Tabs for content
            dmc.Tabs(
                id="tabs",
                value="tab-1",  # Default tab to open
                children=[
                    # Tab 1 content
                    dmc.TabsPanel(
                        value="tab-1",
                        children=[
                            html.Div(
                                [
                                    html.Span("Each record is a NYC 311 Service Request handled by local law enforcement (NYPD) "),
                                    html.B(f"Latest Data: {update_date}")
                                ]
                            ),
                            html.Div(className="container", children=[
                                dmc.Text("Select Parameters", ta="center", size="lg"),
                                html.Div([
                                    # Start Date
                                    dmc.DatePickerInput(
                                        id="start-date",
                                        label="Start Date",
                                        #description="Select the start date",
                                        value=date(2025, 1, 1).isoformat(),
                                        minDate=date(2025, 1, 1).isoformat(),
                                        maxDate=update_date.isoformat(),
                                        style={"marginRight": "20px", "marginBottom": "5px"}
                                    ),
                                    # End Date
                                    dmc.DatePickerInput(
                                        id="end-date",
                                        label="End Date",
                                        #description="Select the end date",
                                        value=update_date.isoformat(),
                                        minDate=date(2025, 1, 1).isoformat(),
                                        maxDate=update_date.isoformat(),
                                        style={"marginBottom": "20px"}
                                    ),
                                ], style={"display": "flex", "flexDirection": "row", "marginBottom": "2px"}),
                                # Community Dropdown
                                html.Div([
                                    dmc.Select(
                                        id="dropdown",
                                        label="Select Community Board",
                                        placeholder="Choose an option",
                                        data=[{"label": opt, "value": opt} for opt in board_options],
                                        value="All",
                                        clearable=True,
                                        style={"width": "300px", "marginBottom": "2px"},  # General styling
                                        styles={
                                            "input": {"backgroundColor": "#f0f8ff"},  # Background color for the input box
                                            "dropdown": {"backgroundColor": "#d1ffbd"},  # Background color for the dropdown menu
                                            "item": {"color": "#000", "padding": "8px"},  # Styling for dropdown items
                                            "hover": {"backgroundColor": "#cceeff"}  # Hover effect for dropdown items
                                        }
                                    ),                                
                                ]),
                                # Request Dropdown
                                html.Div([
                                    dmc.Select(
                                        id="violation",
                                        label="Select Violation",
                                        placeholder="Choose an option",
                                        data=[{"label": opt, "value": opt} for opt in request_options],
                                        value="Blocked Sidewalk",
                                        clearable=True,
                                        style={"width": "300px", "marginBottom": "2px"},  # General styling
                                        styles={
                                            "input": {"backgroundColor": "#f0f8ff"},  # Background color for the input box
                                            "dropdown": {"backgroundColor": "#d1ffbd"},  # Background color for the dropdown menu
                                            "item": {"color": "#000", "padding": "8px"},  # Styling for dropdown items
                                            "hover": {"backgroundColor": "#cceeff"}  # Hover effect for dropdown items
                                        }
                                    ),                                
                                ])
                            ]),
                            #Reporting
                            html.Div(className="container", children=[
                                dcc.Markdown("### How does NYPD respond?", style={'textAlign': 'center'}),
                                dcc.Markdown("**Note:** No specific action or reason is given for Action or No-Action category. A 'Summon' is similar to a fined ticket"),
                                dcc.Graph(id="pie"),
                            ]), 
                            html.Div(className="container", children=[
                                dcc.Markdown("### What is NYPD Response Time?", style={'textAlign': 'center'}),
                                dcc.Markdown("**Note:** According to investigative studies, response times less than 5 mins is suspicious behavior."),
                                html.Div([
                                    dcc.RadioItems(
                                        id="radio1",
                                        options=[
                                            {"label": "Summary", "value": "stat"},
                                            {"label": "Time Distribution", "value": "dist"},
                                        ],
                                        value="stat",
                                        inline=True,
                                        className="dash-radioitems",
                                    ),
                                    dcc.Graph(
                                        id="resolution_bar",
                                        config={
                                            "scrollZoom": False,      # Disable zoom with scrolling
                                            "doubleClick": "reset",  # Reset the plot on double-click
                                            "displayModeBar": False,  # Enable the mode bar for other features
                                            "staticPlot": True ,
                                        }),
                                ]),
                            ]),
                            # History Graph
                            html.Div(className="container", children=[
                                dcc.Markdown("### What are the trends?", style={'textAlign': 'center'}),
                                html.Div([
                                    dcc.RadioItems(
                                        id="radio3",
                                        options=[
                                            {"label": "Requests", "value": "request"},
                                            {"label": "InAction-Rate", "value": "inaction"},
                                            {"label": "Hourly Requests", "value": "hour"},
                                        ],
                                        value="request",
                                        inline=True,
                                        className="dash-radioitems",
                                    ),
                                    dcc.Graph(
                                        id="history",
                                        config={
                                            "scrollZoom": False,      # Disable zoom with scrolling
                                            "doubleClick": "reset",  # Reset the plot on double-click
                                            "displayModeBar": True,  # Enable the mode bar for other features
                                            "staticPlot": True,
                                            }
                                    ),
                                ]),
                            ]),
                            #Interactive Map
                            html.Div(className="container", children=[
                                dcc.Markdown("### Where are the requests being made? (Click Hotspot!)", style={'textAlign': 'center'}),
                                # Slider
                                html.H4("Select minimum count to display"),
                                dcc.Slider(
                                    id="slider",
                                    min=1,
                                    max=10,
                                    step=1,
                                    marks={
                                        1: "1",2: "2",3: "3",4: "4",5: "5",
                                        6: "6",7: "7",8: "8",9: "9",10: "10",
                                    },
                                    value=3,
                                    className="dash-slider",
                                ),
                                html.Div([
                                    dcc.RadioItems(
                                        id="radio4",
                                        options=[
                                            {"label": "InAction-Rate", "value": "inaction"},
                                            {"label": "Response Time", "value": "time"},
                                        ],
                                        value="inaction",
                                        inline=True,
                                        className="dash-radioitems",
                                    ),
                                    html.Div([
                                        html.Button("Toggle Legend", id="legend-button", style={'marginTop': '10px'}),
                                        html.Div(
                                            id="legend-info",
                                            style={
                                                'display': 'block',  # Hidden by default
                                                'backgroundColor': 'white',
                                                'border': '1px solid black',
                                                'padding': '10px',
                                                'borderRadius': '5px',
                                                'width': '300px',
                                                'margin': '10px auto',
                                                'textAlign': 'left'
                                            }
                                        )
                                    ], style={'textAlign': 'center'}),
                                    html.Iframe(id='folium-map', width='100%', height='400px')
                                ]),
                            ]),
                            # 311 Data Table
                            html.Div(className="container", children=[
                                dcc.Markdown("### Latest 311 Service Requests", style={'textAlign': 'center'}),

                                # Data Table
                                dash_table.DataTable(
                                    id="recent-table",
                                    columns=[
                                        {"name": i, "id": i, "deletable": False, "selectable": True} for i in 
                                        ['Date', 'Time', 'Address', 'Precinct', 'Resolution', 'Response_Mins', 'Resolution_Full']
                                    ],
                                    style_table={
                                        'overflowX': 'auto', 
                                        'maxWidth': '100%',
                                    },
                                    style_header={
                                        'backgroundColor': '#B0E0E6',
                                        'fontWeight': 'bold',
                                        'border': '1px solid black',
                                    },
                                    style_data={
                                        'border': '1px solid black',
                                        'whiteSpace': 'normal',
                                        'height': 'auto',  # Allow row wrapping for long text
                                    },
                                    style_data_conditional=[
                                        {'if': {'filter_query': '{Resolution} = "Late"'}, 'backgroundColor': '#ffb5c0'},
                                        {'if': {'filter_query': '{Resolution} = "Action"'}, 'backgroundColor': '#D5F5E3'},
                                        {'if': {'filter_query': '{Resolution} = "No-Action"'}, 'backgroundColor': '#ffdbbb'},
                                        {'if': {'filter_query': '{Resolution} = "Summon_Arrest"'}, 'backgroundColor': '#ADD8E6'}
                                    ],
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '5px',
                                        'minWidth': '80px',
                                        'maxWidth': '200px',
                                        'overflow': 'hidden',
                                        'textOverflow': 'ellipsis',
                                    },
                                    page_size=10,
                                    sort_action='native',
                                    fixed_rows={'headers': False},  # Disable fixed headers for mobile scrolling
                                ),
                            ], style={'width': '80%', 'margin': 'auto'})
                        ],
                    ),
                    # Tab 2 content
                    dmc.TabsPanel(
                        value="tab-2",
                        children=[
                            html.Div([
                                dcc.Markdown('''
                                        ### Data
                                        ---
                                        * The data is retrieved from [311 Service Requests]("https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9/about_data/") via NYC Open Data.
                                        * Each record is a **reported** violation.
                                        * NYPD response time is the difference between 311 opening and closing time.
                                        * Dashboard Source Code is accessible on [Github](https://github.com/sustainabu/OpenDataNYC).
                                        ### Purpose
                                        --- 
                                        * This is a community TOOL to monitor and measure progress.
                                        * Evaluate police responses 
                                             
                                        ### About Me
                                        ---
                                        * My name is Abu Nayeem. I'm a transportation advocate and Jamaica, Queens resident.
                                        * I'm trained as an economist (MS Economics in UC Berkeley) and self-learned programmer.
                                        * Contact Me (anayeem1@gmail.com)
                                    '''
                                    )
                            ])
                        ]
                    ),
                ]
            ),
        ])
    ]
)



#C1
# Callback to update plot based on input
@callback(
    Output("pie", "figure"),
    [Input('start-date', 'value'), 
     Input('end-date', 'value'), 
     Input("dropdown", "value"),
     Input("violation", "value")
     ]
)
def update_graph(start_date, end_date, board, violation):
    # Ensure start_date and end_date are valid
    if start_date is None:
        start_date = date(2025, 1, 1)  # Default to the minimum date in the dataset
    else:
        start_date = pd.to_datetime(start_date).date()

    if end_date is None:
        end_date = date(2025, 6, 11)  # Default to the maximum date in the dataset
    else:
        end_date = pd.to_datetime(end_date).date()

    # Apply all filters: community board and date range
    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df["descriptor"] == violation]
    if board != "All":
        filtered_df = filtered_df[filtered_df["cboard_expand"] == board]

    filtered_df = filtered_df[
        (filtered_df["dateTime"] >= start_date) &
        (filtered_df["dateTime"] <= end_date)
    ]


    # Shortcut Renaming
    def boardT():
        if board != "All":
            return board.split(':')[0]
        else:
            return "All"
        
    # Define specific colors for each resolution
    color_map = {
        "Late": "#FF474C",
        "No-Action": "#FFA53F",
        "Action": "lightgreen",
        "Summon_Arrest": "#63e5ff"  # Adjust as per your categories
    }

    # Check if filtered_df is empty
    if filtered_df.empty:
        # Handle case where no data matches the filters
        fig = px.pie(
            names=["No Data"],
            values=[1],
            title="No data available for the selected parameters."
        )
    else:
        # Group data for pie chart
        grouped_data = (
            filtered_df.groupby("resolution")["index_"]
            .sum()
            .reset_index()
            .rename(columns={"index_": "Count"})
        )

    # Create pie chart
    fig = px.pie(
        grouped_data,
        names="resolution",
        values="Count",
        title=f"Total Resolutions for {boardT()}: {filtered_df['index_'].sum()}",
        color="resolution",
        color_discrete_map=color_map
    )

    # Adjust the layout for the legend
    fig.update_layout(
        legend=dict(
            orientation='h',  # Horizontal legend
            yanchor='top',
            y=-0.15,  # Position below the chart
            xanchor='center',
            x=0.5  # Centered horizontally
        ),
        title_x=0.5,
        margin=dict(t=50, b=100)  # Adjust margins to make space for the legend
    )

    return fig

#C2 Resolution
@callback(
    Output("resolution_bar", "figure"),
    [Input('start-date', 'value'), 
     Input('end-date', 'value'), 
     Input("dropdown", "value"),
     Input("violation", "value"),
     Input("radio1", "value")
     ]
)
def bar_graph(start_date, end_date, board, violation, choice):
    # Ensure start_date and end_date are valid
    if start_date is None:
        start_date = date(2025, 1, 1)  # Default to the minimum date in the dataset
    else:
        start_date = pd.to_datetime(start_date).date()

    if end_date is None:
        end_date = date(2025, 6, 11)  # Default to the maximum date in the dataset
    else:
        end_date = pd.to_datetime(end_date).date()

    # Apply all filters: community board and date range
    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df["descriptor"] == violation]
    if board != "All":
        filtered_df = filtered_df[filtered_df["cboard_expand"] == board]

    filtered_df = filtered_df[
        (filtered_df["dateTime"] >= start_date) &
        (filtered_df["dateTime"] <= end_date)
    ]

    # Shortcut Renaming
    def boardT():
        if board != "All":
            return board.split(':')[0]
        else:
            return "All"
    
    # Predefined resolution categories and elapsed minute bins    
    all_resolutions = ["Action", "Late", "No-Action", "Summon_Arrest"]  # Add all possible resolution values here
    elapsed_bins = ["min0->5", "min5->30", "min30->60", "min60->360", "min360+"]  # Define all bins

    # Step 1: Aggregate Total, Median, and Mean
    cols_total = ["resolution", "index_"]
    cols_elapsed = ["resolution", "MinutesElapsed"]

    # Total count with predefined categories
    df_total = filtered_df[cols_total].groupby("resolution", observed=False).sum()
    df_total = df_total.reindex(all_resolutions, fill_value=0).reset_index()
    df_total.columns = ["resolution", "Total"]

    # Median of MinutesElapsed
    df_median = filtered_df[cols_elapsed].groupby("resolution", observed=False).median()
    df_median = df_median.reindex(all_resolutions, fill_value=0).reset_index()
    df_median = df_median.round(2)
    df_median.columns = ["resolution", "Median_Minutes"]

    # Mean of MinutesElapsed
    df_mean = filtered_df[cols_elapsed].groupby("resolution", observed=False).mean()
    df_mean = df_mean.reindex(all_resolutions, fill_value=0).reset_index()
    df_mean = df_mean.round(2)
    df_mean.columns = ["resolution", "Mean_Minutes"]

    # Merge Total, Median, and Mean
    merged_df = pd.merge(df_total, df_median, on="resolution", how="left")
    merged_df = pd.merge(merged_df, df_mean, on="resolution", how="left")

    # Step 2: Create Binned Count with all bins included
    bins_cols = ["resolution", "ElapsedMinuteBin", "index_"]

    # Group and pivot with predefined bins
    df_bins = filtered_df[bins_cols].groupby(["resolution", "ElapsedMinuteBin"]).sum().reset_index()
    df_bins["ElapsedMinuteBin"] = pd.Categorical(df_bins["ElapsedMinuteBin"], categories=elapsed_bins, ordered=True)
    df_bins = df_bins.pivot_table(index="resolution", columns="ElapsedMinuteBin", values="index_", fill_value=0, observed=False).reset_index()

    # Ensure all bins are included
    df_bins = df_bins.reindex(columns=["resolution"] + elapsed_bins, fill_value=0)

    # Merge binned data with aggregated data
    result_df = pd.merge(merged_df, df_bins, on="resolution", how="left")
    result_df.columns = ["Police_resolution", "Total", "Median_Mins", "Mean_Mins"] + elapsed_bins
    new_order = [1,2,0,3]
    result_df = result_df.reindex(new_order)

    # Step 3: Add Citywide Totals
    city_data = [
        "All",
        result_df["Total"].sum(),
        round(filtered_df["MinutesElapsed"].median(), 2),
        round(filtered_df["MinutesElapsed"].mean(), 2),
        *[result_df[bin].sum() for bin in elapsed_bins],
    ]

    citywide_df = pd.DataFrame([city_data], columns=result_df.columns)

    # Combine aggregated data with citywide totals
    final_df = pd.concat([result_df, citywide_df], ignore_index=True)

    # Step 4: Calculate percentages for binned columns
    for col in elapsed_bins:
        final_df[col] = (
            final_df[col]
            .div(final_df["Total"])
            .fillna(0)
            .mul(100)
            .round(1)  # Round to one decimal place
            #.apply(lambda x: f"{x:.1f}%")
        )
    
    fig1 = go.Figure(data=[
    go.Bar(name='Median', x=final_df['Police_resolution'], y=final_df['Median_Mins']),
    go.Bar(name='Mean', x=final_df['Police_resolution'], y=final_df['Mean_Mins'])
    ])

    fig1.update_layout(
        barmode='group',
        title=f"Response Time (Minutes) for {boardT()}",
        title_x=0.5,
        legend=dict(
            orientation='h',  # Horizontal legend
            yanchor='bottom',
            y=-0.25,  # Position below the chart
            xanchor='center',
            x=0.5,  # Centered horizontally
            traceorder='normal'
        )
    )
    
    ## horizontal graph
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        y=final_df["Police_resolution"],
        x=final_df['min0->5'],
        name='Min_0->5',
        orientation='h',
        #marker=dict(color='#19A0AA'),
        #text=male_percentages,
        #textfont_size=14,
        textposition='inside',  # Position the text inside the bars
    ))

    fig2.add_trace(go.Bar(
        y=final_df["Police_resolution"],
        x=final_df['min5->30'],
        name='Min_5->30',
        orientation='h',
        textposition='inside',  # Position the text inside the bars
    ))

    fig2.add_trace(go.Bar(
        y=final_df["Police_resolution"],
        x=final_df['min30->60'],
        name='Min_30->60',
        orientation='h',
        textposition='inside',  # Position the text inside the bars
    ))
    fig2.add_trace(go.Bar(
        y=final_df["Police_resolution"],
        x=final_df['min60->360'],
        name='Min_60->360',
        orientation='h',
        textposition='inside',  # Position the text inside the bars
    ))
    fig2.add_trace(go.Bar(
        y=final_df["Police_resolution"],
        x=final_df['min360+'],
        name='Min_360+',
        orientation='h',
        textposition='inside',  # Position the text inside the bars
    ))

    quarters = ['All','Summon_Arrest','Action','No-Action','Late']

    fig2.update_layout(
        xaxis=dict(ticksuffix='%'),
        yaxis=dict(categoryorder='array',
                   categoryarray=quarters,
                   tickangle=-90,
                    title=dict(
                        text='',  # Set your desired label text
                        standoff=30,          # Space between label and axis
                        font=dict(size=12),   # Customize font size
                    ),
                ),
        barmode='stack',
        template='plotly_white',
        legend=dict(
            orientation='h',  # Horizontal legend
            yanchor='bottom',
            y=-0.25,  # Position below the chart
            xanchor='center',
            x=0.5,  # Centered horizontally
            traceorder='normal'
        ),
        margin = dict(l=10, r=10, t=10, b=10)
    )
    
    #Select by Radio Button
    return fig2 if choice != "stat" else fig1

#c4 History    
@callback(
    Output("history", "figure"),
    [Input('start-date', 'date'), 
     Input('end-date', 'date'), 
     Input("dropdown", "value"),
     Input("radio3", "value"),
     Input("violation", "value")
     ]
)
def history_graph(start_date, end_date, board, choice, violation):
    # Ensure start_date and end_date are valid
    if start_date is None:
        start_date = date(2025, 1, 1)  # Default to the minimum date in the dataset
    else:
        start_date = pd.to_datetime(start_date).date()

    if end_date is None:
        end_date = date(2025, 6, 11)  # Default to the maximum date in the dataset
    else:
        end_date = pd.to_datetime(end_date).date()

    # Apply all filters: community board and date range
    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df["descriptor"] == violation]
    if board != "All":
        filtered_df = filtered_df[filtered_df["cboard_expand"] == board]

    filtered_df = filtered_df[
        (filtered_df["dateTime"] >= start_date) &
        (filtered_df["dateTime"] <= end_date)
    ]

    # Shortcut Renaming
    def boardT():
        if board != "All":
            return board.split(':')[0]
        else:
            return "All"

    custom_palette = [ "#ff7f0e","#1f77b4", "#2ca02c", "#d62728", "#9467bd"]
    current_year = filtered_df.Year.max() 

    #filtered_df["Inaction"]= filtered_df["Late"] + filtered_df["No-Action"]
    

    # Get Total by Precinct
    p=['WeekBin', 'Year','Late', 'No-Action','index_']
    df1=filtered_df[p].groupby(['WeekBin','Year']).sum().reset_index()
    df1.columns=['WeekBin','Year','Late','No-Action','total']
    df1['InAction_Rate']= round((df1['Late'] +df1['No-Action']) / df1['total'],2)



    # Choose plot data based on radio choice
    if choice == 'request':
        bg = filtered_df.groupby(['WeekBin', 'Year'])['index_'].sum().unstack()
        traces = []
        nl = '<br>'  # HTML line break for Plotly titles
        for year in bg.columns:
            linestyle = 'solid' if year == current_year else 'dash'
            traces.append(go.Scatter(
                x=bg.index, y=bg[year],
                mode='lines',
                name=str(year),
                line=dict(dash=linestyle, color=custom_palette[year % len(custom_palette)])
            ))
        title = f"<b>Requests History for {boardT()}{nl}from {start_date} to {end_date}</b>"

        # Create Plotly figure
        figure = go.Figure(data=traces)
        figure.update_layout(
            title=dict(
                text=title,
                font=dict(size=14),  # Adjust font size
                x=0.5,               # Center align the title
                xanchor='center',
                yanchor='top',
            ),
            xaxis_title='WeekBin (0 = beginning of year)',
            yaxis_title='',
            legend_title='',
            template='plotly_white',
            legend=dict(
                orientation='h',  # Horizontal legend
                yanchor='bottom',
                y=-0.25,  # Position below the chart
                xanchor='center',
                x=0.5,  # Centered horizontally
                traceorder='normal'
            ),
            margin=dict(l=10, r=10, t=80, b=10)  # Add padding to the top with `t`
        )

    elif choice == 'hour':
        nl = '<br>'  # HTML line break for Plotly

        # Ensure 'Hour' column exists
        filtered_df['Hour'] = pd.to_datetime(filtered_df['dateTimeO']).dt.hour

        # Group by Hour of Day (0–23), fill in missing hours with 0
        counts = filtered_df.groupby('Hour').size().reindex(range(24), fill_value=0)

        # Use Bar chart instead of Scatter
        traces = [go.Bar(
            x=counts.index,  # 0–23 hours
            y=counts.values,
            name='Hourly Requests',
            marker_color=custom_palette[0]  # Choose color
        )]

        # Chart title
        title = f"<b>Hourly Requests for {boardT()}{nl}from {start_date} to {end_date}</b>"

        # Create Plotly figure
        figure = go.Figure(data=traces)
        figure.update_layout(
            title=dict(
                text=title,
                font=dict(size=14),
                x=0.5,
                xanchor='center',
                yanchor='top',
            ),
            xaxis=dict(
                title='Hour of Day (0–23)',
                dtick=1  # Show all hours on x-axis
            ),
            yaxis=dict(
                title='Number of Requests'
            ),
            legend_title='',
            template='plotly_white',
            margin=dict(l=10, r=10, t=80, b=10)
        )

    else:
        traces = []
        nl = '<br>'  # HTML line break for Plotly titles
        for year in df1['Year'].unique():
            df_year = df1[df1['Year'] == year]
            linestyle = 'solid' if year == current_year else 'dash'
            traces.append(go.Scatter(
                x=df_year['WeekBin'], y=df_year['InAction_Rate'],
                mode='lines',
                name=str(year),
                line=dict(dash=linestyle, color=custom_palette[year % len(custom_palette)])
            ))
        title = f"<b>InAction Rate History for {boardT()}{nl} from {start_date} to {end_date}</b>"

        # Create Plotly figure
        figure = go.Figure(data=traces)
        figure.update_layout(
            title=dict(
                text=title,
                font=dict(size=14),  # Adjust font size
                x=0.5,               # Center align the title
                xanchor='center',
                yanchor='top',
            ),
            xaxis_title='WeekBin (0 = beginning of year)',
            yaxis_title='',
            legend_title='',
            legend=dict(
                orientation='h',  # Horizontal legend
                yanchor='bottom',
                y=-0.25,  # Position below the chart
                xanchor='center',
                x=0.5,  # Centered horizontally
                traceorder='normal'
            ),
            template='plotly_white',
            margin=dict(l=10, r=10, t=80, b=10)  # Add padding to the top with `t`
            
        )
    return figure



#Callback for Folium Map
@callback(
    Output("folium-map", "srcDoc"),
    [Input('start-date', 'value'), 
     Input('end-date', 'value'), 
     Input("dropdown", "value"),
     Input("slider", "value"),
     Input("radio4", "value"),
     Input("violation", "value")
     ]
)
def folium_map(start_date, end_date, board, slide,choice,violation):
    # Ensure start_date and end_date are valid
    if start_date is None:
        start_date = date(2025, 1, 1)  # Default to the minimum date in the dataset
    else:
        start_date = pd.to_datetime(start_date).date()

    if end_date is None:
        end_date = date(2025, 6, 11)  # Default to the maximum date in the dataset
    else:
        end_date = pd.to_datetime(end_date).date()

    # Apply all filters: community board and date range
    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df["descriptor"] == violation]
    if board != "All":
        filtered_df = filtered_df[filtered_df["cboard_expand"] == board]

    filtered_df = filtered_df[
        (filtered_df["dateTime"] >= start_date) &
        (filtered_df["dateTime"] <= end_date)
    ]


    # Calculate midpoint of latitude and longitude
    latitude_mid = (filtered_df.latitude.max() + filtered_df.latitude.min()) / 2
    longitude_mid = (filtered_df.longitude.max() + filtered_df.longitude.min()) / 2
    
    # Set default map location and zoom based on input
    if board == "All":
        zoom = 11.25
        map_location = [40.7128, -74.0060]  # Default NYC location
    else:
        zoom = 12.5
        map_location = [latitude_mid, longitude_mid]

    # Initialize folium map
    nyc_map = folium.Map(location=map_location, zoom_start=zoom, tiles="CartoDB positron", height='100%', control_scale=True)


    # Get Total by UAddress
    p=['incident_address','cboard', 'precinct','UAdd','longitude','latitude','index_']
    df1=filtered_df[p].groupby(['incident_address','cboard','precinct','UAdd','longitude','latitude']).sum().reset_index()
    df1.columns=['Address','cboard','precinct','UAdd','longitude','latitude','total']

    # Filter data based on input
    df1 = df1[df1['total'] > slide]

    # Get Elapsed Min Binned Count
    p2=['UAdd','ElapsedMinuteBin','index_']
    pv=filtered_df[p2].groupby(['UAdd','ElapsedMinuteBin']).sum().reset_index()
    pv2=pd.pivot_table(pv,index='UAdd', columns='ElapsedMinuteBin', values=['index_']).reset_index().fillna(0)

    #CHECK ORDER OF COLUMNS- Alphabetical
    pv2.columns=['UAdd',"min0->5", "min30->60", "min360+", "min5->30","min60->360"]  
    c1= pd.merge(df1, pv2, on='UAdd', how='right')

    # Get Resolution Count
    p2=['UAdd','resolution','index_']
    cv=filtered_df[p2].groupby(['UAdd','resolution']).sum().reset_index()
    cv2=pd.pivot_table(cv,index='UAdd', columns='resolution', values=['index_']).reset_index().fillna(0)

    #CHECK ORDER OF COLUMNS- Alphabetical
    cv2.columns=['UAdd','Action','Late','No-Action','Summon_Arrest']
    B= pd.merge(c1, cv2, on='UAdd', how='right')

    # to get median
    p2=['UAdd','MinutesElapsed']
    C=filtered_df[p2].groupby(['UAdd']).median().reset_index()
    C.columns= ['UAdd','Median_Minutes']  
    C.Median_Minutes=round(C.Median_Minutes,2)
    D= pd.merge(B, C, on='UAdd', how='right') 
    # to get mean
    E=filtered_df[p2].groupby(['UAdd']).mean().reset_index()
    E.columns= ['UAdd','Mean_Minutes']  
    E.Mean_Minutes=round(E.Mean_Minutes,2)
    F= pd.merge(D, E, on='UAdd', how='right') 

    F['InAction_Rate']= round((F['Late'] +F['No-Action']) / F['total'],2)

   # B17= F.query('total>50').sort_values('Median_Minutes', ascending=False)


    def Resp(x):
        if x<=0.5:
            return "Low" #5 mins or less
        elif x>0.5 and x<=0.75:
            return "Medium"
        else:
            return "High" # greater than 360 mins
            
    F = F.copy()
    F['Inaction_rank'] = F['InAction_Rate'].apply(Resp)

    def Resp(x):
        if x<=30:
            return "Low" #5 mins or less
        elif x>30 and x<=60:
            return "Medium"
        else:
            return "High" # greater than 360 mins
        
    F = F.copy()
    F['Time_rank'] = F['Median_Minutes'].apply(Resp)


    F.dropna(subset=['longitude'], inplace=True)
    F.dropna(subset=['latitude'], inplace=True)

    if choice == 'inaction':
        categories = [
            ("Inaction_rank == 'Low'", "#007849"),  # Green
            ("Inaction_rank == 'Medium'", "#FFB52E"),  # Orange
            ("Inaction_rank == 'High'", "#E32227")  # Red
        ]
        # Add markers to the map
        for query, color in categories:
            category_df = F.query(query)
            for _, row in category_df.iterrows():
                popup_text = (
                    f"Address: {row['Address']}<br>"
                    f"CBoard: {row['cboard']}<br>"
                    f"Total: {row['total']}<br>"
                    f"InAction Rate: {row['InAction_Rate']}<br>"
                    f"Late#: {row['Late']}<br>"
                    f"No-Action#: {row['No-Action']}<br>"
                    f"Action#: {row['Action']}<br>"
                    f"Summon_Arrest#: {row['Summon_Arrest']}"
                )
                folium.CircleMarker(
                    location=(row["latitude"], row["longitude"]),
                    radius=row['total'] / 10 + 5,
                    color=color,
                    popup = folium.Popup(popup_text, max_width=300),
                    fill=True
                ).add_to(nyc_map)
    else:
        # Define marker categories
        categories = [
            ("Time_rank == 'Low'", "#007849"),  # Green
            ("Time_rank == 'Medium'", "#FFB52E"),  # Orange
            ("Time_rank == 'High'", "#E32227")  # Red
        ]

        # Add markers to the map
        for query, color in categories:
            category_df = F.query(query)
            for _, row in category_df.iterrows():
                popup_text = (
                    f"Address: {row['Address']}<br>"
                    f"CBoard: {row['cboard']}<br>"
                    f"Total: {row['total']}<br>"
                    f"MedianMin: {row['Median_Minutes']}<br>"
                    f"MeanMin: {row['Mean_Minutes']}<br>"
                    f"Min_0->5: {row['min0->5']}<br>"
                    f"Min_5->30: {row['min5->30']}<br>"
                    f"Min_30->60: {row['min30->60']}<br>"
                    f"Min_60->360: {row['min60->360']}<br>"
                    f"Min_360+: {row['min360+']}<br>"
                )
                folium.CircleMarker(
                    location=(row["latitude"], row["longitude"]),
                    radius=row['total'] / 15 + 3,
                    color=color,
                    popup = folium.Popup(popup_text, max_width=300),
                    fill=True
                ).add_to(nyc_map)    
    
    return nyc_map._repr_html_()

#c5 Data Table
@app.callback(
    Output("recent-table", "data"),
    [Input('start-date', 'value'), 
     Input('end-date', 'value'), 
     Input("dropdown", "value"),
     Input("violation", "value")
     ]
)
def recent_table(start_date, end_date, board, violation):
    # Ensure start_date and end_date are valid
    if start_date is None:
        start_date = date(2025, 1, 1)  # Default to the minimum date in the dataset
    else:
        start_date = pd.to_datetime(start_date).date()

    if end_date is None:
        end_date = date(2025, 6, 11)  # Default to the maximum date in the dataset
    else:
        end_date = pd.to_datetime(end_date).date()

    # Apply all filters: community board and date range
    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df["descriptor"] == violation]
    if board != "All":
        filtered_df = filtered_df[filtered_df["cboard_expand"] == board]

    filtered_df = filtered_df[
        (filtered_df["dateTime"] >= start_date) &
        (filtered_df["dateTime"] <= end_date)
    ]

    # Select relevant columns for the table
    recent_df = filtered_df[['dateTime', 'Time', 'incident_address','precinct','resolution', 'MinutesElapsed', 'resolution_description']]
    recent_df.columns = ['Date', 'Time','Address','Precinct', 'Resolution', 'Response_Mins', 'Resolution_Full']
    
    return recent_df.to_dict('records')



### Legend Items
### Clickable Legend
# Callback to toggle legend visibility
@app.callback(
    Output("legend-info", "style"),
    Input("legend-button", "n_clicks"),
    State("legend-info", "style")
)
def toggle_legend_visibility(n_clicks, current_style):
    if n_clicks is None:
        # If no clicks, return the default visible style (already set in layout)
        return current_style
    
    if n_clicks and current_style["display"] == "none":
        return {"display": "block", "backgroundColor": "white", "border": "1px solid black", "padding": "10px"}
    return {"display": "none"}


# Callback to populate legend content
@app.callback(
    Output("legend-info", "children"),
    Input("radio4", "value")
)
def update_legend_content(choice):
    # Legend content based on selection
    if choice == 'inaction':
        legend_items = [
            html.Div([
                html.Span("", style={
                    "display": "inline-block",
                    "width": "15px",
                    "height": "15px",
                    "backgroundColor": "#007849",  # Color for 'Low'
                    "marginRight": "10px"
                }),
                html.Span("Low: ", style={"fontWeight": "bold"}),
                html.Span("Inaction < 0.5")
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Span("", style={
                    "display": "inline-block",
                    "width": "15px",
                    "height": "15px",
                    "backgroundColor": "#FFB52E",  # Color for 'Medium'
                    "marginRight": "10px"
                }),
                html.Span("Medium: ", style={"fontWeight": "bold"}),
                html.Span("Inaction 0.5 to 0.75")
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Span("", style={
                    "display": "inline-block",
                    "width": "15px",
                    "height": "15px",
                    "backgroundColor": "#E32227",  # Color for 'High'
                    "marginRight": "10px"
                }),
                html.Span("High: ", style={"fontWeight": "bold"}),
                html.Span("Inaction > 0.75")
            ])
        ]
        return legend_items
    else:
        legend_items = [
            html.Div([
                html.Span("", style={
                    "display": "inline-block",
                    "width": "15px",
                    "height": "15px",
                    "backgroundColor": "#007849",  # Color for 'Low'
                    "marginRight": "10px"
                }),
                html.Span("Low: ", style={"fontWeight": "bold"}),
                html.Span("Median <= 30 mins")
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Span("", style={
                    "display": "inline-block",
                    "width": "15px",
                    "height": "15px",
                    "backgroundColor": "#FFB52E",  # Color for 'Medium'
                    "marginRight": "10px"
                }),
                html.Span("Medium: ", style={"fontWeight": "bold"}),
                html.Span("Median 30 to 60 mins")
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Span("", style={
                    "display": "inline-block",
                    "width": "15px",
                    "height": "15px",
                    "backgroundColor": "#E32227",  # Color for 'High'
                    "marginRight": "10px"
                }),
                html.Span("High: ", style={"fontWeight": "bold"}),
                html.Span("Median > 60 mins")
            ])
        ]
        return legend_items      

#Formmatting of drawers and Tabs
# Combined callback for drawer and tabs
@app.callback(
    [Output("drawer", "opened"), Output("tabs", "value")],
    [Input("burger-menu", "opened"),
     Input("drawer-tab-1", "n_clicks"),
     Input("drawer-tab-2", "n_clicks")],
    prevent_initial_call=True
)
def handle_drawer_and_tabs(opened, tab1_clicks, tab2_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, "tab-1"  # Default behavior
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Toggle drawer or switch tabs based on input
    if triggered_id == "burger-menu":
        return opened, dash.no_update  # Toggle drawer
    elif triggered_id == "drawer-tab-1":
        return False, "tab-1"  # Close drawer and switch to Tab 1
    elif triggered_id == "drawer-tab-2":
        return False, "tab-2"  # Close drawer and switch to Tab 2
    
    return False, "tab-1"  # Fallback behavior

# Callback to highlight the selected menu item
@app.callback(
    [Output("drawer-tab-1", "style"),
     Output("drawer-tab-2", "style")],
    [Input("drawer-tab-1", "n_clicks"),
     Input("drawer-tab-2", "n_clicks")],
    prevent_initial_call=True
)
def highlight_menu_item(tab1_clicks, tab2_clicks):
    ctx = dash.callback_context
    default_style = {"cursor": "pointer", "backgroundColor": "transparent", "padding": "10px"}
    highlight_style = {"cursor": "pointer", "backgroundColor": "#007bff", "color": "white", "padding": "10px"}
    
    if not ctx.triggered:
        return default_style, default_style
    
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id == "drawer-tab-1":
        return highlight_style, default_style
    elif triggered_id == "drawer-tab-2":
        return default_style, highlight_style
    
    return default_style, default_style  # Fallback



# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
