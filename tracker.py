import requests
import json
import folium
from geopy.distance import geodesic

# Function to check if SDR covers the required ISS SSTV frequency range (around 145 MHz)
def check_frequency_coverage(sdr):
    if 'bands' in sdr:
        for band in sdr['bands']:
            if band.get("c") == "m2":
                lower_freq = band.get("l")
                upper_freq = band.get("h")
                if lower_freq <= 145 <= upper_freq:
                    return True
    return False

# Function to get the minimum distance of an SDR from the ISS path
def get_min_distance_from_iss_path(sdr_location, iss_path):
    min_distance = float('inf')
    for path_point in iss_path:
        if is_valid_coordinate(*sdr_location) and is_valid_coordinate(*path_point):
            distance = geodesic(sdr_location, path_point).km
            min_distance = min(min_distance, distance)
    return min_distance

# Function to check if latitude and longitude are valid
def is_valid_coordinate(lat, lon):
    return -90 <= lat <= 90 and -180 <= lon <= 180

# Fetch SDR data
url = "http://websdr.ewi.utwente.nl/~~websdrlistk?v=1&fmt=2&chseq=0"
response = requests.get(url)
response_text = response.text.strip()
json_start = response_text.find('[')
json_end = response_text.rfind(']') + 1

try:
    sdr_data = json.loads(response_text[json_start:json_end])
except json.JSONDecodeError as e:
    print("Failed to parse JSON:", e)
    exit()

# Fetch ISS path data
n2yo_api_url = "https://api.n2yo.com/rest/v1/satellite/positions/25544/0/0/0/3600/&apiKey=PD5NYS-2UFPJW-Y2XY87-50KZ"
iss_response = requests.get(n2yo_api_url)
iss_data = iss_response.json()

# Parse ISS positions
iss_positions = []
for position in iss_data['positions']:
    lat = position['satlatitude']
    lon = position['satlongitude']
    if is_valid_coordinate(lat, lon):
        iss_positions.append((lat, lon))

# Initialize map
sdr_map = folium.Map(location=[20, 0], zoom_start=2, control_scale=True, tiles="CartoDB Positron")

# Plot SDRs with color coding based on distance to ISS path
for sdr in sdr_data:
    lat = sdr.get("lat")
    lon = sdr.get("lon")
    desc = sdr.get("desc")
    url = sdr.get("url")

    if lat is not None and lon is not None and is_valid_coordinate(lat, lon):
        sdr_location = (lat, lon)
        
        # Check if SDR meets frequency requirements
        if check_frequency_coverage(sdr):
            # Get the minimum distance from the ISS path
            min_distance = get_min_distance_from_iss_path(sdr_location, iss_positions)
            
            # Set marker color based on distance
            if min_distance <= 350:
                marker_color = "green"
            elif 350 < min_distance <= 500:
                marker_color = "orange"
            else:
                marker_color = "blue"  # Original color for out-of-range SDRs
        else:
            marker_color = "blue"

        # Add marker with appropriate color
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(f"{desc}<br><a href='{url}' target='_blank'>Link</a>", max_width=300),
            tooltip=f"{desc} (Location: {lat}, {lon})",
            icon=folium.Icon(color=marker_color)
        ).add_to(sdr_map)

# Add ISS path as a polyline
folium.PolyLine(
    iss_positions,
    color="red",
    weight=2.5,
    opacity=0.8
).add_to(sdr_map)

# Save the map as an HTML file
sdr_map.save("sdr_map_with_iss_path_and_distance_coding.html")
print("Map saved as sdr_map_with_iss_path_and_distance_coding.html.")
