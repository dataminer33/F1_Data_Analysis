import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import numpy as np

# Set page config to wide mode
st.set_page_config(layout="wide")

# Custom CSS with color-neutral scheme
st.markdown("""
<style>
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
        padding: 2rem;
    }
    .stApp {
        max-width: 100%;
        padding: 1rem;
    }
    h1, h2, h3 {
        color: #e10600;
        font-family: 'Formula1', sans-serif;
        text-align: center;
    }
    .stSelectbox, .stSlider, .stDataFrame {
        background-color: var(--background-color);
        border: 1px solid var(--border-color);
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .logo-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        background-image: url('https://upload.wikimedia.org/wikipedia/commons/0/02/Michael_Schumacher%2C_Ferrari_F2001_%288968595731%29_%28cropped%29.jpg');
        background-size: cover;
        background-position: center;
        padding: 2rem;
        position: relative;
        height: 400px;
    }
    .logo-container::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(var(--background-rgb), 0.6);
    }
    .logo {
        width: 100px;
        height: auto;
        position: relative;
        z-index: 1;
    }
    .center-content {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    .title {
        position: relative;
        z-index: 1;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: var(--tab-bg-color);
        border-radius: 5px 5px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        padding-left: 20px;
        padding-right: 20px;
        font-size: 18px;
        color: var(--text-color);
    }
    .stTabs [aria-selected="true"] {
        background-color: #e10600;
        color: white;
    }

    /* Color-neutral variables */
    :root {
        --background-color: #ffffff;
        --text-color: #333333;
        --border-color: #cccccc;
        --tab-bg-color: #f0f2f6;
        --background-rgb: 255, 255, 255;
    }

    /* Dark mode */
    @media (prefers-color-scheme: dark) {
        :root {
            --background-color: #1e1e1e;
            --text-color: #ffffff;
            --border-color: #555555;
            --tab-bg-color: #2d2d2d;
            --background-rgb: 30, 30, 30;
        }
    }
</style>
""", unsafe_allow_html=True)

# Load data (using your existing load_data function)
@st.cache_data
def load_data():
    results = pd.read_csv('data/results.csv')
    drivers = pd.read_csv('data/drivers.csv')
    races = pd.read_csv('data/races.csv')
    constructors = pd.read_csv('data/constructors.csv')
    champions = pd.read_csv('data/world_champions.csv')

    # Clean and prepare data
    drivers = drivers[['driverId', 'forename', 'surname', 'dob', 'nationality']]
    drivers['full_name'] = drivers['forename'] + " " + drivers['surname']
    champions = champions[['Driver', 'Nationality','Titles']]
    # Merge datasets
    df = drivers.merge(results, on='driverId')
    df = df.merge(races[['raceId', 'name', 'year']], on='raceId')
    df = df.merge(constructors[['constructorId', 'name']], on='constructorId', suffixes=('_race', '_constructor'))
    
    return df, drivers, results, races, constructors, champions

df, drivers, results, races, constructors, champions = load_data()

# Calculate Bayesian average
def calculate_bayesian_average(wins, total, global_average, weight=10):
    return (wins + weight * global_average) / (total + weight)

# Calculate driver statistics with Bayesian average
def calculate_driver_stats(df):
    stats = df.groupby('full_name').agg({
        'resultId': 'count',
        'points': 'sum',
        'laps': 'sum',
        'position': lambda x: (x == '1').sum()
    }).reset_index()
    
    stats.columns = ['full_name', 'total_races', 'total_points', 'total_laps', 'total_wins']
    stats['win_rate'] = stats['total_wins'] / stats['total_races']
    stats['points_per_race'] = stats['total_points'] / stats['total_races']
    
    # Calculate Bayesian average
    global_win_rate = stats['total_wins'].sum() / stats['total_races'].sum()
    stats['adjusted_win_rate'] = stats.apply(lambda row: calculate_bayesian_average(row['total_wins'], row['total_races'], global_win_rate), axis=1)
    
    return stats

# Calculate constructor statistics with Bayesian average
def analyze_constructor_impact(df):
    constructor_performance = df.groupby('name_constructor').agg({
        'points': ['mean', 'sum'],
        'position': lambda x: (x == '1').sum(),
        'resultId': 'count'
    }).reset_index()
    constructor_performance.columns = ['constructor', 'avg_points', 'total_points', 'total_wins', 'total_races']
    constructor_performance['win_rate'] = constructor_performance['total_wins'] / constructor_performance['total_races']
    
    # Calculate Bayesian average
    global_win_rate = constructor_performance['total_wins'].sum() / constructor_performance['total_races'].sum()
    constructor_performance['adjusted_win_rate'] = constructor_performance.apply(
        lambda row: calculate_bayesian_average(row['total_wins'], row['total_races'], global_win_rate), axis=1)
    
    return constructor_performance

# App layout
st.markdown("""
<div class="logo-container">
    <img src="https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg" class="logo" alt="F1 Logo">
    <h1 class="title">Formula 1 Data Analysis</h1>
    <img src="https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg" class="logo" alt="F1 Logo">
</div>
""", unsafe_allow_html=True)


# Tabs
tab1, tab2 = st.tabs(["General Stats", "Driver Analysis"])

with tab1:
    st.header('General Statistics')

    # Calculate statistics
    driver_stats = calculate_driver_stats(df)
    constructor_stats = analyze_constructor_impact(df)

    # Pre-processing
    top_drivers = driver_stats.nlargest(30, 'adjusted_win_rate')[['full_name', 'adjusted_win_rate', 'total_wins', 'total_races', 'win_rate']]
    top_drivers['adjusted_win_rate'] = top_drivers['adjusted_win_rate'].apply(lambda x: f"{x:.4f}")
    top_drivers['win_rate'] = top_drivers['win_rate'].apply(lambda x: f"{x:.4f}")

    top_constructors = constructor_stats.nlargest(30, 'adjusted_win_rate')[['constructor', 'adjusted_win_rate', 'total_wins', 'total_races', 'win_rate']]
    top_constructors['adjusted_win_rate'] = top_constructors['adjusted_win_rate'].apply(lambda x: f"{x:.4f}")
    top_constructors['win_rate'] = top_constructors['win_rate'].apply(lambda x: f"{x:.4f}")

    # Display general stats in a more visually appealing way
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Drivers that Raced in F1 ", len(drivers))
    with col2:
        winning_drivers = len(driver_stats[driver_stats['total_wins'] > 0])
        st.metric("Total Driver Winning a Grand Prix", winning_drivers)
    with col3:
        winning_percentage = (winning_drivers / len(drivers)) * 100
        st.metric("Likelihood of a Driver Winning a Race", f"{winning_percentage:.2f}%")

    # World Champions Chart
    st.subheader('World Champions')
    fig = px.bar(champions, x='Driver', y='Titles', 
                 labels={'Driver': 'Drivers', 'Titles': 'Titles'},
                 color_discrete_sequence=['#e10600'])
    fig.update_xaxes(tickangle=45,tickfont=dict(color='white', size=16))
    fig.update_layout(xaxis_title_font=dict(color='white', size=16),
                      yaxis_title_font=dict(color='white', size=16)) 
    st.plotly_chart(fig,use_container_width=True)


    # Top 10 Drivers Bar Chart 
    st.subheader('Top 10 Drivers adjusted by total Races Participated')
    fig = px.bar(top_drivers, x='full_name', y='adjusted_win_rate', 
                 labels={'full_name': 'Drivers', 'adjusted_win_rate': 'Adjusted Win Rate'},
                 color_discrete_sequence=['#e10600'])
    fig.update_xaxes(tickangle=45,tickfont=dict(color='white', size=16))
    fig.update_layout(xaxis_title_font=dict(color='white', size=16),
                      yaxis_title_font=dict(color='white', size=16)) 
    st.plotly_chart(fig,use_container_width=True)

    # Top 10 Constructors Bar Chart
    st.subheader('Top 10 Constructors Adjusted by total Races Participated') 
    fig = px.bar(top_constructors, x='constructor', y='adjusted_win_rate', 
                 labels={'constructor': 'Constructor', 'adjusted_win_rate': 'Adjusted Win Rate'},
                 color_discrete_sequence=['#e10600'])
    fig.update_xaxes(tickangle=45,tickfont=dict(color='white', size=16))
    fig.update_layout(xaxis_title_font=dict(color='white', size=16),
                      yaxis_title_font=dict(color='white', size=16))  
    st.plotly_chart(fig, use_container_width=True)

    # Top Drivers by Bayesian Win Rate
    st.subheader('Top 30 Drivers Adjusted by total Races Participated')
    st.dataframe(top_drivers, use_container_width=True)

    # Top Constructors by Bayesian Win Rate
    st.subheader('Top 30 Constructors Adjusted by total Races Participated')
    st.dataframe(top_constructors, use_container_width=True)



with tab2:
    st.header('Driver Comparison')

    # Driver selection
    driver_list = sorted(df['full_name'].unique())
    selected_drivers = st.multiselect('Select up to 5 drivers', driver_list, max_selections=5)

    if not selected_drivers:
        st.warning("Please select at least one driver to analyze.")
    else:
        # Filter data for selected drivers
        filtered_df = df[df['full_name'].isin(selected_drivers)]

        # Calculate year range based on selected drivers
        min_year = filtered_df['year'].min()
        max_year = filtered_df['year'].max()

        # Year range selection
        year_range = st.slider('Select year range', int(min_year), int(max_year), (int(min_year), int(max_year)))

        # Further filter data based on year range
        filtered_df = filtered_df[(filtered_df['year'].between(year_range[0], year_range[1]))]

        # Circuit selection (only show circuits where selected drivers participated)
        participated_circuits = sorted(filtered_df['name_race'].unique())
        circuit_list = ['All'] + participated_circuits
        selected_circuit = st.selectbox('Select a circuit', circuit_list)

        if selected_circuit != 'All':
            filtered_df = filtered_df[filtered_df['name_race'] == selected_circuit]

        
        # Average Points per Season
        st.subheader('Average Points per Race Over Time')
        avg_points_data = []
        for driver in selected_drivers:
            driver_data = filtered_df[filtered_df['full_name'] == driver]
            if not driver_data.empty:
                avg_points = driver_data.groupby(['year', 'name_constructor'])['points'].mean().reset_index()
                avg_points['full_name'] = driver
                avg_points_data.append(avg_points)

        avg_points_df = pd.concat(avg_points_data, ignore_index=True)
        fig = px.line(avg_points_df, x='year', y='points', color='full_name',
                      labels={'year': 'Year', 'points': 'Average Points per Race', 'full_name': 'Driver','name_constructor': 'Constructor'},
                      hover_data={'name_constructor':True})
        fig.update_layout(xaxis_title='Year', yaxis_title='Average Points per Race')
        st.plotly_chart(fig, use_container_width=True)

        # Cumulative Wins
        cumulative_wins_data = []
        for driver in selected_drivers:
            driver_data = filtered_df[(filtered_df['full_name'] == driver) & (filtered_df['position'] == '1')].sort_values('year')
            if not driver_data.empty:
                cumulative_wins = driver_data.groupby(['year', 'name_constructor']).size().reset_index(name='wins')
                cumulative_wins['wins'] = cumulative_wins['wins'].cumsum()
                cumulative_wins['full_name'] = driver
                cumulative_wins_data.append(cumulative_wins)

        if cumulative_wins_data: 
            st.subheader('Cumulative Wins Over Time')
            cumulative_wins_df = pd.concat(cumulative_wins_data, ignore_index=True)
            fig = px.line(cumulative_wins_df, x='year', y='wins', color='full_name',
                        labels={'year': 'Year', 'wins': 'Cumulative Wins', 'full_name': 'Driver','name_constructor': 'Constructor'},
                        hover_data={'name_constructor':True})
            st.plotly_chart(fig, use_container_width=True)

        # Average Finishing Position
        st.subheader('Average Finishing Position Over Time')
        filtered_df['position_numeric'] = pd.to_numeric(filtered_df['position'], errors='coerce')
        avg_position = filtered_df.groupby(['full_name', 'year', 'name_constructor'])['position_numeric'].mean().reset_index()
        fig = px.line(avg_position, x='year', y='position_numeric', color='full_name',
                      labels={'year': 'Year', 'position_numeric': 'Average Finishing Position', 'full_name': 'Driver','name_constructor':'Constructor'},
                      hover_data={'name_constructor':True})
        fig.update_layout(yaxis_autorange='reversed')
        st.plotly_chart(fig, use_container_width=True)

        # Display race results
        st.subheader('Race Results')
        st.dataframe(filtered_df[['full_name', 'year', 'name_race', 'grid', 'position', 'points']], use_container_width=True)