import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation
import folium
from streamlit_folium import folium_static

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

    if location:
        address = location.raw.get('address', {})
        city = address.get('city', '')
        return city
    else:
        return "Unknown Location"


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

st.sidebar.header('Jucy Car Counters 🏁')

st.sidebar.markdown(
    f'**Rico** 🚗: <span style="color:red;font-size:1.2em;">{st.session_state.rico_count}</span>',
    unsafe_allow_html=True
)
st.sidebar.markdown(
    f'**Anders** 🚕: <span style="color:darkblue;font-size:1.2em;">{st.session_state.anders_count}</span>',
    unsafe_allow_html=True
)
st.sidebar.markdown(
    f'**Live** 🚙: <span style="color:blue;font-size:1.2em;">{st.session_state.live_count}</span>',
    unsafe_allow_html=True
)

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

st.sidebar.header('Make a Sighting 🚨')

person = st.sidebar.selectbox("Select a person", ["Rico", "Anders", "Live"])

if st.sidebar.button("Submit"):
    log = None
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    latitude = location['coords']['latitude']
    longitude = location['coords']['longitude']

    if person == "Rico":
        st.session_state.rico_count += 1
        log = f"Added 1 sighting for {person}."
    elif person == "Anders":
        st.session_state.anders_count += 1
        log = f"Added 1 sighting for {person}."
    elif person == "Live":
        st.session_state.live_count += 1
        log = f"Added 1 sighting for {person}."

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

for idx, log_entry in enumerate(st.session_state.history[:5]):
    city = get_city_from_coords(log_entry['Latitude'], log_entry['Longitude'])
    col1, col2 = st.columns([5, 1])  # adjust the ratio as needed

    with col1:
        col1.write(f"{log_entry['Timestamp']} - {log_entry['Log']} - Near {city}")

    with col2:
        if col2.button("Delete", key=f"delete_{idx}"):
            log_content = st.session_state.history[idx]['Log']

            if "Rico" in log_content:
                if "Added" in log_content:
                    st.session_state.rico_count -= 1
                else:
                    st.session_state.rico_count += 1
            elif "Anders" in log_content:
                if "Added" in log_content:
                    st.session_state.anders_count -= 1
                else:
                    st.session_state.anders_count += 1
            elif "Live" in log_content:
                if "Added" in log_content:
                    st.session_state.live_count -= 1
                else:
                    st.session_state.live_count += 1

            # Delete the log entry
            del st.session_state.history[idx]

            # Save the updated totals and history to the CSVs
            totals_data = {
                "Name": ["Rico", "Anders", "Live"],
                "Total Cars Seen": [st.session_state.rico_count, st.session_state.anders_count,
                                    st.session_state.live_count]
            }
            save_to_csv_totals(pd.DataFrame(totals_data))
            save_to_csv_history(pd.DataFrame(st.session_state.history))
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
    st.session_state.history = []
    totals_data = {
        "Name": ["Rico", "Anders", "Live"],
        "Total Cars Seen": [st.session_state.rico_count, st.session_state.anders_count, st.session_state.live_count]
    }
    save_to_csv_totals(pd.DataFrame(totals_data))
    save_to_csv_history(pd.DataFrame(st.session_state.history))
    st.experimental_rerun()
