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

# Function to read Excel file into DataFrame
def read_excel_to_dataframe(excel_file_path):
    # Read Excel file into DataFrame
    df = pd.read_excel(excel_file_path, sheet_name="Players")
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

# Main function to run the Streamlit web app
def main():
    # Set page layout to wide
    st.set_page_config(layout="wide")

    # Set title of the web app
    st.title("Players Data")

    # Check if 'import' folder exists, if not, create it
    if not os.path.exists("import"):
        os.makedirs("import")

    # Path to the Excel file
    excel_file_path = "import/demo.xlsx"

    # File uploader to select Excel file
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"], key="excel_uploader")

    if uploaded_file is None:
        if not os.path.exists(excel_file_path):
            st.warning("Please upload an Excel file or place 'demo.xlsx' in the 'import' folder.")
            return
    else:
        # Save uploaded file to 'import' folder
        with open(excel_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

    # Read Excel file into DataFrame
    df = read_excel_to_dataframe(excel_file_path)
    
    # Get unique team names
    team_names = df["team_name"].unique().tolist()
    team_names.insert(0, "All")  # Add "All" option to the beginning

    # Dropdown selection for team filter
    selected_team = st.selectbox("Select Team", team_names)

    # Filter DataFrame based on selected team
    if selected_team != "All":
        filtered_df = df[df["team_name"] == selected_team]
    else:
        filtered_df = df
    
    # Display filtered DataFrame
    st.write("### Filtered DataFrame:")
    st.dataframe(filtered_df)

    # bar_y = st.selectbox('Bar chart value', options=LABELS.keys())
    for key in LABELS.keys():
        drawBarChart(filtered_df, key, selected_team)

# Run the main function
if __name__ == "__main__":
    main()
