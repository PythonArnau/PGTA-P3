from Loss_of_separation import to_hhmmss
from datetime import datetime, timedelta
import math

def circle_points(lat0, lon0, radius_nm, n_points=72):
    points = []
    for i in range(n_points + 1):  # +1 para cerrar el círculo
        angle = math.radians(i * 360 / n_points)
        dlat = (radius_nm / 60) * math.cos(angle)
        dlon = (radius_nm / (60 * math.cos(math.radians(lat0)))) * math.sin(angle)
        lat = lat0 + dlat
        lon = lon0 + dlon
        points.append((lon, lat))
    return points


def kml_circle(lat, lon, radius_nm, name="Circle 0.5NM"):
    pts = circle_points(lat, lon, radius_nm)
    coords = " ".join([f"{p[0]},{p[1]},0" for p in pts])

    return f"""
    <Placemark>
        <name>{name}</name>
        <Style>
            <LineStyle>
                <color>ff0000ff</color> <!-- rojo -->
                <width>2</width>
            </LineStyle>
        </Style>
        <LineString>
            <tessellate>1</tessellate>
            <coordinates>
                {coords}
            </coordinates>
        </LineString>
    </Placemark>
    """

def tod_to_kml(tod_seconds):
    base = datetime(2026, 5, 14)  # fecha del día radar
    dt = base + timedelta(seconds=tod_seconds)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def export2kml(filename, pairs, lat06, lon06, lat24, lon24):

    flights = []
    for p in pairs:
        if p.lat05_f is not None:
            flights.append({
                "callsign": p.follower,
                "lon": p.lon05_f,
                "lat": p.lat05_f,
                "time": tod_to_kml(p.TWR_time)
            })
    
    kml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<kml xmlns="http://www.opengis.net/kml/2.2">',
           '<Document>']
    
    for f in flights:
        kml.append(f"""
        <Placemark>
            <name>{f['callsign']}</name>
            <TimeStamp>
                <when>{f['time']}</when>
            </TimeStamp>
            <Point>
                <coordinates>{f['lon']},{f['lat']}</coordinates>
            </Point>
        </Placemark>
        """)

    circle_kml = kml_circle(lat06, lon06, 0.5, name=f"Círculo TWR 06")
    circle_kml2 = kml_circle(lat24, lon24, 0.5, name=f"Círculo TWR 24")
    kml.append(circle_kml)
    kml.append(circle_kml2)

    kml.append('</Document>')
    kml.append('</kml>')

    with open(filename, "w", encoding="utf-8") as file:
        file.write("\n".join(kml))

def exportFlightPaths2kml(filename, flights):

    kml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<kml xmlns="http://www.opengis.net/kml/2.2">',
           '<Document>']
    

    for f in flights:
        coords = " ".join([f"{rec.lon},{rec.lat},0" for rec in f.records])
        name = f"Route {f.callsign}"
        kml.append(f"""
        <Placemark>
            <name>{name}</name>
            <Style>
                <LineStyle>
                    <color>ff00a5ff</color> <!-- naranja -->
                    <width>2</width>
                </LineStyle>
            </Style>
            <LineString>
                <tessellate>1</tessellate>
                <coordinates>
                    {coords}
                </coordinates>
            </LineString>
        </Placemark>
        """)
    
    kml.append('</Document>')
    kml.append('</kml>')

    with open(filename, "w", encoding="utf-8") as file:
        file.write("\n".join(kml))