import streamlit as st
import altair as alt
import pandas as pd
import os

LABELS = {
    'HLTV Rating 2.0 (allegedly reverse engineered)': 'HLTV 2.0',
    'ADR': 'adr',
    'KAST': 'kast',
    'Kills': 'kill_count'
}
FORMATS = {
    'HLTV Rating 2.0 (allegedly reverse engineered)': '.2f',
    'ADR': '.1f',
    'KAST': '.1f',
    'Kills': '.0f'
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

def colorize(val):
    color = 'green' if val == 'W' else 'red'
    return f'color: {color}'

# Path to the Excel file
EXCEL_FILE_PATH = "import/demo.xlsx"

# Function to load Excel file into dataframe
@st.cache_data
def load_excel_file(file_path):
    # Load Excel file into dataframe
    xls = pd.ExcelFile(file_path)
    sheets = {}
    for sheet_name in xls.sheet_names:
        sheets[sheet_name] = pd.read_excel(xls, sheet_name)
    return sheets

# Function to read Excel file into DataFrame
def read_excel_to_dataframe(file_path, sheet):
    # Read Excel file into DataFrame
    df = pd.read_excel(file_path, sheet_name=sheet)
    return df

def drawBarChart(df, yaxis_label, selected_team):
    yaxis = LABELS[yaxis_label]
    precision = FORMATS[yaxis_label]
    # Bar chart
    if not df.empty:
        sorted_df = df.sort_values(by=[yaxis], ascending=False)
        chart_data = sorted_df[["name", "team_name", yaxis]].reset_index()
        chart_data = chart_data.rename(columns={"team_name": 'Team'}) # Bar chart doesn't understand column names with whitespace
        if yaxis == 'HLTV 2.0':
            yaxis = 'HLTV2'
            chart_data = chart_data.rename(columns={"HLTV 2.0": yaxis}) # Bar chart doesn't understand column names with whitespace
        
        # Define color encoding based on team names
        domain = chart_data['Team'].unique().tolist()
        range_ = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']  # Eight different colors
        
        st.write(f"### {yaxis_label}")
        st.altair_chart(alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('name', sort=None, title='Player'),
            y=alt.Y(yaxis, title=yaxis_label),
            color=alt.Color('Team', scale=alt.Scale(domain=domain, range=range_)),
            text=alt.Text(yaxis, format=precision)
        ), use_container_width=True)
    else:
        st.write("No data to display for selected team.")

def drawWeaponChart(players, kills_df):
    kills_df = kills_df[kills_df['killer_name'].isin(players)]
    result_df = kills_df.groupby(['killer_name', 'weapon_name']).size().reset_index(name='Count')
    for player in players:
        player_weapons_df = result_df[result_df['killer_name']==player]
        sorted_df = player_weapons_df.sort_values(by='Count', ascending=False)
        sorted_df = sorted_df.rename(columns={"weapon_name": 'Weapon'})
        col1, col2 = st.columns([3,1])
        with col1:
            # Create text layer for labels
            st.altair_chart(alt.Chart(sorted_df).mark_bar().encode(
                x=alt.X('Weapon', sort=None, title=player),
                y=alt.Y('Count', title='Kills'),
                color=alt.Color('Weapon', scale=alt.Scale(domain=list(WEAPON_COLORS.keys()), range=list(WEAPON_COLORS.values()))),
            ).configure_legend(
                disable=True  # Hide the legend
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

    entry_kills_as_ct_df = entry_kills_df[(entry_kills_df['killer_side']==3) & (entry_kills_df['victim_side']==2)]
    entry_kills_as_t_df = entry_kills_df[(entry_kills_df['killer_side']==2) & (entry_kills_df['victim_side']==3)]

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
        st.write('Red line is only "1/1" help line, not average success rate or anything like that. Will calculate and draw actual key values later.')
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
            title='Entry duels (CT)'
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
            title='Entry duels (T)'
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
    row['Id'] = row['checksum']
    return row

def loadMatchHistory(matches_df, rounds_df, kills_df, selected_team):
    match_columns = ['Id', 'Result', 'Enemy', 'Map', f'Score ({selected_team})', 'Score (Enemy)']
    matches_df = matches_df[(matches_df['name_team_a']==selected_team) | (matches_df['name_team_b']==selected_team)]
    matches_df = matches_df.apply(lambda row: populateMatchData(row, selected_team), axis=1)
    matches_df = matches_df.sort_values(by='name')
    st.write(matches_df[match_columns].style.applymap(colorize, subset=['Result'])) # debug

    match_id_list = matches_df['Id'].tolist()
    match_id_list.insert(0,'-')
    selected_match_id = st.selectbox('Show match stats', options=match_id_list, index=0)
    if selected_match_id != '-':
        rounds_df = rounds_df[rounds_df['match_checksum']==selected_match_id]
        kills_df = kills_df[kills_df['match_checksum']==selected_match_id]
        merged_df = pd.merge(rounds_df, kills_df, how='inner', left_on='number', right_on='round_number')
        st.write(merged_df) # debug

# Main function to run the Streamlit web app
def main():
    st.set_page_config(page_title='Unofficial CSDemoManager export parser', page_icon='📊', layout="wide", initial_sidebar_state="auto", menu_items=None)
    with st.spinner('Loading data...'):
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

    # Read Excel file into DataFrame
    players_df = sheets['Players']
    
    # Get unique team names
    team_names = players_df["team_name"].unique().tolist()
    team_names.insert(0, "All")  # Add "All" option to the beginning

    # Dropdown selection for team filter
    selected_team = st.selectbox("Select Team", team_names)

    # Filter DataFrame based on selected team
    if selected_team != "All":
        team_filter = True
        filtered_players_df = players_df[players_df["team_name"] == selected_team]
        loadMatchHistory(sheets['Matches'], sheets['Rounds'], sheets['Kills'], selected_team)
    else:
        team_filter = False
        filtered_players_df = players_df
    
    show_raw_player_data = st.toggle('Show raw player data', value=False)
    if show_raw_player_data:
        st.dataframe(filtered_players_df) # debug

    # bar_y = st.selectbox('Bar chart value', options=LABELS.keys())
    for key in LABELS.keys():
        drawBarChart(filtered_players_df, key, selected_team)
    if selected_team != 'All':
        drawWeaponChart(filtered_players_df['name'].tolist(), sheets['Kills'])

    drawEntryKills(sheets['Kills'], filtered_players_df, team_filter)

# Run the main function
if __name__ == "__main__":
    main()
