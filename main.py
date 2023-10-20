import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation
import folium
from streamlit_folium import folium_static
import requests
import base64
from io import StringIO
import sqlite3

DATABASE_NAME = "sightings.db"


def create_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn


def initialize_database():
    with create_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS totals
                     (Name TEXT, TotalCarsSeen INTEGER, Streak INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS history
                     (Timestamp TEXT, Log TEXT, Latitude REAL, Longitude REAL)''')


initialize_database()


def load_totals_from_db():
    with create_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM totals')
        rows = c.fetchall()
        if rows:
            return pd.DataFrame(rows, columns=["Name", "Total Cars Seen", "Streak"])
        else:
            default_data = {
                "Name": ["Rico", "Anders", "Live"],
                "Total Cars Seen": [0, 0, 0],
                "Streak": [0, 0, 0]
            }
            save_totals_to_db(pd.DataFrame(default_data))
            return pd.DataFrame(default_data)


def load_history_from_db():
    with create_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM history')
        rows = c.fetchall()
        if rows:
            return pd.DataFrame(rows, columns=["Timestamp", "Log", "Latitude", "Longitude"])
        else:
            return pd.DataFrame(columns=["Timestamp", "Log", "Latitude", "Longitude"])


def save_totals_to_db(df):
    with create_connection() as conn:
        df.to_sql('totals', conn, if_exists='replace', index=False)


def save_history_to_db(df):
    with create_connection() as conn:
        if not df.empty:
            df.to_sql('history', conn, if_exists='replace', index=False)
        else:
            conn.execute("DELETE FROM history")



csv_totals = "totals.csv"
csv_history = "history.csv"
location = get_geolocation()


def get_city_from_coords(latitude, longitude):
    geolocator = Nominatim(user_agent="jusyAPP")
    location = geolocator.reverse((latitude, longitude), exactly_one=True)

    if location:
        address = location.raw.get('address', {})
        city = address.get('city', '')
        return city
    else:
        return "Unknown Location"


def update_streaks(person):
    with create_connection() as conn:
        c = conn.cursor()

        # Start by assuming we've broken the streak
        current_streak = 0

        # Check for recent entries to determine the streak
        consecutive_entries = [entry for entry in st.session_state.history if person in entry['Log']]

        for entry in consecutive_entries:
            if person in entry['Log']:
                current_streak += 1
            else:
                break

        # Update the person's streak in the database
        c.execute("UPDATE totals SET Streak=? WHERE Name=?", (current_streak, person))


def get_highest_streak():
    with create_connection() as conn:
        c = conn.cursor()

        # Fetch all streaks and find the max
        c.execute("SELECT Name, Streak FROM totals")
        all_streaks = c.fetchall()
        highest_streak = max(all_streaks, key=lambda x: x[1])

        return highest_streak


def update_streaks_on_delete(person):
    with create_connection() as conn:
        c = conn.cursor()

        current_streak = 0

        consecutive_entries = [entry for entry in st.session_state.history if person in entry['Log']]

        for entry in consecutive_entries:
            if person in entry['Log']:
                current_streak += 1
            else:
                break

        c.execute("UPDATE totals SET Streak=? WHERE Name=?", (current_streak, person))


totals_df = load_totals_from_db()
history_df = load_history_from_db()

if 'rico_count' not in st.session_state:
    st.session_state.rico_count = totals_df.loc[totals_df["Name"] == "Rico", "Total Cars Seen"].values[0]

if 'anders_count' not in st.session_state:
    st.session_state.anders_count = totals_df.loc[totals_df["Name"] == "Anders", "Total Cars Seen"].values[0]

if 'live_count' not in st.session_state:
    st.session_state.live_count = totals_df.loc[totals_df["Name"] == "Live", "Total Cars Seen"].values[0]

if 'history' not in st.session_state:
    st.session_state.history = history_df.to_dict(orient='records')

if 'rico_streak' not in st.session_state:
    st.session_state.rico_streak = totals_df.loc[totals_df["Name"] == "Rico", "Streak"].values[0]

if 'anders_streak' not in st.session_state:
    st.session_state.anders_streak = totals_df.loc[totals_df["Name"] == "Anders", "Streak"].values[0]

if 'live_streak' not in st.session_state:
    st.session_state.live_streak = totals_df.loc[totals_df["Name"] == "Live", "Streak"].values[0]

st.sidebar.header('Make a Sighting 🚨')

person = st.sidebar.selectbox("Select a person", ["Rico", "Anders", "Live"])

if st.sidebar.button("Submit"):
    timestamp = datetime.now().strftime('%Y-%m-%d | %H:%M')

    latitude = location['coords']['latitude']
    longitude = location['coords']['longitude']

    if person == "Rico":
        st.session_state.rico_count += 1
    elif person == "Anders":
        st.session_state.anders_count += 1
    elif person == "Live":
        st.session_state.live_count += 1

    new_log = {
        "Timestamp": timestamp,
        "Log": person,
        "Latitude": location['coords']['latitude'] if location else None,
        "Longitude": location['coords']['longitude'] if location else None
    }
    st.session_state.history.insert(0, new_log)

    totals_data = {
        "Name": ["Rico", "Anders", "Live"],
        "Total Cars Seen": [st.session_state.rico_count, st.session_state.anders_count, st.session_state.live_count],
        "Streak": [st.session_state.rico_streak, st.session_state.anders_streak, st.session_state.live_streak]
    }

    save_totals_to_db(pd.DataFrame(totals_data))
    save_history_to_db(pd.DataFrame(st.session_state.history))
    update_streaks(person)

    st.experimental_rerun()

sorted_counts = sorted(
    [('Rico', st.session_state.rico_count),
     ('Anders', st.session_state.anders_count),
     ('Live', st.session_state.live_count)],
    key=lambda x: x[1], reverse=True
)
is_tie = sorted_counts[0][1] == sorted_counts[1][1]
all_same = len(set([count[1] for count in sorted_counts])) == 1
no_sightings = sorted_counts[0][1] == 0

st.sidebar.markdown("""
<style>
.leader-card {
    background-color: #ffdd57;  
    padding: 10px 15px;
    margin: 10px 0px;
    border-radius: 15px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

if all_same and no_sightings:
    st.sidebar.markdown(f"""
    <div class="leader-card">
        <h3>🚫 No Sightings Yet 🚫</h3>
        <h2>Let the Race Begin!</h2>
    </div>
    """, unsafe_allow_html=True)
elif all_same:
    st.sidebar.markdown(f"""
    <div class="leader-card">
        <h3>🏆 Three-way Tie! 🏆</h3>
        <h2>All at {sorted_counts[0][1]} Sightings</h2>
    </div>
    """, unsafe_allow_html=True)
elif is_tie:
    st.sidebar.markdown(f"""
    <div class="leader-card">
        <h3>🏆 It's a Tie! 🏆</h3>
        <h2>{sorted_counts[0][0]} & {sorted_counts[1][0]}</h2>
        <p>{sorted_counts[0][1]} Sightings</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown(f"""
    <div class="leader-card">
        <h3>🏆 Current Leader 🏆</h3>
        <h2>{sorted_counts[0][0]}</h2>
        <p>{sorted_counts[0][1]} Sightings</p>
    </div>
    """, unsafe_allow_html=True)

highest_streak_person, highest_streak_count = get_highest_streak()

st.sidebar.markdown("""
<style>
.streak-card {
    background-color: #ffeca4;  
    padding: 10px 15px;
    margin: 10px 0px;
    border-radius: 15px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

if highest_streak_count == 0:
    st.sidebar.markdown(f"""
    <div class="streak-card">
        <h3>🚫 No Streaks Yet 🚫</h3>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown(f"""
    <div class="streak-card">
        <h3>🔥 Current Streak Champion 🔥</h3>
        <h2>{highest_streak_person}</h2>
        <p>Streak: {highest_streak_count} Sightings</p>
    </div>
    """, unsafe_allow_html=True)

st.subheader('Jucy Car Game 🚗🃏')

chart_data = {
    "Person": ["Rico", "Anders", "Live"],
    "Sightings": [st.session_state.rico_count, st.session_state.anders_count, st.session_state.live_count]
}

chart_df = pd.DataFrame(chart_data)

chart = alt.Chart(chart_df).mark_bar().encode(
    x='Person',
    y='Sightings',
    color='Person'
)

st.altair_chart(chart, use_container_width=True)

st.subheader('History Log')

# Display the last 5 actions with a delete button for each log entry
for idx, log_entry in enumerate(st.session_state.history[:5]):
    city = get_city_from_coords(log_entry['Latitude'], log_entry['Longitude'])
    col1, col2 = st.columns([5, 1])  # adjust the ratio as needed

    with col1:
        col1.write(f"{log_entry['Timestamp']} - {log_entry['Log']} - Near {city}")

    with col2:
        if col2.button("Delete", key=f"delete_{idx}"):
            log_content = st.session_state.history[idx]['Log']

            person_deleted = None
            if "Rico" in log_content:
                st.session_state.rico_count -= 1
                person_deleted = "Rico"
            elif "Anders" in log_content:
                st.session_state.anders_count -= 1
                person_deleted = "Anders"
            elif "Live" in log_content:
                st.session_state.live_count -= 1
                person_deleted = "Live"

            del st.session_state.history[idx]

            if person_deleted:
                update_streaks_on_delete(person_deleted)

            totals_data = {
                "Name": ["Rico", "Anders", "Live"],
                "Total Cars Seen": [st.session_state.rico_count, st.session_state.anders_count,
                                    st.session_state.live_count],
                "Streak": [st.session_state.rico_streak, st.session_state.anders_streak, st.session_state.live_streak]
            }
            save_totals_to_db(pd.DataFrame(totals_data))
            save_history_to_db(pd.DataFrame(st.session_state.history))
            st.experimental_rerun()


def assign_color(log):
    if 'Rico' in log:
        return 'red'
    elif 'Anders' in log:
        return 'darkblue'
    elif 'Live' in log:
        return 'blue'
    else:
        return 'black'


sightings = history_df[history_df['Latitude'].notna() & history_df['Longitude'].notna()]
sightings['color'] = sightings['Log'].apply(assign_color)
sightings = sightings.rename(columns={"Latitude": "lat", "Longitude": "lon"})

if not sightings.empty:
    m = folium.Map(location=[sightings['lat'].mean(), sightings['lon'].mean()], zoom_start=13)

    for idx, row in sightings.iterrows():
        folium.Marker([row['lat'], row['lon']],
                      popup=row['Log'],
                      icon=folium.Icon(color=row['color'])
                      ).add_to(m)
    folium_static(m)
else:
    default_location = [20, 0]  # Equator and Prime Meridian
    m = folium.Map(location=default_location, zoom_start=2)
    folium_static(m)

if st.button("Reset All Counts"):
    st.session_state.rico_count = 0
    st.session_state.anders_count = 0
    st.session_state.live_count = 0
    st.session_state.rico_streak = 0
    st.session_state.anders_streak = 0
    st.session_state.live_streak = 0
    st.session_state.history = []
    totals_data = {
        "Name": ["Rico", "Anders", "Live"],
        "Total Cars Seen": [st.session_state.rico_count, st.session_state.anders_count, st.session_state.live_count],
        "Streak": [st.session_state.rico_streak, st.session_state.anders_streak, st.session_state.live_streak]
    }
    save_totals_to_db(pd.DataFrame(totals_data))
    save_history_to_db(pd.DataFrame(st.session_state.history))
    st.experimental_rerun()
