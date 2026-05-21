from geo_utils2 import latlon_to_xy, xy_to_latlon
import pandas as pd

class threshold_data:
    def __init__(self):
        self.flight: str = ""
        self.rwy: str = ""
        self.dep_time: float = 0.0
        self.sid: str = ""
        self.wake: str = ""
        self.IAS: float = 0.0
        self.height: float = 0.0
        self.tod: float = 0.0
        self.lat: float = 0.0
        self.lon: float = 0.0
        self.cross_thr: bool = False



def select_flights_rwy(flights, rwy1, rwy2):
    selected_flights_rw1 = []
    seleft_flights_rw2 = []
    for flight in flights:
        if flight.runway == rwy1:
            selected_flights_rw1.append(flight)
    for flight in flights:
        if flight.runway == rwy2:
            seleft_flights_rw2.append(flight)
    return selected_flights_rw1, seleft_flights_rw2

def detect_threshold(flights):
    #Definimos los puntos de las thresholds [lat,lon]
    thr_24L = [
        [41 + 16 / 60 + 57.65 / 3600, 2 + 4 / 60 + 28.64 / 3600],
        [41 + 16 / 60 + 55.96 / 3600, 2 + 4 / 60 + 29.68 / 3600],
        [41 + 16 / 60 + 52.61 / 3600, 2 + 4 / 60 + 10.73 / 3600],
        [41 + 16 / 60 + 54.80 / 3600, 2 + 4 / 60 + 19.29 / 3600],
    ]
    thr_06R = [
        [41 + 17 / 60 + 32.36 / 3600, 2 + 6 / 60 + 9.96 / 3600],
        [41 + 17 / 60 + 30.66 / 3600, 2 + 6 / 60 + 10.97 / 3600],
        [41 + 17 / 60 + 33.46 / 3600, 2 + 6 / 60 + 20.25 / 3600],
        [41 + 17 / 60 + 35.67 / 3600, 2 + 6 / 60 + 18.69 / 3600],
    ]

    #Convertir vertices de threshold a coordenadas x,y
    thr_24L_xy = []
    thr_06R_xy = []

    for lat,lon in thr_24L:
        x,y = latlon_to_xy(lat,lon)
        thr_24L_xy.append([x,y])

    for lat,lon in thr_06R:
        x,y = latlon_to_xy(lat,lon)
        thr_06R_xy.append([x,y])

    rw1_flights, rw2_flights = select_flights_rwy(flights, "LEBL-24L", "LEBL-06R")
    results = []

    for fl in rw1_flights:
        detected = False
        th_data = threshold_data()
        th_data.flight = fl.callsign
        th_data.rwy = fl.runway
        th_data.dep_time = fl.departure_sec
        th_data.sid = fl.sid
        th_data.wake = fl.wake

        for rec in fl.records:
            if rec.lat is None and rec.lon is None:
                continue
            if punto_en_cuadrilatero(rec,thr_24L_xy):
                th_data.lat, th_data.lon = xy_to_latlon(rec.x, rec.y)
                th_data.IAS = rec.IAS
                th_data.height = rec.h_ft
                th_data.tod = rec.ToD
                th_data.cross_thr = True
                detected = True
                break
        if not detected:
            th_data.cross_thr = False
        results.append(th_data)

    for fl in rw2_flights:
        detected = False
        th_data = threshold_data()
        th_data.flight = fl.callsign
        th_data.rwy = fl.runway
        th_data.dep_time = fl.departure_sec
        th_data.sid = fl.sid
        th_data.wake = fl.wake

        for rec in fl.records:
            if rec.lat is None and rec.lon is None:
                continue
            if punto_en_cuadrilatero(rec,thr_06R_xy):
                th_data.lat, th_data.lon = xy_to_latlon(rec.x, rec.y)
                th_data.IAS = rec.IAS
                th_data.height = rec.h_ft
                th_data.tod = rec.ToD
                th_data.cross_thr = True
                detected = True
                break
        if not detected:
            th_data.cross_thr = False
        results.append(th_data)

    return results


def punto_en_cuadrilatero(record, vertices):
    #El punto estara dentro siempre que esté a la izquierda de cada lado del cuadrilátero
    #El cross product tiene que ser siempre el mismo signo

    px = record.x
    py = record.y

    signs = []

    for i in range(4):
        x1, y1 = vertices[i]
        x2,y2 = vertices[(i+1)%4]

        #Vector lado i, i+1 cuadrilatero
        vx_lado = x2 - x1
        vy_lado = y2 - y1

        #Vector punto, lado i
        vx_punto = px - x1
        vy_punto = py - y1

        producto_vect = (vx_lado*vy_punto) - (vy_lado*vx_punto)
        signs.append(producto_vect)

    #Comprobamos si hay algun signo distinto
    for s in signs:
        if s == 0:
            continue
        if (s > 0) != (signs[0] > 0):
            return False

    return True

def export_threshold_excel(results, filepath="threshold_results.xlsx"):
    data = []
    for r in results:
        data.append({
            "Flight":        r.flight,
            "Runway":        r.rwy,
            "Dep. Time (s)": round(r.dep_time, 1),
            "SID":           r.sid,
            "Wake":          r.wake,
            "IAS (kt)":      round(r.IAS, 1)    if r.cross_thr else None,
            "Height (ft)":   round(r.height, 0) if r.cross_thr else None,
            "ToD (s)":       round(r.tod, 1)    if r.cross_thr else None,
            "Detection latitude": r.lat if r.cross_thr else None,
            "Detection longitude": r.lon if r.cross_thr else None,
            "Crossed THR":   "SÍ" if r.cross_thr else "NO",
        })

    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)


def export_threshold_kml(results, filepath="threshold_crossings.kml"):
    kml_header = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>Threshold Crossings</name>

  <Style id="style_24L">
    <IconStyle>
      <scale>1.0</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href></Icon>
    </IconStyle>
    <LabelStyle><scale>0.8</scale></LabelStyle>
  </Style>

  <Style id="style_06R">
    <IconStyle>
      <scale>1.0</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href></Icon>
    </IconStyle>
    <LabelStyle><scale>0.8</scale></LabelStyle>
  </Style>

'''
    kml_footer = '</Document>\n</kml>'

    placemarks = []
    for r in results:
        if not r.cross_thr:
            continue

        style = "style_24L" if "24L" in r.rwy else "style_06R"

        placemark = f'''  <Placemark>
    <name>{r.flight}</name>
    <styleUrl>#{style}</styleUrl>
    <description><![CDATA[
      <b>Flight:</b> {r.flight}<br/>
      <b>Runway:</b> {r.rwy}<br/>
      <b>SID:</b> {r.sid}<br/>
      <b>Wake:</b> {r.wake}<br/>
      <b>Dep. Time:</b> {r.dep_time:.1f} s<br/>
      <b>IAS:</b> {r.IAS:.1f} kt<br/>
      <b>Height:</b> {r.height:.0f} ft<br/>
      <b>ToD:</b> {r.tod:.1f} s<br/>
    ]]></description>
    <Point>
      <altitudeMode>clampToGround</altitudeMode>
      <coordinates>{r.lon:.6f},{r.lat:.6f},0</coordinates>
    </Point>
  </Placemark>
'''
        placemarks.append(placemark)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(kml_header)
        f.writelines(placemarks)
        f.write(kml_footer)
