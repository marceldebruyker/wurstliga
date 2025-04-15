import streamlit as st
import pandas as pd
import os
import altair as alt
import random

# temp
# --- Configuration ---
CSV_FILE = 'wurstliga_results.csv'
# Define ALL columns expected in the CSV now
ALL_EXPECTED_COLUMNS = ['Spieltag', 'Rank_Pos', 'Name', 'Spieltagspunkte_P', 'Tabellenpunkte', 'TV', 'NULL', 'STS']
# Columns required for core app functionality
REQUIRED_COLUMNS = ['Spieltag', 'Name', 'Tabellenpunkte', 'TV', 'NULL', 'STS']
OPTIONAL_COLUMNS = ['Rank_Pos', 'Spieltagspunkte_P']
MAX_PLAYERS_DEFAULT_CHART = 5

# --- Data Loading Function ---
@st.cache_data(ttl=300, show_spinner="Lade Wurstliga Daten...")
def load_data(csv_path):
    """
    Loads, validates, and cleans data including TV, NULL, and STS columns.
    """
    empty_df = pd.DataFrame(columns=ALL_EXPECTED_COLUMNS)
    if not os.path.exists(csv_path):
        st.error(f"Fehler: CSV-Datei nicht gefunden: {os.path.abspath(csv_path)}")
        return empty_df
    if os.path.getsize(csv_path) == 0:
        print(f"Info: CSV-Datei '{csv_path}' ist leer.")
        return empty_df

    try:
        try: df = pd.read_csv(csv_path)
        except pd.errors.ParserError: df = pd.read_csv(csv_path, engine='python')
        if df.empty: return empty_df

        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            st.error(f"Fehler: Notwendige Spalten fehlen: {', '.join(missing_cols)}.")
            return empty_df

        for col in ALL_EXPECTED_COLUMNS:
             if col not in df.columns:
                  fill_val = 0 if col in ['TV', 'NULL', 'STS'] else pd.NA
                  df[col] = fill_val
                  print(f"Info: Fehlende Spalte '{col}' hinzugefügt (mit '{fill_val}').")

        df['Spieltag'] = pd.to_numeric(df['Spieltag'], errors='coerce')
        df['Rank_Pos'] = pd.to_numeric(df['Rank_Pos'], errors='coerce')
        df['Spieltagspunkte_P'] = pd.to_numeric(df['Spieltagspunkte_P'], errors='coerce')
        df['Tabellenpunkte'] = pd.to_numeric(df['Tabellenpunkte'], errors='coerce')
        df['TV'] = pd.to_numeric(df['TV'], errors='coerce')
        df['NULL'] = pd.to_numeric(df['NULL'], errors='coerce')
        df['STS'] = pd.to_numeric(df['STS'], errors='coerce')
        df['Name'] = df['Name'].astype(str)

        essential_cols = ['Spieltag', 'Name', 'Tabellenpunkte', 'TV', 'NULL', 'STS']
        original_rows = len(df)
        df.dropna(subset=essential_cols, inplace=True)
        rows_after_dropna = len(df)
        if original_rows > rows_after_dropna:
             print(f"Info: {original_rows - rows_after_dropna} Zeilen entfernt wg. fehlender Werte in {essential_cols}.")

        if df.empty: return empty_df

        df['Spieltag'] = df['Spieltag'].astype(int)
        df['Rank_Pos'] = df['Rank_Pos'].astype('Int64')
        df['Spieltagspunkte_P'] = df['Spieltagspunkte_P'].astype('Int64')
        df['Tabellenpunkte'] = df['Tabellenpunkte'].astype(int)
        df['TV'] = df['TV'].astype(int)
        df['NULL'] = df['NULL'].astype(int)
        df['STS'] = df['STS'].astype(int)

        print(f"Info: Daten erfolgreich geladen. {len(df)} gültige Zeilen.")
        return df[ALL_EXPECTED_COLUMNS]

    except Exception as e:
        st.error(f"Unerwarteter Fehler beim Laden/Verarbeiten der CSV '{csv_path}': {e}")
        return empty_df

# --- Rank Chart Data Preparation Function ---
def prepare_rank_chart_data(df):
    if df.empty or df['Spieltag'].nunique() < 2: return pd.DataFrame()
    df_chart = df.sort_values(by=['Spieltag', 'Name'])
    df_chart['Tabellenpunkte'] = pd.to_numeric(df_chart['Tabellenpunkte'], errors='coerce').fillna(0)
    df_chart['Cumulative_Tabellenpunkte'] = df_chart.groupby('Name')['Tabellenpunkte'].cumsum()
    df_chart['Cumulative_Tabellenpunkte'] = pd.to_numeric(df_chart['Cumulative_Tabellenpunkte'], errors='coerce').fillna(0)
    df_chart['Rank_At_Spieltag'] = df_chart.groupby('Spieltag')['Cumulative_Tabellenpunkte'] \
                                     .rank(method='min', ascending=False)
    df_chart['Rank_At_Spieltag'] = df_chart['Rank_At_Spieltag'].fillna(0).astype(int)
    return df_chart[['Spieltag', 'Name', 'Rank_At_Spieltag', 'Cumulative_Tabellenpunkte']]

# --- Main Application ---
def main():
    # *** UPDATED Title ***
    st.set_page_config(layout="wide", page_title="Wurstliga") # Changed page title
    st.title("📊 Wurstliga") # Changed main title

    st.sidebar.info("Zeigt die Ergebnisse der Wurstliga basierend auf `wurstliga_results.csv`.")

    df_results = load_data(CSV_FILE)
    if df_results.empty:
        st.warning("Keine gültigen Daten zum Anzeigen vorhanden.")
        return

    all_players = sorted(df_results['Name'].unique().tolist())
    if 'initial_random_players' not in st.session_state:
        num_to_select = min(len(all_players), MAX_PLAYERS_DEFAULT_CHART)
        st.session_state.initial_random_players = random.sample(all_players, k=num_to_select) if num_to_select > 0 else []

    # --- Display Sections ---
    display_overall_standings(df_results)
    display_rank_evolution_chart_section(df_results, all_players)
    display_individual_spieltag(df_results)

# --- Display Helper Functions ---
def display_overall_standings(df):
    """Displays the overall standings table including TV, NULL, and STS counts."""
    # *** UPDATED Header ***
    st.header("Tabelle") # Changed header

    try:
        df_total = df.groupby('Name', as_index=False).agg(
            Total_Spieltagspunkte_P=('Spieltagspunkte_P', 'sum'),
            Total_Tabellenpunkte=('Tabellenpunkte', 'sum'),
            Total_TV=('TV', 'sum'),
            Total_NULL=('NULL', 'sum'),
            Total_STS=('STS', 'sum')
        )
        df_display = df_total.sort_values(
            by=['Total_Tabellenpunkte', 'Total_Spieltagspunkte_P'],
            ascending=[False, False]
        ).reset_index(drop=True)
        df_display.index = df_display.index + 1
        df_display.insert(0, 'Rang', df_display.index)
        df_display.columns = [
            'Rang', 'Name', 'Kicktipp Pkt.', 'Wurstliga Pkt.',
            'TV', 'NULL', 'STS'
        ]
        df_display['TV'] = df_display['TV'].astype(int)
        df_display['NULL'] = df_display['NULL'].astype(int)
        df_display['STS'] = df_display['STS'].astype(int)
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Kicktipp Pkt.": st.column_config.NumberColumn(format="%d Pkt."),
                "Wurstliga Pkt.": st.column_config.NumberColumn(format="%d Pkt."),
                "TV": st.column_config.NumberColumn("Tipps Verpasst", help="Anzahl Spieltage mit 0 Kicktipp Punkten", format="%d"),
                "NULL": st.column_config.NumberColumn("Null Punkte", help="Anzahl Spieltage mit 0 Wurstliga Punkten", format="%d"),
                "STS": st.column_config.NumberColumn("Spieltagssiege", help="Anzahl Spieltage mit max. Kicktipp Punkten", format="%d"),
            }
         )
    except Exception as e:
        st.error(f"Fehler bei der Anzeige der Gesamtwertung: {e}")

def display_rank_evolution_chart_section(df, all_players):
    st.header("Rangentwicklung")
    if df['Spieltag'].nunique() < 2:
        st.info("Die Rangentwicklung benötigt Daten von mindestens zwei Spieltagen.")
        return
    default_selection = st.session_state.get('initial_random_players', [])
    valid_default = [p for p in default_selection if p in all_players]
    if not valid_default and all_players:
        num_to_select = min(len(all_players), MAX_PLAYERS_DEFAULT_CHART)
        valid_default = random.sample(all_players, k=num_to_select) if num_to_select > 0 else []
    selected_players = st.multiselect(
        label="Spieler für Chart auswählen:",
        options=all_players, default=valid_default, key="player_rank_selector"
    )
    if not selected_players: st.info("Wählen Sie Spieler aus, um deren Entwicklung anzuzeigen.")
    else: display_rank_evolution_chart(df, selected_players)

def display_rank_evolution_chart(df, selected_players):
    try:
        df_rank_chart_all = prepare_rank_chart_data(df.copy())
        if df_rank_chart_all.empty: return
        df_filtered_chart = df_rank_chart_all[df_rank_chart_all['Name'].isin(selected_players)]
        if df_filtered_chart.empty:
             st.warning("Keine Daten für die ausgewählten Spieler gefunden für den Chart.")
             return
        chart = alt.Chart(df_filtered_chart).mark_line(point=True).encode(
            x=alt.X('Spieltag:O', axis=alt.Axis(title='Spieltag', labelAngle=0)),
            y=alt.Y('Rank_At_Spieltag:Q', axis=alt.Axis(title='Rang'), scale=alt.Scale(reverse=True)),
            color=alt.Color('Name:N', title="Ausgewählte Spieler"),
            tooltip=[
                alt.Tooltip('Spieltag:O'), alt.Tooltip('Name:N'),
                alt.Tooltip('Rank_At_Spieltag:Q', title='Rang'),
                alt.Tooltip('Cumulative_Tabellenpunkte:Q', title='Punkte (kum.)')
            ]
        ).properties(title='Entwicklung der Tabellenposition (Wurstliga Punkte)').interactive()
        st.altair_chart(chart, use_container_width=True)
    except Exception as e: st.error(f"Fehler bei der Erstellung der Rangentwicklungsgrafik: {e}")

def display_individual_spieltag(df):
    st.header("Einzelne Spieltage im Detail")
    try:
        available_spieltage = sorted(df['Spieltag'].unique(), reverse=True)
        if not available_spieltage: st.warning("Keine Spieltage für Detailansicht gefunden."); return
        selected_spieltag = st.selectbox("Wähle einen Spieltag:", available_spieltage, index=0, key="spieltag_selector")
        if selected_spieltag:
            df_selected = df[df['Spieltag'] == selected_spieltag].copy()
            cols_to_display, col_names_display, sort_by_cols, ascending_order = [], [], [], []
            use_rank_pos = 'Rank_Pos' in df_selected.columns and not df_selected['Rank_Pos'].isnull().all()
            if use_rank_pos:
                cols_to_display = ['Rank_Pos', 'Name', 'Spieltagspunkte_P', 'Tabellenpunkte', 'TV', 'NULL', 'STS']
                col_names_display = ['Pl.', 'Name', 'P', 'Wurst Pkt.', 'TV', 'NULL', 'STS']
                sort_by_cols = ['Tabellenpunkte', 'Spieltagspunkte_P', 'Rank_Pos']
                ascending_order = [False, False, True]
            else:
                cols_to_display = ['Name', 'Spieltagspunkte_P', 'Tabellenpunkte', 'TV', 'NULL', 'STS']
                col_names_display = ['Name', 'P', 'Wurst Pkt.', 'TV', 'NULL', 'STS']
                sort_by_cols = ['Tabellenpunkte', 'Spieltagspunkte_P']
                ascending_order = [False, False]
            cols_to_display = [col for col in cols_to_display if col in df_selected.columns]
            sort_by_cols = [col for col in sort_by_cols if col in df_selected.columns]
            if not sort_by_cols: sort_by_cols = ['Name']; ascending_order = True
            df_display = df_selected.sort_values(by=sort_by_cols, ascending=ascending_order).reset_index(drop=True)
            df_display = df_display[cols_to_display]
            df_display.columns = col_names_display
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "TV": st.column_config.NumberColumn("TV", help="Tipp Verpasst (0 Kicktipp Pkt.)?", format="%d"),
                    "NULL": st.column_config.NumberColumn("NULL", help="Null Punkte Runde (0 Wurstliga Pkt.)?", format="%d"),
                    "STS": st.column_config.NumberColumn("STS", help="Spieltagssieger (Max Kicktipp Pkt.)?", format="%d"),
                    "Pl.": st.column_config.NumberColumn("Kicktipp Platz", format="%d."),
                    "P": st.column_config.NumberColumn("Kicktipp Pkt.", format="%d"),
                    "Wurst Pkt.": st.column_config.NumberColumn("Wurstliga Pkt.", format="%d"),
                }
            )
    except Exception as e:
        st.error(f"Fehler bei der Anzeige der Einzeltage: {e}")

# --- Run the Main Function ---
if __name__ == "__main__":
    main()