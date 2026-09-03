import dash
from dash import Dash
from dash import html,dash_table,dcc
from dash.dependencies import Input,Output,State
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import os
from pathlib import Path



class Dashboard:
    def __init__(self,server,engine):

        self.app = Dash(
            __name__,
            server=server,
            routes_pathname_prefix='/dashboard/',
            assets_folder=str(Path(__file__).parent / 'assets')
        )
        self.engine = engine

        webscrapping_path = Path.cwd().parent / "1 - Web Scrapping"

        # Load worldcup and team names from text files
        name_of_all_worldcups_path = webscrapping_path / "name_of_all_worldcups.txt"
        a_file = open(name_of_all_worldcups_path, "r", newline='')
        raw_worldcups = a_file.read()
        worldcups = raw_worldcups.splitlines(False)
        a_file.close()
        self.worldcups = worldcups
        self.worldcups_year = [int(worldcup.split()[0]) for worldcup in worldcups]
        
        # Load team names from text file
        name_of_all_teams_path = webscrapping_path / "name_of_all_teams.txt"
        b_file = open(name_of_all_teams_path ,"r",newline = '')
        raw_teams = b_file.read()
        name_of_all_teams = raw_teams.splitlines(False)
        b_file.close()
        self.name_of_all_teams = name_of_all_teams

        year_wcup_dic = {}
        for year,worldcup in zip(self.worldcups_year,worldcups):
            year_wcup_dic[year] = worldcup
        self.year_wcup_dic = year_wcup_dic

        slider_marks = {}
        for year in self.worldcups_year:
            slider_marks[year] = {'label': '{}'.format(year),'style': {'color':'black'}}
        self.slider_marks = slider_marks


        # New version without classes
        df_quarter = pd.read_csv('wcup_has_teams.csv', encoding='utf-8-sig',sep =';',index_col = 3)
        year_wcup = int(worldcups[0].split(' ')[0])
        filtro_ano = (df_quarter['YEAR'] == year_wcup)

        # Take all teams that played in the selected year
        team_names = df_quarter[filtro_ano]['TEAM'].unique()

        # Take the quartiles of a specific team
        default_team = team_names[0] if len(team_names) > 0 else 'Argentina'
        filtro_time = (df_quarter['TEAM'] == default_team)
        df_quarter = df_quarter[['N_PLAYERS','FIRST_QUARTILE','SECOND_QUARTILE','THIRD_QUARTILE','FORTH_QUARTILE']]
        df_quarter = df_quarter[np.logical_and(filtro_ano,filtro_time)].T
        df_quarter.rename({'N_PLAYERS':'Total','FIRST_QUARTILE':'First Quarter','SECOND_QUARTILE':'Second Quarter','THIRD_QUARTILE':'Third Quarter','FORTH_QUARTILE':'Fourth Quarter'},inplace = True)
        displayed_team = df_quarter
        '''
        default_worldcup = WorldcupQuarters('2022 Qatar')
        displayed_team = default_worldcup.get_quarters_from_team('Argentina').df()
        displayed_team = displayed_team.reset_index()
        displayed_team.columns = ['','Frequence', 'Percentage(%)']
        team_names = default_worldcup.get_teams()
        
        
        '''
        self.team_names = team_names
        self.displayed_team = displayed_team
        self._set_layout()

    def worldcup_list_by_range(self,Range):
        Min,Max = Range
        Min_idx,Max_idx = self.worldcups_year.index(Min),self.worldcups_year.index(Max)
        Years = []
        while(Min_idx != Max_idx+1):
            Years.append(self.worldcups_year[Min_idx])
            Min_idx +=1
        return Years
            
    def worldcup_quarters(self,Range):
        # Range - A list with the minimum year and the maximum year of the period to be displayed e.g [1930,2018], [1938,2002],etc
        # qx_line - Returns a list of lists  with the percentage of players born in each quarter per worldcup per quarter e.g [[q1_1930,q1_1934,q1_1938],[q2_1930,q2...],...] 
        min_year,max_year = Range
        engine = self.engine
        with engine.connect() as connection:

            df = pd.read_sql("SELECT * FROM WORLDCUP_TABLE",connection)
        years_filter = (df['GAME_YEAR']>=min_year) & (df['GAME_YEAR']<=max_year) & (df['TYPE']=='Percentage(%)')
        q1_line = list(df[years_filter]['FIRST_QUARTER'])
        q2_line = list(df[years_filter]['SECOND_QUARTER'])
        q3_line = list(df[years_filter]['THIRD_QUARTER'])
        q4_line = list(df[years_filter]['FORTH_QUARTER'])
        return q1_line,q2_line,q3_line,q4_line


    

    def _set_layout(self):
        #Initializes the first team to be displayed on the table
        default_year = 1930
        default_team = 'Argentina'
        app = self.app
        colors = {'title':"#371f1f",'text':'#374151','background':'#ffffff','boxplot':'#B5BD13','td':'#FFFFFF','tr':'#374151',
            'First Quarter':'#2C82B5','Second Quarter':'#015C91','Third Quarter':'#57AEE7','Fourth Quarter':'#8B9EAA'}
        pie_colors = {'First Quarter':"#015C91",'Second Quarter':"#2C82B5",
            'Third Quarter':"#57AEE7",'Fourth Quarter':"#8B9EAA"}
        font_family = 'Segoe UI, Helvetica Neue, sans-serif'

        dropdown_style = {'color':colors['text'],
                'fontSize':'16px',
                'fontFamily':font_family
                        } 
        dropdown_div_style = {'margin-bottom':'1%',
                            'width':'70%',
                            'margin-left':'15%',
                            'margin-right':'15%'}
        
        self.app.layout =  html.Div([
            html.H1('Relative Age Effect',style = {'textAlign':'center','color': colors['title'],'fontFamily':font_family,'fontWeight':700,'paddingTop':'2%'}),
            
                html.Div([
                    
                    html.Div(
                        dcc.Dropdown(id = 'wcups_dropdown',
                                    options = self.worldcups,
                                    value = self.worldcups[0],
                                    style = dropdown_style,
                                    className='dropdown-modern',
                                    ),
                        style = dropdown_div_style
                    ),
                    
                    html.Div(
                        dcc.Dropdown(id = 'teams_dropdown',
                                    options = self.team_names,
                                    value = self.team_names[0],
                                    style = dropdown_style,
                                    className='dropdown-modern'),
                        style = dropdown_div_style
                    )
                ], className='dashboard-filters'),

                ############################################################ Tabela #########################################################
            
                html.Div(
                    dash_table.DataTable(id ='table',data = self.displayed_team.to_dict('records'),
                                        columns= [{"name": i, "id": i} for i in self.displayed_team.columns],
                                        style_header={
                                            'backgroundColor':'#eef2f5',
                                            'color':colors['text'],
                                            'textAlign':'left',
                                            'fontSize': '15px',
                                            'fontFamily':font_family,
                                            'fontWeight':600,
                                            'border':'0',
                                            'borderBottom':'1px solid #dbe2ea'
                                            
                                        },
                                        style_data={
                                            'backgroundColor':colors['background'],
                                            'color':colors['tr'],
                                            'textAlign':'left',
                                            'height' : '50px',
                                            'fontSize': '15px',
                                            'fontFamily':font_family,
                                            'fontWeight':500,
                                            'border':'0'
                                        },
                                        style_data_conditional=[
                                                {
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': '#f8fafc'
                                                },
                                                {
                                                    'if': {'column_id': ''},
                                                    'minWidth': '200px',  # Set the minimum width for Column 1
                                                    'maxWidth': '400px',  # Set the maximum width for Column 1
                                                    'overflow': 'hidden',
                                                    'textOverflow': 'ellipsis'
                                                },
                                                {
                                                    'if': {'column_id': 'Frequency'},
                                                    'textAlign':'right',
                                                    'minWidth': '200px',  # Set the minimum width for Column 2
                                                    'maxWidth': '400px',  # Set the maximum width for Column 2
                                                    'overflow': 'hidden',
                                                    'textOverflow': 'ellipsis'
                                                },
                                                                                    {
                                                    'if': {'column_id': 'Percentage(%)'},
                                                    'textAlign':'right',
                                                    'minWidth': '200px',  # Set the minimum width for Column 3
                                                    'maxWidth': '400px',  # Set the maximum width for Column 3
                                                    'overflow': 'hidden',
                                                    'textOverflow': 'ellipsis'
                                                }
                                        ],
                                        style_header_conditional=[
                                            {'if': {'column_id': 'Frequency'}, 'textAlign': 'right'},
                                            {'if': {'column_id': 'Percentage(%)'}, 'textAlign': 'right'}
                                        ],
                                        style_as_list_view=True,
                                        style_table={'minHeight': '0'}
                                        ),
                    
                                className='dashboard-card dashboard-card--wide'
                ),

                ############################################################ Bar Graphs #########################################################
                html.Div(
                    id = 'bars_title',style = {'text-align':'center',
                                                    'color': colors['title'],
                                                    'fontFamily':font_family,
                                                    'fontWeight':700,
                                                    'paddingTop':'2%',
                                                    'fontSize':'1.85em'
                                                    }, className='dashboard-section-title'),
                

                html.Div([
                    html.Div(
                        dcc.Graph(id='graph'),
                        className='dashboard-card'
                    ),

                    html.Div(
                        dcc.Graph(id='graph2'),
                        className='dashboard-card'
                    )],
                    className='dashboard-grid'
                ),

            
                ############################################################ Box plot #########################################################

                html.Div([
                    dcc.Dropdown(id = 'drop_boxplot_over_worldcups',
                                options = self.name_of_all_teams,
                                value = self.name_of_all_teams[0],
                                style = dropdown_style,
                                className='dropdown-modern'),
                    dcc.Graph(id = 'boxplot_over_worldcups')
                ], className='dashboard-card dashboard-card--wide'),
            

                # Não modificado
                html.Div([
                    dcc.Dropdown(id = 'wcups_dropdown2',
                                options = self.worldcups,
                                value = self.worldcups[0],
                                style = dropdown_style,
                                className='dropdown-modern'),
                    dcc.Dropdown(id = 'drop_boxplot_over_worldcups_for_three',
                                style = dropdown_style,
                                className='dropdown-modern',
                                multi = True),
                    dcc.Graph(id = 'boxplot_over_worldcups_for_three')
                ], className='dashboard-card dashboard-card--wide'),
            
        
            
            
            
                html.Div([
                        dcc.Dropdown(id = 'wcups_dropdown3',
                                    options = self.worldcups,
                                    value = self.worldcups[0],
                                        style = dropdown_style,
                                        className='dropdown-modern'),
                        dcc.Graph(id='graph3',
                                    style = {'margin':'auto'} )
                            ], className='dashboard-card dashboard-card--centered'),
                
            
                
            # html.Div(
            #         dcc.Graph(figure = go.Figure(
            #                               data = [go.Bar(name = 'First Trimester',x = worldcups_year, y = t1_Bar,marker_color = colors['First Quarter']),
                #                                      go.Bar(name = 'Second Trimester',x = worldcups_year, y = t2_Bar,marker_color = colors['Second Quarter']),
            #                                       go.Bar(name = 'Third Trimester',x = worldcups_year, y = t3_Bar,marker_color = colors['Third Quarter']),
            #                                       go.Bar(name = 'Forth Trimester',x = worldcups_year, y = t4_Bar,marker_color = colors['Forth Quarter'])],
            #                               layout = go.Layout(title = {'text':'Total of players per Trimester per World Cup'.format(worldcup),
                #                                                'font':{
            #                                                     'color':colors['text'],
            #                                                     'size':20
            #                                                },
            #                                                 'x':0.5
            #                                                 },
                                                            
                #                                               yaxis = dict(title = 'Players Percentual(%)'),
                #                                               plot_bgcolor=colors['background'],
                #                                               paper_bgcolor= colors['background'],
                #                                               font_color = colors['text'],
                #                                               legend = dict(x=-0.3,y=1)),
                #                                               
                                                                
                #                            )
                #                  
                                            
                #        ),
                #        style = {'margin-left':'15%',
                #                'margin-right':'15%',
                #                }
                #)   
                html.Div(
                    'Birthday Distribution across World Cups',
                    style={
                        'text-align': 'center',
                        'color': colors['title'],
                        'fontFamily': font_family,
                        'fontWeight': 700,
                        'paddingTop': '2%',
                        'fontSize': '1.85em'
                    },
                    className='dashboard-section-title'
                ),
                html.Div([
                    dcc.RangeSlider(id='slider',
                            min=1930,
                            max=2022,
                            marks=self.slider_marks,
                            count=1,
                            value=[1930, 2022]),
                    dcc.Graph(id='line_chart')
                ],
                    className='dashboard-card dashboard-card--wide'
                )
            
            
            
        ], className='dashboard-layout', style = {'color':colors['text'],
            'backgroundColor':'#f8fafc',
            'fontFamily':font_family,
            'fontWeight':500,
            'minHeight':'100vh'})







        ############################################################## Table #########################################################

        @app.callback([Output('table','data'),
                    Output('table','columns')],
                    [Input('teams_dropdown','value'),
                    Input('wcups_dropdown','value')]) ####
        def update_table_function(selected_team,selected_worldcup):
            #selected_worldcup - String with the year of the game and the host e.g (1930 Uruguay, 1934 Italy)
            #selected_team - String with the name of the team selected
            year = selected_worldcup.split(' ')[0]
            with self.engine.connect() as connection:

                quarters_df = pd.read_sql(
                    text("""
                        SELECT TYPE, TOTAL, FIRST_QUARTER, SECOND_QUARTER, THIRD_QUARTER, FORTH_QUARTER
                        FROM WCUP_HAS_TEAMS_TABLE
                        WHERE TEAM = :team AND YEAR = :year
                    """),
                    connection,
                    params={"team": selected_team, "year": int(year)}
                )

            if quarters_df.empty:
                empty_df = pd.DataFrame(columns=['', 'Frequency', 'Percentage(%)'])
                return empty_df.to_dict('records'), [{"name": i, "id": i} for i in empty_df.columns]

            freq_row = quarters_df[quarters_df['TYPE'] == 'Frequence']
            perc_row = quarters_df[quarters_df['TYPE'] == 'Percentage(%)']

            if freq_row.empty or perc_row.empty:
                empty_df = pd.DataFrame(columns=['', 'Frequency', 'Percentage(%)'])
                return empty_df.to_dict('records'), [{"name": i, "id": i} for i in empty_df.columns]

            freq_row = freq_row.iloc[0]
            perc_row = perc_row.iloc[0]
            quarters_df = pd.DataFrame({
                '': ['Total', 'First Quarter', 'Second Quarter', 'Third Quarter', 'Fourth Quarter'],
                'Frequency': [freq_row['TOTAL'], freq_row['FIRST_QUARTER'], freq_row['SECOND_QUARTER'], freq_row['THIRD_QUARTER'], freq_row['FORTH_QUARTER']],
                'Percentage(%)': [perc_row['TOTAL'], perc_row['FIRST_QUARTER'], perc_row['SECOND_QUARTER'], perc_row['THIRD_QUARTER'], perc_row['FORTH_QUARTER']]
            })
            data = quarters_df.to_dict('records')
            columns = [{"name": i, "id": i} for i in quarters_df.columns]
            return data,columns



        @app.callback([Output('teams_dropdown','options'),
                      Output('teams_dropdown','value')],
                    [Input('wcups_dropdown','value')],
                    [State('teams_dropdown','value')])
        def update_teams_dropdown(selected_worldcup, current_team):
            #selected_worldcup - String with the year of the game and the host e.g (1930 Uruguay, 1934 Italy)
            year = selected_worldcup.split(' ')[0]
            with self.engine.connect() as connection:

                df = pd.read_sql("SELECT * FROM WCUP_HAS_TEAMS_TABLE",connection)
            filtro = (df['YEAR'] == int(year))
            teams_options = list(df[filtro]['TEAM'].unique())
            if not teams_options:
                return [], None

            if current_team in teams_options:
                return teams_options, current_team

            return teams_options, teams_options[0]


        ############################################################## Bar Plot  #########################################################

        @app.callback(Output('bars_title','children'),
                    [Input('teams_dropdown','value'),
                    Input('wcups_dropdown','value')])
        def update_bars_title(selected_team,selected_worldcup):
            return "{}'s distribution on {} world cup".format(selected_team,selected_worldcup)



        @app.callback(Output('graph','figure'),
                    [Input('teams_dropdown','value'),
                    Input('wcups_dropdown','value')])
        def update_graph(selected_team,selected_worldcup):

            with self.engine.connect() as connection:
                df = pd.read_sql("SELECT * FROM WCUP_HAS_TEAMS_TABLE",connection)

            year = int(selected_worldcup.split(' ')[0])
            updated_df = df[(df['TEAM'] == selected_team) & (df['YEAR'] == year)]

            freq_row = updated_df[updated_df['TYPE'] == 'Frequence']
            if freq_row.empty:
                return go.Figure()

            freq_row = freq_row.iloc[0]
            bar_values = np.array([
                float(freq_row['FIRST_QUARTER']),
                float(freq_row['SECOND_QUARTER']),
                float(freq_row['THIRD_QUARTER']),
                float(freq_row['FORTH_QUARTER'])
            ])

            label_df2 = ['First Quarter','Second Quarter','Third Quarter','Fourth Quarter']
            bar_colors = [pie_colors[label] for label in label_df2]
            fig = go.Figure(data = go.Bar(
                                        y = label_df2,
                                        x = bar_values,
                                        orientation = 'h',
                                        name = 'Gráfico1',
                                        marker = dict(color = bar_colors),
                                        text = bar_values,
                                        texttemplate = '<b>%{text:.0f}</b>',
                                        textposition = 'outside'),
                            layout = go.Layout(
                                            plot_bgcolor= colors['background'],
                                            paper_bgcolor= colors['background'],
                                            font=dict(family=font_family, color=colors['text']))
                                            )
            fig.update_layout(
                showlegend=False,
                xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
                yaxis=dict(
                    autorange='reversed',
                    tickmode='array',
                    tickvals=label_df2,
                    ticktext=[f'<b>{label}</b>' for label in label_df2],
                    tickfont=dict(size=15)
                )
            )
            
            
            return fig

        @app.callback(Output('graph2','figure'),
                    [Input('teams_dropdown','value'),
                    Input('wcups_dropdown','value')])
        def update_graph2(selected_team,selected_worldcup):

            with self.engine.connect() as connection:

                df = pd.read_sql("SELECT YEAR,TEAM,TYPE,FIRST_QUARTER + SECOND_QUARTER AS FIRST_AND_SECOND_QUARTER,THIRD_QUARTER,FORTH_QUARTER FROM WCUP_HAS_TEAMS_TABLE",connection)
            year = int(selected_worldcup.split(' ')[0])
            updated_df = df[(df['TEAM'] == selected_team) & (df['YEAR'] == year)]

            freq_row = updated_df[updated_df['TYPE'] == 'Frequence']
            if freq_row.empty:
                return go.Figure()

            freq_row = freq_row.iloc[0]
            bar_values = np.array([
                float(freq_row['FIRST_AND_SECOND_QUARTER']),
                float(freq_row['THIRD_QUARTER']),
                float(freq_row['FORTH_QUARTER'])
            ])
            label_df = ['First and Second','Third Quarter','Fourth Quarter']
            bar_colors = [pie_colors['First Quarter'],pie_colors['Third Quarter'],pie_colors['Fourth Quarter']]
            
            
            fig = go.Figure(data = go.Bar(
                                        y = label_df,
                                        x = bar_values,
                                        orientation = 'h',
                                        name = 'Gráfico2',
                                        marker = dict(color = bar_colors),
                                        text = bar_values,
                                        texttemplate = '<b>%{text:.0f}</b>',
                                        textposition = 'outside'),
                            layout = go.Layout(
                                            plot_bgcolor= colors['background'],
                                            paper_bgcolor= colors['background'],
                                            font=dict(family=font_family, color=colors['text']))
                                            )
            fig.update_layout(
                showlegend=False,
                xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
                yaxis=dict(
                    autorange='reversed',
                    tickmode='array',
                    tickvals=label_df,
                    ticktext=[f'<b>{label}</b>' for label in label_df],
                    tickfont=dict(size=15)
                )
            )


            return fig

        ##############################################################BoxPlot over world cups #############################################
        @app.callback(Output('boxplot_over_worldcups','figure'),Input('drop_boxplot_over_worldcups','value'))
        def update_boxplot_over_worldcups(selected_team):

            # Finds all games that a team has participated
            with self.engine.connect() as connection:

                query = f"SELECT YEAR AS PARTICIPATED_YEARS \
                        FROM WCUP_HAS_TEAMS_TABLE AS WHT \
                        INNER JOIN WORLDCUP_TABLE AS WT \
                        ON WHT.YEAR = WT.GAME_YEAR WHERE TEAM = '{selected_team}'\
                        "
                df = pd.read_sql(query,connection)
            df.drop_duplicates(inplace = True)
            df.index = range(1,df.shape[0]+1)
            df = df.astype('int32')
            participated_worldcups = df['PARTICIPATED_YEARS']


            boxplot_color = "#4D85FF"

            fig  = go.Figure(layout = go.Layout(title = {'text':'<b>{} birthdate distribution over the years</b>'.format(selected_team),
                                                'font':{
                                                    'family':font_family,
                                                    'color':colors['text'],
                                                    'size':30
                                                },
                                                'x':0.5
                                                },
                                            plot_bgcolor=colors['background'],
                                            paper_bgcolor= colors['background'],
                                            yaxis = {'title':'Month'},
                                            font=dict(family=font_family, color=colors['text'])))

            for i,wcup_year in enumerate(participated_worldcups):
                with self.engine.connect() as connection:
            
                    query = f"SELECT BIRTH_MONTH \
                            FROM  PLAYERS_TABLE AS PT \
                            INNER JOIN TEAM_HAS_PLAYERS_TABLE AS THP \
                            ON PT.ID = THP.PLAYERS_ID  \
                            WHERE TEAMS_NAME = '{selected_team}' AND GAME_YEAR = '{wcup_year}'"
                    df2 = pd.read_sql(query,connection)
                    team_box = df2['BIRTH_MONTH'].values
                    fig.add_trace(go.Box(y=team_box, name=wcup_year, marker_color=boxplot_color, opacity=0.68))
            fig.update_layout(showlegend=False,yaxis = dict(showgrid = False))
            
            return fig

                
        #####################################Boxplot from 3 teams over 1 selected world cup #############################################


        @app.callback([Output('drop_boxplot_over_worldcups_for_three','options'),
                    Output('drop_boxplot_over_worldcups_for_three','value')],
                    Input('wcups_dropdown2','value'))
        def update_barplot_dropdown(selected_worldcup):
            year = selected_worldcup.split(' ')[0]
            with self.engine.connect() as connection:

                query = f"SELECT DISTINCT TEAM FROM WCUP_HAS_TEAMS_TABLE WHERE YEAR = '{year}'"
                df = pd.read_sql(query,connection)
            teams = df['TEAM'].values    
            return teams,teams[:3]


        @app.callback(Output('boxplot_over_worldcups_for_three','figure'),
                    [Input('wcups_dropdown2','value'),
                    Input('drop_boxplot_over_worldcups_for_three','value')])
        def update_boxplot_over_worldcups_for_three(worldcup,selected_teams):

            
            worldcup_year = worldcup.split(' ')[0]


            fig  = go.Figure(layout = go.Layout(title = {'text':'<b>{},{} and {} on {} world cup</b>'.format(selected_teams[0],selected_teams[1],selected_teams[2],worldcup_year),
                                                'font':{
                                                    'family':font_family,
                                                    'color':colors['text'],
                                                    'size':30
                                                },
                                                'x':0.5
                                                },
                                            plot_bgcolor=colors['background'],
                                            paper_bgcolor= colors['background'],
                                            yaxis = {'title':'Month'},
                                            font=dict(family=font_family, color=colors['text'])),
                            )
            
            for index, team in enumerate(selected_teams):
                with self.engine.connect() as connection:
            
                    query = f"SELECT PT.NAME,BIRTH_MONTH,THP.TEAMS_NAME \
                                FROM PLAYERS_TABLE AS PT  \
                                INNER JOIN TEAM_HAS_PLAYERS_TABLE AS THP \
                                ON PT.ID = THP.PLAYERS_ID \
                                WHERE GAME_YEAR = '{worldcup_year}' \
                                AND TEAMS_NAME = '{team}'" 
                    df2 = pd.read_sql(query,connection)
                    team_box = df2['BIRTH_MONTH'].values
                    boxplot_style = {'marker_color': colors['Third Quarter']} if index == 2 else {}
                    fig.add_trace(go.Box(y=team_box, name=team, **boxplot_style))
            

                
                
            fig.update_layout(showlegend=False,yaxis = dict(showgrid = False))

            return fig



                



        ################################ Pie Chart with all teams from one world cup #############################

        @app.callback(Output('graph3','figure'),
                    [Input('wcups_dropdown3','value')])
        def update_graph3(worldcup):
            worldcups_year = worldcup.split(" ")[0]
            with self.engine.connect() as connection:

                query = f"SELECT FIRST_QUARTER,SECOND_QUARTER,THIRD_QUARTER,FORTH_QUARTER FROM WORLDCUP_TABLE WHERE TYPE = 'Percentage(%)' AND GAME_YEAR = '{worldcups_year}'"
                df2 = pd.read_sql(query,connection)
                values = df2.loc[0].values
                    

            label_df = ['First Quarter','Second Quarter','Third Quarter','Fourth Quarter']
            colors_pie = [pie_colors[label] for label in label_df]
            
            fig = go.Figure(data = go.Pie(labels = label_df,
                                        values = values,
                                        textinfo ='percent',
                                        name = 'Gráfico3',
                                        marker = dict(colors = colors_pie),
                                        textfont_size = 15,
                                        insidetextfont = dict(color = 'white'),
                                        sort = False,
                                        direction = 'clockwise'
                                        ),
                            layout = go.Layout(title = {'text':'<b>All Teams from {} World Cup</b>'.format(worldcup),
                                                'font':{
                                                    'family':font_family,
                                                    'color':colors['text'],
                                                    'size':20
                                                },
                                                'x':0.5
                                                },
                                            plot_bgcolor=colors['background'],
                                            paper_bgcolor= colors['background'],
                                            font=dict(family=font_family, color=colors['text']))
                                            )
            fig.update_layout(legend=dict(x=0, y=1))
            
            
            return fig
            

        ######################################## Line chart for all world cups ##########################################



        @app.callback(Output('line_chart','figure'),
            Input('slider','value'))
        def update_line_chart(Range):
            
            
            q_line = self.worldcup_quarters(Range)
            x_range = self.worldcup_list_by_range(Range)

            line_colors = [pie_colors['First Quarter'],pie_colors['Second Quarter'],pie_colors['Third Quarter'],pie_colors['Fourth Quarter']]
            labels = ['First Quarter','Second Quarter','Third Quarter','Fourth Quarter']
            figure = go.Figure(
                                data = [go.Scatter(x=x_range, y=q_line[0], name=labels[0], mode='lines', line=dict(color=line_colors[0], width=3)),
                                    go.Scatter(x=x_range, y=q_line[1], name=labels[1], mode='lines', line=dict(color=line_colors[1], width=3)),
                                    go.Scatter(x=x_range, y=q_line[2], name=labels[2], mode='lines', line=dict(color=line_colors[2], width=3)),
                                    go.Scatter(x=x_range, y=q_line[3], name=labels[3], mode='lines', line=dict(color=line_colors[3], width=3))],
                                layout = go.Layout(
                                                    
                                            xaxis = dict(showgrid=False,
                                                showline=True,
                                                linecolor='#dbe2ea',
                                                tickmode='linear',
                                                dtick=8),
                                            yaxis = dict(zeroline=False,
                                                                title = 'Birthdate Distribution(%)',
                                                                range = [10,40],
                                                showgrid=False,
                                                showline=True,
                                                linecolor='#dbe2ea'),
                                                                
                                                    margin=dict(
                                                                autoexpand=False,
                                                                l=70,
                                                                r=120,
                                                                t=50,
                                                                b=60,
                                                                ),     
                                                    
                                                    plot_bgcolor=colors['background'],
                                                    paper_bgcolor= colors['background'],
                                                    font=dict(family=font_family, color=colors['text']))
                                                    )
            
            annotations = [
                dict(
                    xref='paper',
                    x=1,
                    y=series[-1],
                    xanchor='left',
                    yanchor='middle',
                    text='{}%'.format(series[-1]),
                    font=dict(family=font_family, size=14, color=color),
                    showarrow=False
                )
                for series, color in zip(q_line, line_colors)
            ]

            figure.update_layout(
                annotations=annotations,
                showlegend=True,
                autosize=True,
                legend=dict(orientation='h', x=0, y=1.12)
            )
                

            return figure


















