import streamlit as st
import altair as alt
import pandas as pd
import os

# TO-DO make one object that has labels and formats as own keys for all labels
LABELS = {
    'HLTV2': 'HLTV 2.0',
    'ADR': 'adr',
    'KAST-%': 'kast',
    'Kills': 'kill_count'
}
PRECISIONS = {
    'HLTV2': 2,
    'ADR': 1,
    'KAST-%': 1,
    'Kills': 0
}

WEAPON_COLORS = {
    'AK-47': '#800000', 'AUG': '#8B4513', 'AWP': '#6B4226', 'CZ75 Auto': '#8B008B',
    'Decoy Grenade': '#404040', 'Desert Eagle': '#B8860B', 'Dual Berettas': '#8B4513',
    'FAMAS': '#8B0000', 'Five-SeveN': '#008080', 'Flashbang': '#006400', 'Galil AR': '#4B0082',
    'Glock-18': '#004d00', 'HE Grenade': '#404040', 'Incendiary Grenade': '#8B0000', 'Knife': '#004d00',
    'M4A1': '#006400', 'M4A4': '#00008B', 'MAC-10': '#8B4513', 'Molotov': '#8B0000', 'MP5-SD': '#556B2F',
    'MP7': '#00008B', 'MP9': '#404040', 'Nova': '#4B0082', 'P2000': '#006400', 'P250': '#8B4513',
    'P90': '#8B4513', 'SG 553': '#8B4513', 'Smoke Grenade': '#404040', 'SSG 08': '#004d00', 'Tec-9': '#8B4513',
    'UMP-45': '#8B4513', 'USP-S': '#404040', 'XM1014': '#4B0082', 'Zeus x27': '#8B0000'
}

# One would think that these should change in the future, until then, let's go with this
SIDE_ID = {
    'CT': 3,
    'T': 2
}

PLAYER_COLUMN_RENAMES = {'name': 'Player', 'match_count': 'GP', 'kill_count': 'K', 
                         'death_count': 'D', 'assist_count': 'A', 'HLTV 2.0': 'HLTV2', 
                         'kast': 'KAST-%', 'adr': 'ADR', 'first_kill_count': 'K (entry)', 'first_death_count': 'D (entry)'}
def colorize(val):
    color = 'green' if val == 'W' else 'red'
    return f'color: {color}'

# Not proud of using this for singular column too, but I wanted to move on to more important things
def applyFormats(df, column=None):
    if column == None:
        for key in ('HLTV2', 'ADR', 'KAST-%'):
            format_string = '{:.%df}' % PRECISIONS[key]
            df[key] = format_string.format(df[key])
    else:
        format_string = '{:.%df}' % PRECISIONS[column]
        df[column] = format_string.format(df[column])
    return df

# Path to the Excel file
EXCEL_FILE_PATH = os.path.dirname(os.path.abspath(__file__)) + "/import/demo.xlsx"

# Function to load Excel file into dataframe
@st.cache_data
def load_excel_file(file_path):
    # Load Excel file into dataframe
    xls = pd.ExcelFile(file_path)
    sheets = {}
    for sheet_name in xls.sheet_names:
        sheets[sheet_name] = pd.read_excel(xls, sheet_name)
    return sheets

def drawBarChart(df, yaxis_label):
    # Bar chart
    precision = '.%df' % PRECISIONS[yaxis_label]
    if not df.empty:
        sorted_df = df.sort_values(by=[LABELS[yaxis_label]], ascending=False)
        chart_data = sorted_df[["name", "team_name", LABELS[yaxis_label]]].reset_index()
        chart_data = chart_data.rename(columns={"team_name": 'Team'}) # Bar chart doesn't understand column names with whitespace
        
        # Define color encoding based on team names
        domain = chart_data['Team'].unique().tolist()
        range_ = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']  # Eight different colors
        chart_data = chart_data.rename(columns={LABELS[yaxis_label]: yaxis_label})
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
                color=alt.Color('Weapon', scale=alt.Scale(domain=list(WEAPON_COLORS.keys()), range=list(WEAPON_COLORS.values()))),
            ).configure_legend(
                disable=True
            ), use_container_width=True)
        with col2:
            

            pie_chart = alt.Chart(sorted_df).mark_arc().encode(
                color=alt.Color('Weapon', scale=alt.Scale(domain=list(WEAPON_COLORS.keys()), range=list(WEAPON_COLORS.values()))),
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

    entry_kills_as_ct_df = entry_kills_df[(entry_kills_df['killer_side']==SIDE_ID['CT']) & (entry_kills_df['victim_side']==SIDE_ID['T'])]
    entry_kills_as_t_df = entry_kills_df[(entry_kills_df['killer_side']==SIDE_ID['T']) & (entry_kills_df['victim_side']==SIDE_ID['CT'])]

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

def populateMatchData(row, selected_team):
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

# TO-DO Add top fragger and entry kills per team to score table
def overallStatsAndMatches(matches_df, rounds_df, kills_df, players_df, selected_team):
    col1, col2 = st.columns(2)
    with col1:
        players_columns = ['name', 'match_count', 'kill_count', 'death_count', 'assist_count', 'HLTV 2.0', 'kast', 'adr', 'first_kill_count', 'first_death_count']
        players_df = players_df[players_columns].rename(columns=PLAYER_COLUMN_RENAMES)
        players_df = players_df.apply(lambda row: applyFormats(row), axis=1)
        st.dataframe(data=players_df, hide_index=True)
    with col2:
        # Get all matches for specific team with all rounds and kills
        if selected_team != 'All': # For now, make this work with all teams later
            match_columns = ['Match ID', 'Result', 'Enemy', 'Map', f'Score ({selected_team})', 'Score (Enemy)']
            matches_df = matches_df[(matches_df['name_team_a']==selected_team) | (matches_df['name_team_b']==selected_team)]
            matches_df = matches_df.apply(lambda row: populateMatchData(row, selected_team), axis=1)
            matches_df = matches_df.sort_values(by='name')
            match_id_list = matches_df['Match ID'].tolist()
            match_id_list.insert(0,'-')
            rounds_df = rounds_df[rounds_df['match_checksum'].isin(match_id_list)]
            kills_df = kills_df[kills_df['match_checksum'].isin(match_id_list)]
            merged_df = pd.merge(rounds_df, kills_df, how='inner', left_on='number', right_on='round_number')
            st.dataframe(data=matches_df[match_columns].style.applymap(colorize, subset=['Result']),hide_index=True)
        else:
            st.write('Match list for all teams coming later. Works only for specific team for now.')
    if selected_team != 'All':
        show_raw_kbk_data = st.toggle('Show raw kill-by-kill data')
        if show_raw_kbk_data:
            st.write(merged_df)

    # selected_match_id = st.selectbox('Show match stats (not working yet)', options=match_id_list, index=0)
    # if selected_match_id != '-':
    #     rounds_df = rounds_df[rounds_df['match_checksum']==selected_match_id]
    #     kills_df = kills_df[kills_df['match_checksum']==selected_match_id]
    #     merged_df = pd.merge(rounds_df, kills_df, how='inner', left_on='number', right_on='round_number')
    
    

# Main function to run the Streamlit web app
def main():
    st.set_page_config(page_title='Unofficial CSDemoManager export parser', page_icon='📊', layout="wide", initial_sidebar_state="auto", menu_items=None)
    with st.spinner('Loading data to cache to make ultra fast queries...'):
        sheets = load_excel_file(EXCEL_FILE_PATH)
    # Set page layout to wide
    # Set title of the web app
    with st.expander('The what?'):
        st.write('''**What is this?**\n\nTool that parses statistics using Excel exports provided by [CS Demo Manager](https://cs-demo-manager.com/). 
                 Currently there's only one Excel file that contains statistics of 
                 [Elisa Open Season 6](https://liquipedia.net/counterstrike/Elisa/Open_Suomi/Season_6).\n\n**Other questions/comments?**\n\nContact gaLezki @ Twitter''')


    # Check if 'import' folder exists, if not, create it
    if not os.path.exists("import"):
        os.makedirs("import")

    # # File uploader to select Excel file
    # uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"], key="excel_uploader")

    # if uploaded_file is None:
    #     if not os.path.exists(EXCEL_FILE_PATH):
    #         st.warning("Please upload an Excel file or place 'demo.xlsx' in the 'import' folder.")
    #         return
    # else:
    #     # Save uploaded file to 'import' folder
    #     with open(EXCEL_FILE_PATH, "wb") as f:
    #         f.write(uploaded_file.getvalue())
    
    # Get unique team names
    team_names = sheets['Players']["team_name"].unique().tolist()
    team_names.insert(0, "All")  # Add "All" option to the beginning

    # Dropdown selection for team filter
    selected_team = st.selectbox("Select Team", team_names)

    # Filter DataFrame based on selected team
    if selected_team != "All":
        team_filter = True
        filtered_players_df = sheets['Players'][sheets['Players']["team_name"] == selected_team]
    else:
        team_filter = False
        filtered_players_df = sheets['Players']
    overallStatsAndMatches(sheets['Matches'], sheets['Rounds'], sheets['Kills'], filtered_players_df, selected_team)
    show_raw_player_data = st.toggle('Show raw player data', value=False)
    if show_raw_player_data:
        st.dataframe(filtered_players_df)
    drawEntryKills(sheets['Kills'], filtered_players_df, team_filter)
    for key in LABELS.keys():
        if selected_team == 'All':
            drawBarChart(filtered_players_df, key)
    if selected_team != 'All':
        drawWeaponChart(filtered_players_df['name'].tolist(), sheets['Kills'])

# Run the main function
if __name__ == "__main__":
    main()
