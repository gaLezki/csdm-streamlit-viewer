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


# Path to the Excel file
EXCEL_FILE_PATH = "import/demo.xlsx"

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

def drawWeaponChart(players):
    kills_df = read_excel_to_dataframe(EXCEL_FILE_PATH, 'Kills')
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

def drawEntryKills(players_df):
    kills_df = read_excel_to_dataframe(EXCEL_FILE_PATH, 'Kills')
    # Find the index of the row with the smallest tick for each match_checksum & round_number combination
    idx_min_tick = kills_df.groupby(['match_checksum', 'round_number'])['tick'].idxmin()

    # Select the rows with the smallest tick
    entry_kills_df = kills_df.loc[idx_min_tick]

    # Group by killer_name and victim_name and count occurrences
    killer_counts = entry_kills_df['killer_name'].value_counts().reset_index()
    killer_counts.columns = ['Name', 'Kills']

    victim_counts = entry_kills_df['victim_name'].value_counts().reset_index()
    victim_counts.columns = ['Name', 'Deaths']

    # Merge the counts
    merged_counts = pd.merge(killer_counts, victim_counts, on='Name', how='outer').fillna(0)
    merged_counts_with_team = pd.merge(merged_counts, players_df, left_on='Name', right_on='name')

    # Create scatter plot
    st.write('### Entry duels')
    scatter_chart = alt.Chart(merged_counts_with_team).mark_circle().encode(
        x='Kills',
        y='Deaths',
        color='team_name',
        tooltip=['Name', 'Kills', 'Deaths', 'team_name']
    ).properties(
        width=600,
        height=400
    )

    # Render chart using Streamlit
    st.write(scatter_chart)
    

# Main function to run the Streamlit web app
def main():
    # Set page layout to wide
    st.set_page_config(layout="wide")

    # Set title of the web app
    st.title("Players Data")

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
    players_df = read_excel_to_dataframe(EXCEL_FILE_PATH, 'Players')
    
    # Get unique team names
    team_names = players_df["team_name"].unique().tolist()
    team_names.insert(0, "All")  # Add "All" option to the beginning

    # Dropdown selection for team filter
    selected_team = st.selectbox("Select Team", team_names)

    # Filter DataFrame based on selected team
    if selected_team != "All":
        filtered_players_df = players_df[players_df["team_name"] == selected_team]
    else:
        filtered_players_df = players_df
    
    # Display filtered DataFrame
    st.write("### Filtered DataFrame:")
    st.dataframe(filtered_players_df) # debug

    # bar_y = st.selectbox('Bar chart value', options=LABELS.keys())
    # for key in LABELS.keys():
    #     drawBarChart(filtered_df, key, selected_team)
    if selected_team != 'All':
        drawWeaponChart(filtered_players_df['name'].tolist())

    drawEntryKills(players_df)

# Run the main function
if __name__ == "__main__":
    main()
