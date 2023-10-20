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


def push_to_github(filename, content, message="Update csv data"):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json()['sha']
        b64_content = base64.b64encode(content.encode()).decode()
        data = {
            "message": message,
            "content": b64_content,
            "sha": sha
        }
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            print("Successfully pushed to GitHub!")
        else:
            print("Failed to push to GitHub!")
            print(response.content)
    else:
        print("Failed to retrieve content from GitHub!")
        print(response.content)


def fetch_from_github(filename):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        b64_content = response.json()['content']
        decoded_content = base64.b64decode(b64_content).decode()
        return decoded_content
    else:
        print("Failed to retrieve content from GitHub!")
        print(response.content)
        return None


csv_totals = "totals.csv"
csv_history = "history.csv"
location = get_geolocation()


def load_totals():
    csv_content = fetch_from_github(csv_totals)
    if csv_content:
        try:
            df = pd.read_csv(StringIO(csv_content))
            if "Streak" not in df.columns:
                df["Streak"] = 0
            return df
        except Exception as e:
            print(f"Error reading the CSV: {e}")
            return pd.DataFrame({
                "Name": ["Rico", "Anders", "Live"],
                "Total Cars Seen": [0, 0, 0],
                "Streak": [0, 0, 0]
            })
    else:
        return pd.DataFrame({
            "Name": ["Rico", "Anders", "Live"],
            "Total Cars Seen": [0, 0, 0],
            "Streak": [0, 0, 0]
        })


def load_history():
    csv_content = fetch_from_github(csv_history)
    if csv_content:
        try:
            df = pd.read_csv(StringIO(csv_content))
            if df.empty:
                return pd.DataFrame(columns=["Timestamp", "Log", "Latitude", "Longitude"])
            return df
        except Exception as e:
            print(f"Error reading the CSV: {e}")
            return pd.DataFrame(columns=["Timestamp", "Log", "Latitude", "Longitude"])
    else:
        return pd.DataFrame(columns=["Timestamp", "Log", "Latitude", "Longitude"])


def save_to_csv_totals(df):
    df.to_csv(csv_totals, index=False)
    csv_data = df.to_csv(index=False)
    push_to_github(csv_totals, csv_data, message="Updated totals.csv")


def save_to_csv_history(df):
    df.to_csv(csv_history, index=False)
    csv_data = df.to_csv(index=False)
    push_to_github(csv_history, csv_data, message="Updated history.csv")


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
    last_entry = st.session_state.history[0] if st.session_state.history else None
    if last_entry and person in last_entry['Log']:
        if person == "Rico":
            st.session_state.rico_streak += 1
        elif person == "Anders":
            st.session_state.anders_streak += 1
        elif person == "Live":
            st.session_state.live_streak += 1
    else:
        if person == "Rico":
            st.session_state.rico_streak = 1
        elif person == "Anders":
            st.session_state.anders_streak = 1
        elif person == "Live":
            st.session_state.live_streak = 1

    if person == "Rico":
        st.session_state.anders_streak = 0
        st.session_state.live_streak = 0
    elif person == "Anders":
        st.session_state.rico_streak = 0
        st.session_state.live_streak = 0
    elif person == "Live":
        st.session_state.rico_streak = 0
        st.session_state.anders_streak = 0

    totals_data = {
        "Name": ["Rico", "Anders", "Live"],
        "Total Cars Seen": [st.session_state.rico_count, st.session_state.anders_count, st.session_state.live_count],
        "Streak": [st.session_state.rico_streak, st.session_state.anders_streak, st.session_state.live_streak]
    }
    save_to_csv_totals(pd.DataFrame(totals_data))


def get_highest_streak():
    streak_data = {
        "Rico": st.session_state.rico_streak,
        "Anders": st.session_state.anders_streak,
        "Live": st.session_state.live_streak
    }

    highest_streak_person = max(streak_data, key=streak_data.get)
    highest_streak_count = streak_data[highest_streak_person]

    return highest_streak_person, highest_streak_count


def update_streaks_on_delete(person):
    consecutive_entries = [entry for entry in st.session_state.history if person in entry['Log']]
    current_streak = len(consecutive_entries)

    if person == "Rico":
        st.session_state.rico_streak = current_streak
    elif person == "Anders":
        st.session_state.anders_streak = current_streak
    elif person == "Live":
        st.session_state.live_streak = current_streak


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

    save_to_csv_totals(pd.DataFrame(totals_data))
    save_to_csv_history(pd.DataFrame(st.session_state.history))
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
    st.session_state.rico_streak = 0
    st.session_state.anders_streak = 0
    st.session_state.live_streak = 0
    st.session_state.history = []
    totals_data = {
        "Name": ["Rico", "Anders", "Live"],
        "Total Cars Seen": [st.session_state.rico_count, st.session_state.anders_count, st.session_state.live_count],
        "Streak": [st.session_state.rico_streak, st.session_state.anders_streak, st.session_state.live_streak]
    }
    save_to_csv_totals(pd.DataFrame(totals_data))
    save_to_csv_history(pd.DataFrame(st.session_state.history))
    st.experimental_rerun()
