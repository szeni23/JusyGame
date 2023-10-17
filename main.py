import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation

csv_totals = "totals.csv"
csv_history = "history.csv"
location = get_geolocation()

def load_totals():
    try:
        return pd.read_csv(csv_totals)
    except FileNotFoundError:
        return pd.DataFrame({
            "Name": ["Rico", "Anders", "Live"],
            "Total Cars Seen": [0, 0, 0]
        })

def load_history():
    try:
        df = pd.read_csv(csv_history)
        if df.empty:
            return pd.DataFrame(columns=["Timestamp", "Log", "Latitude", "Longitude"])
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=["Timestamp", "Log", "Latitude", "Longitude"])


def save_to_csv_totals(df):
    df.to_csv(csv_totals, index=False)

def save_to_csv_history(df):
    df.to_csv(csv_history, index=False)



def get_city_from_coords(latitude, longitude):
    geolocator = Nominatim(user_agent="jusyAPP")
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    address = location.raw['address']
    city = address.get('city', '')
    return city


totals_df = load_totals()
history_df = load_history()

if 'rico_count' not in st.session_state:
    st.session_state.rico_count = totals_df.loc[totals_df["Name"] == "Rico", "Total Cars Seen"].values[0]

if 'anders_count' not in st.session_state:
    st.session_state.anders_count = totals_df.loc[totals_df["Name"] == "Anders", "Total Cars Seen"].values[0]

if 'live_count' not in st.session_state:
    st.session_state.live_count = totals_df.loc[totals_df["Name"] == "Live", "Total Cars Seen"].values[0]

if 'history' not in st.session_state:
    st.session_state.history = history_df.to_dict(orient='records')


st.sidebar.header('Jucy Car Counters')
st.sidebar.markdown(f'Rico: {st.session_state.rico_count}')
st.sidebar.markdown(f'Anders: {st.session_state.anders_count}')
st.sidebar.markdown(f'Live: {st.session_state.live_count}')

person = st.sidebar.selectbox("Select a person", ["Rico", "Anders", "Live"])
action = st.sidebar.selectbox("Action", ["Add Sighting", "Deduct Sighting"])

if st.sidebar.button("Submit"):
    log = None
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    latitude = location['coords']['latitude']
    longitude = location['coords']['longitude']

    if person == "Rico":
        if action == "Add Sighting":
            st.session_state.rico_count += 1
            log = f"Added 1 sighting for {person}."
        elif st.session_state.rico_count > 0:  # Ensure count doesn't go negative
            st.session_state.rico_count -= 1
            log = f"Deducted 1 sighting for {person}."

    elif person == "Anders":
        if action == "Add Sighting":
            st.session_state.anders_count += 1
            log = f"Added 1 sighting for {person}."
        elif st.session_state.anders_count > 0:  # Ensure count doesn't go negative
            st.session_state.anders_count -= 1
            log = f"Deducted 1 sighting for {person}."

    elif person == "Live":
        if action == "Add Sighting":
            st.session_state.live_count += 1
            log = f"Added 1 sighting for {person}."
        elif st.session_state.live_count > 0:  # Ensure count doesn't go negative
            st.session_state.live_count -= 1
            log = f"Deducted 1 sighting for {person}."

    if log:
        new_log = {
            "Timestamp": timestamp,
            "Log": log,
            "Latitude": location['coords']['latitude'] if location else None,
            "Longitude": location['coords']['longitude'] if location else None
        }
        st.session_state.history.insert(0, new_log)

    totals_data = {
        "Name": ["Rico", "Anders", "Live"],
        "Total Cars Seen": [st.session_state.rico_count, st.session_state.anders_count, st.session_state.live_count]
    }
    save_to_csv_totals(pd.DataFrame(totals_data))
    save_to_csv_history(pd.DataFrame(st.session_state.history))

    st.experimental_rerun()

st.title('Jucy Car Sighting Game')

chart_data = {
    "Person": ["Rico", "Anders", "Live"],
    "Sightings": [st.session_state.rico_count, st.session_state.anders_count, st.session_state.live_count]
}

chart_df = pd.DataFrame(chart_data)

chart = alt.Chart(chart_df).mark_bar().encode(
    x='Person',
    y='Sightings',
    color='Person'
).properties(
    title='Jucy Car Sightings Visualization'
)

st.altair_chart(chart, use_container_width=True)


st.subheader('History Log')
for log_entry in st.session_state.history[:5]:  # Display the last 5 actions
    city = get_city_from_coords(log_entry['Latitude'], log_entry['Longitude'])
    st.write(f"{log_entry['Timestamp']} - {log_entry['Log']} - Near {city}")

def assign_color(log):
    if 'Rico' in log:
        return 1
    elif 'Anders' in log:
        return 2
    elif 'Live' in log:
        return 3
    else:
        return 0

last_sightings = history_df.drop_duplicates(subset='Log', keep='last')
map_data = last_sightings[last_sightings['Latitude'].notna() & last_sightings['Longitude'].notna()]
map_data['color'] = map_data['Log'].apply(assign_color)
map_data = map_data.rename(columns={"Latitude": "lat", "Longitude": "lon"})

st.map(map_data)

if st.button("Reset All Counts"):
    st.session_state.rico_count = 0
    st.session_state.anders_count = 0
    st.session_state.live_count = 0
    st.session_state.history = []
    totals_data = {
        "Name": ["Rico", "Anders", "Live"],
        "Total Cars Seen": [st.session_state.rico_count, st.session_state.anders_count, st.session_state.live_count]
    }
    save_to_csv_totals(pd.DataFrame(totals_data))
    save_to_csv_history(pd.DataFrame(st.session_state.history))
    st.experimental_rerun()
