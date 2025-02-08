from flask import Flask, render_template, request, jsonify
import json
import folium
from datetime import datetime
import statistics
import os

app = Flask(__name__)

date_dict = {}

def load_data():
    """Load data from JSON file with multiple path attempts"""
    possible_paths = [
        "public/Data.json",
        "public/1.json",
        "1.json",
        os.path.join(os.path.dirname(__file__), "public/Data.json"),
        os.path.join(os.path.dirname(__file__), "1.json")
    ]
    
    for path in possible_paths:
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, IOError):
            continue
    
    raise FileNotFoundError("Could not find data file in any expected location")

@app.route("/")
def index():
    try:
        data = load_data()
        
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
        app.logger.error(f"Error in index route: {str(e)}")
        return jsonify({"error": f"Failed to load application: {str(e)}"}), 500

@app.route("/get_map", methods=["POST"])
def get_map():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        selected_date = request.json.get("date")
        if not selected_date:
            return jsonify({"error": "Date is required"}), 400
        
        if selected_date not in date_dict:
            return jsonify({"error": "No data found for the selected date."}), 404

        selected_segments = date_dict[selected_date]
        first_lat = selected_segments[0]["startLocation"]["latitudeE7"] / 1e7
        first_lng = selected_segments[0]["startLocation"]["longitudeE7"] / 1e7
        
        m = folium.Map(location=[first_lat, first_lng], zoom_start=13,
                      dragging=False,
                      scrollWheelZoom=False,
                      zoomControl=False)

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

                # Add markers
                start_popup = f"Segment {i} Start: {segment.get('activityType', 'Unknown')}"
                end_popup = f"Segment {i} End: {segment.get('activityType', 'Unknown')}"
                folium.Marker([start_lat, start_lng], popup=start_popup,
                            icon=folium.Icon(color='green', icon='play')).add_to(m)
                folium.Marker([end_lat, end_lng], popup=end_popup,
                            icon=folium.Icon(color='red', icon='stop')).add_to(m)

                # Process waypoints
                waypoints = []
                if "waypointPath" in segment and "waypoints" in segment["waypointPath"]:
                    waypoints = [(wp["latE7"] / 1e7, wp["lngE7"] / 1e7) 
                                for wp in segment["waypointPath"]["waypoints"]]
                    total_stops += len(waypoints)
                    for j, (lat, lng) in enumerate(waypoints, 1):
                        waypoint_popup = f"Segment {i} Waypoint {j}"
                        folium.CircleMarker([lat, lng], radius=3, color="blue",
                                          fill=True, popup=waypoint_popup).add_to(m)

                # Draw route
                route_points = [(start_lat, start_lng)] + waypoints + [(end_lat, end_lng)]
                folium.PolyLine(route_points, color="blue", weight=2.5, opacity=1).add_to(m)

                # Calculate metrics
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
                app.logger.error(f"Error processing segment {i}: {str(e)}")
                continue

        response_data = {
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
        }
        
        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error in get_map route: {str(e)}")
        return jsonify({"error": f"Failed to generate map: {str(e)}"}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
