import streamlit as st
import altair as alt
import pandas as pd
import excelparser_config as constants
import excelparser_graphs as graphs
import excelparser_calculations as calc
import os

# We'll use Streamlit's cache to avoid loading data from file more than once
@st.cache_data
def load_excel_file(file_path):
    # Load Excel file into dataframe
    xls = pd.ExcelFile(file_path)
    sheets = {}
    for sheet_name in xls.sheet_names:
        sheets[sheet_name] = pd.read_excel(xls, sheet_name)
    return sheets    

# Main function to run the Streamlit web app
def main():
    st.set_page_config(page_title='Unofficial CSDemoManager export parser', page_icon='📊', layout="wide", initial_sidebar_state="auto", menu_items=None)
    with st.spinner('Loading data to cache to make ultra fast queries...'):
        sheets = load_excel_file(constants.EXCEL_FILE_PATH)
    # Set page layout to wide
    # Set title of the web app
    with st.expander('The what?'):
        st.write('''**What is this?**\n\nTool that parses statistics using Excel exports provided by [CS Demo Manager](https://cs-demo-manager.com/). 
                 Currently there's only one Excel file that contains statistics of 
                 [Elisa Open Season 6](https://liquipedia.net/counterstrike/Elisa/Open_Suomi/Season_6).\n\n**Other questions/comments?**\n\nContact gaLezki @ Twitter
                 \n\n**About "HLTV2"**\n\nIt seems that these reverse engineered HLTV 2.0 ratings are off by ±0.10 when comparing to actual HLTV 2.0 Ratings.''')


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
    graphs.drawOverallStatsAndMatches(sheets['Matches'], sheets['Rounds'], sheets['Kills'], filtered_players_df, selected_team)
    show_raw_player_data = st.toggle('Show raw player data', value=False)
    if show_raw_player_data:
        st.dataframe(filtered_players_df)
    try:
        entry_data_dict = calc.calculateEntryKills(sheets['Kills'], filtered_players_df)
        graphs.drawEntryKills(entry_data_dict, team_filter)
    except Exception as e:
        if "Unrecognized data set" in str(e):
            st.error("Streamlit tried to show dataset before it was fully loaded to cache. Please refresh the page to fix it.")
        else:
            st.error("An error occurred: {}".format(e))
    for key in constants.LABELS.keys():
        if selected_team == 'All':
            graphs.drawBarChart(filtered_players_df, key)
    if selected_team != 'All':
        graphs.drawWeaponChart(filtered_players_df['name'].tolist(), sheets['Kills'])

# Run the main function
if __name__ == "__main__":
    main()
