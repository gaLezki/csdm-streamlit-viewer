import streamlit as st
import altair as alt
import pandas as pd
import excelparser_config as constants

def colorize(val):
    color = 'green' if val == 'W' else 'red'
    return f'color: {color}'

# Not proud of using this for singular column too, but I wanted to move on to more important things
def applyFormats(df, column=None):
    df = df.copy() # to avoid SettingWithCopyWarning
    if column == None:
        for key in ('HLTV2', 'ADR', 'KAST-%'):
            format_string = '{:.%df}' % constants.PRECISIONS[key]
            df[key] = format_string.format(df[key])
    else:
        format_string = '{:.%df}' % constants.PRECISIONS[column]
        df[column] = format_string.format(df[column])
    return df

def populateTeamMatchData(row, selected_team):
    score_column_name = f'Score ({selected_team})'
    if row['name_team_a'] == selected_team:
        row[score_column_name] = row['score_team_a']
        row['Score (Enemy)'] = row['score_team_b'] 
        row['Enemy'] = row['name_team_b']
    else:
        row[score_column_name] = row['score_team_b']
        row['Score (Enemy)'] = row['score_team_a']
        row['Enemy'] = row['name_team_a']
    row['Result'] = 'W' if (row[score_column_name] > row['Score (Enemy)']) else 'L'
    row['Map'] = row['map'][3:].capitalize()
    row['Match ID'] = row['checksum']
    return row

# TO-DO, more stuff to this function 
def populateAllMatchData(row):
    row['Map'] = row.copy()['map'][3:].capitalize()
    return row

def drawBarChart(df, yaxis_label):
    # Bar chart
    precision = '.%df' % constants.PRECISIONS[yaxis_label]
    if not df.empty:
        sorted_df = df.sort_values(by=[constants.LABELS[yaxis_label]], ascending=False)
        chart_data = sorted_df[["name", "team_name", constants.LABELS[yaxis_label]]].reset_index()
        chart_data = chart_data.rename(columns={"team_name": 'Team'}) # Bar chart doesn't understand column names with whitespace
        
        # Define color encoding based on team names
        domain = chart_data['Team'].unique().tolist()
        range_ = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']  # Eight different colors
        chart_data = chart_data.rename(columns={constants.LABELS[yaxis_label]: yaxis_label})
        chart_data = chart_data.apply(lambda row: applyFormats(row, yaxis_label), axis=1)
        chart_data[yaxis_label] = chart_data[yaxis_label].astype(float)
        st.write(f"### {yaxis_label}")
        st.altair_chart(alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('name', sort=None, title='Player'),
            y=alt.Y(yaxis_label, title=yaxis_label),
            color=alt.Color('Team', scale=alt.Scale(domain=domain, range=range_)),
            text=alt.Text(yaxis_label, format=precision)
        ), use_container_width=True)
    else:
        st.write("No data to display for selected team.")

def drawWeaponChart(players, kills_df):
    kills_df = kills_df[kills_df['killer_name'].isin(players)]
    result_df = kills_df.groupby(['killer_name', 'weapon_name']).size().reset_index(name='Count')
    st.write('### Kill distribution per weapon')
    for player in players:
        player_weapons_df = result_df[result_df['killer_name']==player]
        sorted_df = player_weapons_df.sort_values(by='Count', ascending=False)
        sorted_df = sorted_df.rename(columns={"weapon_name": 'Weapon'})
        st.write(f'#### {player}')
        col1, col2 = st.columns([3,1])
        with col1:            
            st.altair_chart(alt.Chart(sorted_df).mark_bar().encode(
                x=alt.X('Weapon', sort=None, title=player),
                y=alt.Y('Count', title='Kills'),
                color=alt.Color('Weapon', scale=alt.Scale(domain=list(constants.WEAPON_COLORS.keys()), range=list(constants.WEAPON_COLORS.values()))),
            ).configure_legend(
                disable=True
            ), use_container_width=True)
        with col2:
            pie_chart = alt.Chart(sorted_df).mark_arc().encode(
                color=alt.Color('Weapon', scale=alt.Scale(domain=list(constants.WEAPON_COLORS.keys()), range=list(constants.WEAPON_COLORS.values()))),
                theta='Count'
            )
            # Render chart using Streamlit
            st.altair_chart(pie_chart)

def drawRedLine(max_value):
    line_data = {'x': [0, max_value], 'y': [0, max_value]}
    line_df = pd.DataFrame(line_data)
    return alt.Chart(line_df).mark_line(color='red').encode(
        x='x',
        y='y'
    )

def drawEntryKills(kills_df, players_df, team_filter=False):
    # Find the index of the row with the smallest tick for each match_checksum & round_number combination
    idx_min_tick = kills_df.groupby(['match_checksum', 'round_number'])['tick'].idxmin()

    # Select the rows with the smallest tick
    entry_kills_df = kills_df.loc[idx_min_tick]

    entry_kills_as_ct_df = entry_kills_df[(entry_kills_df['killer_side']==constants.SIDE_ID['CT']) & (entry_kills_df['victim_side']==constants.SIDE_ID['T'])]
    entry_kills_as_t_df = entry_kills_df[(entry_kills_df['killer_side']==constants.SIDE_ID['T']) & (entry_kills_df['victim_side']==constants.SIDE_ID['CT'])]

    # Group by killer_name and victim_name and count occurrences
    killer_counts_as_ct = entry_kills_as_ct_df['killer_name'].value_counts().reset_index()
    killer_counts_as_t = entry_kills_as_t_df['killer_name'].value_counts().reset_index()

    # Victim counts from other side
    victim_counts_as_ct = entry_kills_as_t_df['victim_name'].value_counts().reset_index()
    victim_counts_as_t = entry_kills_as_ct_df['victim_name'].value_counts().reset_index()

    # Define columns for all
    killer_counts_as_ct.columns = ['Name', 'Kills']
    killer_counts_as_t.columns = ['Name', 'Kills']
    victim_counts_as_ct.columns = ['Name', 'Deaths']
    victim_counts_as_t.columns = ['Name', 'Deaths']

    # Merge the counts
    merged_counts_as_ct = pd.merge(killer_counts_as_ct, victim_counts_as_ct, on='Name', how='outer').fillna(0)
    merged_counts_ct_with_team = pd.merge(merged_counts_as_ct, players_df, left_on='Name', right_on='name').rename(columns={'team_name': 'Team', 'Name': 'Player'})
    merged_counts_as_t = pd.merge(killer_counts_as_t, victim_counts_as_t, on='Name', how='outer').fillna(0)
    merged_counts_t_with_team = pd.merge(merged_counts_as_t, players_df, left_on='Name', right_on='name').rename(columns={'team_name': 'Team', 'Name': 'Player'})

    # Create scatter plot
    st.write('### Entry duels')
    with st.expander('How to read'):
        st.write(f'Red line is only "50% success" help line, not average success rate or anything like that. Will calculate and draw actual key values later.')
    color_category = 'Team' if team_filter == False else 'Player'    
    col1, col2 = st.columns(2)
    with col1:
        max_value_ct = max(merged_counts_ct_with_team['Kills'].max(), merged_counts_ct_with_team['Deaths'].max()) + 2
        scatter_chart = alt.Chart(merged_counts_ct_with_team).mark_circle().encode(
            x=alt.X('Deaths', scale=alt.Scale(domain=[0, max_value_ct])),
            y=alt.Y('Kills', scale=alt.Scale(domain=[0, max_value_ct]),),
            color=color_category,
            tooltip=['Player', 'Kills', 'Deaths', 'Team']
        ).properties(
            title='Entry duels (as CT)'
        )
        st.altair_chart(scatter_chart + drawRedLine(max_value_ct), use_container_width=True)
    with col2:
        max_value_t = max(merged_counts_t_with_team['Kills'].max(), merged_counts_t_with_team['Deaths'].max()) + 2
        scatter_chart = alt.Chart(merged_counts_t_with_team).mark_circle().encode(
            x=alt.X('Deaths', scale=alt.Scale(domain=[0, max_value_t])),
            y=alt.Y('Kills', scale=alt.Scale(domain=[0, max_value_t])),
            color=color_category,
            tooltip=['Player', 'Kills', 'Deaths', 'Team']
        ).properties(
            title='Entry duels (as T)'
        )
        st.altair_chart(scatter_chart + drawRedLine(max_value_t), use_container_width=True)
    show_raw_entry_data_toggle_ct = st.toggle('Show raw data of all CT-sided entry kills', value=False)
    if show_raw_entry_data_toggle_ct:
        st.write(entry_kills_as_ct_df)
    show_raw_entry_data_toggle_t = st.toggle('Show raw data of all T-sided entry kills', value=False)
    if show_raw_entry_data_toggle_t:
        st.write(entry_kills_as_ct_df)

# TO-DO Add top fragger and entry kills per team to score table
def drawOverallStatsAndMatches(matches_df, rounds_df, kills_df, players_df, selected_team):
    col1, col2 = st.columns(2)
    with col1:
        players_columns = ['name', 'match_count', 'kill_count', 'death_count', 'assist_count', 'HLTV 2.0', 'kast', 'adr', 'first_kill_count', 'first_death_count']
        players_df = players_df[players_columns].rename(columns=constants.PLAYER_COLUMN_RENAMES)
        players_df = players_df.apply(lambda row: applyFormats(row), axis=1)
        st.dataframe(data=players_df, hide_index=True)
    with col2:
        # Get all matches for specific team with all rounds and kills
        matches_df = matches_df.sort_values(by='name')
        if selected_team != 'All': # For now, make this work with all teams later
            match_columns = ['Match ID', 'Result', 'Enemy', 'Map', f'Score ({selected_team})', 'Score (Enemy)']
            matches_df = matches_df[(matches_df['name_team_a']==selected_team) | (matches_df['name_team_b']==selected_team)]
            matches_df = matches_df.apply(lambda row: populateTeamMatchData(row, selected_team), axis=1)
            st.dataframe(data=matches_df[match_columns].style.applymap(colorize, subset=['Result']),hide_index=True)
        else:
            all_matches_columns = ['Match ID', 'Map', 'Team A', 'A', 'B', 'Team B']
            matches_df = matches_df.apply(lambda row: populateAllMatchData(row), axis=1)
            matches_df = matches_df.rename(columns=constants.ALL_MATCHES_COLUMN_RENAMES)
            st.dataframe(data=matches_df[all_matches_columns],hide_index=True)

    show_raw_kbk_data = st.toggle('Show raw kill-by-kill data')
    if show_raw_kbk_data:
        match_id_list = matches_df['Match ID'].tolist()
        all_option_name = 'All matches (all kills of all matches so there are a lot of rows)'
        match_id_list.insert(0,all_option_name)
        selected_match_id = st.selectbox('Filter by Match ID', options=match_id_list, index=1)

        rounds_df = rounds_df[rounds_df['match_checksum'].isin(match_id_list)]
        kills_df = kills_df[kills_df['match_checksum'].isin(match_id_list)]
        if selected_match_id != all_option_name:
            rounds_df = rounds_df[rounds_df['match_checksum']==selected_match_id]
            kills_df = kills_df[kills_df['match_checksum']==selected_match_id]
        else:
            rounds_df = rounds_df[rounds_df['match_checksum'].isin(match_id_list)]
            kills_df = kills_df[kills_df['match_checksum'].isin(match_id_list)]
        merged_kbk_df = pd.merge(rounds_df, kills_df, how='inner', left_on='number', right_on='round_number')
        st.dataframe(data=merged_kbk_df, hide_index=True)