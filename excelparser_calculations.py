import excelparser_config as constants
import pandas as pd

def calculateEntryKills(kills_df, players_df):
    # Find the index of the row with the smallest tick for each match_checksum & round_number combination
    idx_min_tick = kills_df.groupby(['match_checksum', 'round_number'])['tick'].idxmin()

    # Select the rows with the smallest tick
    entry_kills_df = kills_df.loc[idx_min_tick]

    entry_kills_as_ct_df = entry_kills_df[(entry_kills_df['killer_side']==constants.SIDE_ID['CT']) & (entry_kills_df['victim_side']==constants.SIDE_ID['T'])]
    entry_kills_as_t_df = entry_kills_df[(entry_kills_df['killer_side']==constants.SIDE_ID['T']) & (entry_kills_df['victim_side']==constants.SIDE_ID['CT'])]

    # Group by killer_name and victim_name and count occurrences
    killer_counts_as_ct_df = entry_kills_as_ct_df['killer_name'].value_counts().reset_index()
    killer_counts_as_t_df = entry_kills_as_t_df['killer_name'].value_counts().reset_index()

    # Victim counts from other side
    victim_counts_as_ct = entry_kills_as_t_df['victim_name'].value_counts().reset_index()
    victim_counts_as_t = entry_kills_as_ct_df['victim_name'].value_counts().reset_index()

    # Define columns for all
    killer_counts_as_ct_df.columns = ['Name', 'Kills']
    killer_counts_as_t_df.columns = ['Name', 'Kills']
    victim_counts_as_ct.columns = ['Name', 'Deaths']
    victim_counts_as_t.columns = ['Name', 'Deaths']

    # Merge the counts
    merged_counts_as_ct_df = pd.merge(killer_counts_as_ct_df, victim_counts_as_ct, on='Name', how='outer').fillna(0)
    merged_counts_ct_with_team_df = pd.merge(merged_counts_as_ct_df, players_df, left_on='Name', right_on='name').rename(columns={'team_name': 'Team', 'Name': 'Player'})
    merged_counts_as_t_df = pd.merge(killer_counts_as_t_df, victim_counts_as_t, on='Name', how='outer').fillna(0)
    merged_counts_t_with_team_df = pd.merge(merged_counts_as_t_df, players_df, left_on='Name', right_on='name').rename(columns={'team_name': 'Team', 'Name': 'Player'})
    return {
        'CT': merged_counts_ct_with_team_df,
        'T': merged_counts_t_with_team_df,
        'CT_raw': merged_counts_as_ct_df,
        'T_raw': merged_counts_as_t_df
    }