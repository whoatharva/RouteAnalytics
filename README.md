# Data Analytics Flask Project

This is a fun Flask-based project designed to analyze and visualize activity data. It uses Folium for interactive maps and provides detailed analytics like distance, speed, time, and activity types. It's a great way to explore data analytics and create interactive visualizations with Python!

## Features

- **Interactive Map**: Visualize activity routes with markers for start, end, and waypoints.
- **Detailed Analytics**: Calculate total distance, time, speed, and activity counts.
- **Transport Breakdown**: Analyze distances for different activities (walking, motorcycling, and driving).
- **Hourly Activity Insights**: View how activities are distributed throughout the day.

## Project Structure

```
/Data-Analytics-Project
│
├── app.py                    # Main Flask app
├── 1.json                     # Activity data
├── /templates
│   └── index.html             # Frontend for displaying data
└── /static
    └── styles.css             # Optional CSS for styling
```

## Requirements

To get started, you'll need to install the required Python libraries:

```bash
pip install flask folium
```

## How It Works

1. **Data Loading**: The app loads activity data from `1.json` and filters the data based on the date (January 2025).
2. **Map Generation**: The app uses Folium to generate a map displaying activity routes, with markers for the start, end, and waypoints.
3. **Analytics**: The app calculates total distance, time, speed, and transport distances for each activity type, as well as hourly activity breakdowns.
4. **User Interaction**: You can select a date and get a map with detailed statistics about the activity segments for that date.

## How to Use

1. Clone or download the project and make sure the `1.json` data file is in the project directory.
2. Install the dependencies by running:

   ```bash
   pip install flask folium
   ```

3. Start the Flask app by running:

   ```bash
   python app.py
   ```

4. Open a browser and go to `http://127.0.0.1:5000` to interact with the app.
5. Use the `/get_map` endpoint to send a POST request with a selected date to generate a map and analytics for that date.

### Example POST Request to `/get_map`

```json
{
    "date": "2025-01-15"
}
```

### Sample Response

```json
{
    "map": "<iframe ...></iframe>",
    "stats": {
        "total_distance": 12.34,
        "total_time": 123.45,
        "activities": {"WALKING": 5, "MOTORCYCLING": 3},
        "speeds": [{"time": "09:00", "speed": 5.6}],
        "hourly_activity": {"00": 0, "01": 120},
        "total_stops": 3
    }
}
```

## License

MIT License


