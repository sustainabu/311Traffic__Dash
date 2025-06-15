

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