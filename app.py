from flask import Flask, render_template, request, jsonify
import json
import folium
from datetime import datetime
import statistics

app = Flask(__name__)

date_dict = {}

@app.route("/")
def index():
    try:
        with open("1.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            
        for obj in data["timelineObjects"]:
            if "activitySegment" in obj:
                start_time = obj["activitySegment"]["duration"]["startTimestamp"]
                date = start_time.split("T")[0]
                if "2025-01-01" <= date <= "2025-01-31":
                    if date not in date_dict:
                        date_dict[date] = []
                    date_dict[date].append(obj["activitySegment"])
                    
        return render_template("index.html")
    except Exception as e:
        return str(e)

@app.route("/get_map", methods=["POST"])
def get_map():
    try:
        selected_date = request.json.get("date")
        
        if selected_date not in date_dict:
            return jsonify({"error": "No data found for the selected date."})

        selected_segments = date_dict[selected_date]
        first_lat = selected_segments[0]["startLocation"]["latitudeE7"] / 1e7
        first_lng = selected_segments[0]["startLocation"]["longitudeE7"] / 1e7
        m = folium.Map(location=[first_lat, first_lng], zoom_start=13, 
                       dragging=False,  # Disable map dragging
                       scrollWheelZoom=False,  # Disable zoom with scroll wheel
                       zoomControl=False)  # Remove zoom controls

        total_distance = 0
        total_time = 0
        activities = {}
        speeds = []
        hourly_activity = {str(i).zfill(2): 0 for i in range(24)}
        transport_distance = {'MOTORCYCLING': 0, 'WALKING': 0, 'IN_PASSENGER_VEHICLE': 0}
        total_stops = 0

        for i, segment in enumerate(selected_segments, 1):
            try:
                # Extract locations
                start_lat = segment["startLocation"]["latitudeE7"] / 1e7
                start_lng = segment["startLocation"]["longitudeE7"] / 1e7
                end_lat = segment["endLocation"]["latitudeE7"] / 1e7
                end_lng = segment["endLocation"]["longitudeE7"] / 1e7

                # Add markers with descriptive names
                start_popup = f"Segment {i} Start: {segment.get('activityType', 'Unknown')}"
                end_popup = f"Segment {i} End: {segment.get('activityType', 'Unknown')}"
                folium.Marker([start_lat, start_lng], popup=start_popup, 
                               icon=folium.Icon(color='green', icon='play')).add_to(m)
                folium.Marker([end_lat, end_lng], popup=end_popup, 
                               icon=folium.Icon(color='red', icon='stop')).add_to(m)

                # Process waypoints
                waypoints = []
                if "waypointPath" in segment and "waypoints" in segment["waypointPath"]:
                    waypoints = [(wp["latE7"] / 1e7, wp["lngE7"] / 1e7) for wp in segment["waypointPath"]["waypoints"]]
                    total_stops += len(waypoints)
                    for j, (lat, lng) in enumerate(waypoints, 1):
                        waypoint_popup = f"Segment {i} Waypoint {j}"
                        folium.CircleMarker([lat, lng], radius=3, color="blue", 
                                             fill=True, popup=waypoint_popup).add_to(m)

                # Draw route
                route_points = [(start_lat, start_lng)] + waypoints + [(end_lat, end_lng)]
                folium.PolyLine(route_points, color="blue", weight=2.5, opacity=1).add_to(m)

                # Calculate metrics (same as previous implementation)
                distance = segment.get("distance", 0)
                total_distance += distance
                
                start_time = datetime.fromisoformat(segment["duration"]["startTimestamp"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(segment["duration"]["endTimestamp"].replace('Z', '+00:00'))
                duration = (end_time - start_time).total_seconds()
                total_time += duration

                activity_type = segment["activityType"]
                activities[activity_type] = activities.get(activity_type, 0) + 1

                hourly_activity[str(start_time.hour).zfill(2)] += duration

                if activity_type in transport_distance:
                    transport_distance[activity_type] += distance / 1000

                if duration > 0:
                    speed = (distance / 1000) / (duration / 3600)
                    speeds.append({
                        "time": start_time.strftime("%H:%M"),
                        "speed": round(speed, 2)
                    })

            except Exception as e:
                print(f"Error processing segment: {str(e)}")
                continue

        return jsonify({
            "map": m._repr_html_(),
            "stats": {
                "total_distance": round(total_distance / 1000, 2),
                "total_time": round(total_time / 60, 2),
                "activities": activities,
                "speeds": speeds,
                "hourly_activity": hourly_activity,
                "transport_distance": transport_distance,
                "total_stops": total_stops
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)