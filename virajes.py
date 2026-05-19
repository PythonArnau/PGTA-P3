import math
import pandas as pd


class TurnStart:
    def __init__(self):
        self.flight: str = ""
        self.turn_start: bool = False
        self.dep_time: float = 0.0
        self.turn_lat: float = 0.0
        self.turn_lon: float = 0.0
        self.turn_time: float = 0.0
        self.roll_angle: float = 0.0
        self.heading: float = 0.0
        self.TTA: float = 0.0
        self.altitude: float = 0.0 #En ft de momento
        self.SID: str = ""
        self.wake: str = ""
        self.cross_radial: bool = False

def select_flights(flights_list, rwy = "LEBL-24L"):
    #Escogemos solo los vuelos que salen por RWY 24L
    selected_flights = []
    for flight in flights_list:
        if flight.runway == rwy:
            selected_flights.append(flight)
    return selected_flights

def detect_turn(flights, hdg_threshold, ra_threshold):
    departure_flights = select_flights(flights, rwy = "LEBL-24L")
    start_turn_list = []

    #Filtro de altura para descartar records en pista o en SID en ft
    min_alt = 100
    max_alt = 2000

    for flight in departure_flights:
        turn = TurnStart()
        turn.flight = flight.callsign
        turn.dep_time = flight.departure_sec
        turn.SID = flight.sid
        turn.wake = flight.wake



        #Nos quedamos solo con los records con valor de heading y altitud dentro del rango
        valid_records = [rec for rec in flight.records
                         if rec.h_ft is not None
                         and min_alt <= rec.h_ft <= max_alt
                         and rec.HDG_bds is not None
                         and not math.isnan(rec.HDG_bds)]

        radial_cross = crosses_radial(flight)
        turn.cross_radial = radial_cross

        #Primer filtro: Diferencia en heading
        for i in range(1,len(valid_records)):

            diff = valid_records[i].HDG_bds - valid_records[i - 1].HDG_bds
            delta_hdg = abs((diff + 180) % 360 - 180)

            if delta_hdg > hdg_threshold and turn.turn_start == False:
                turn.turn_start = True
                turn.turn_lat = valid_records[i].lat
                turn.turn_lon = valid_records[i].lon
                turn.turn_time = valid_records[i].ToD
                turn.heading = valid_records[i].HDG
                turn.altitude = valid_records[i].h_ft

                ra_interp, tta_interp = interpolate_RA(flight.records, valid_records[i].ToD)
                turn.roll_angle = ra_interp
                turn.TTA = tta_interp
                break

        #Segundo Filtro: Roll angle
        if not turn.turn_start:
            for i in range(1,len(valid_records)):
                ra = valid_records[i].RA
                if ra is None or math.isnan(ra):
                    continue
                if abs(ra) > ra_threshold:
                    turn.turn_start = True
                    turn.turn_lat = valid_records[i].lat
                    turn.turn_lon = valid_records[i].lon
                    turn.turn_time = valid_records[i].ToD
                    turn.heading = valid_records[i].HDG
                    turn.altitude = valid_records[i].h_ft

                    ra_interp, tta_interp = interpolate_RA(flight.records, valid_records[i].ToD)
                    turn.roll_angle = ra_interp
                    turn.TTA = tta_interp
                    break

        start_turn_list.append(turn)

    return start_turn_list


def interpolate_RA(records, time):
    valid_records = [rec for rec in records if rec.RA is not None and not math.isnan(rec.RA)]

    if len(valid_records) < 2:
        #Sin suficientes records
        return None

    prev = None
    next = None
    for record in valid_records:
        if record.ToD <= time:
            prev = record
        elif record.ToD > time and next is None:
            next = record
            break

    if prev is None or next is None:
        return None #Out of range

    #Interpolar
    dt_tot = next.ToD - prev.ToD
    dt_target = time - prev.ToD
    alpha = dt_target/dt_tot

    interpolated_RA = prev.RA + alpha * (next.RA - prev.RA)

    n_tta = parse_float(next.TTA)
    p_tta = parse_float(prev.TTA)
    interpolated_TTA = p_tta + alpha * (n_tta - p_tta)
    return interpolated_RA, interpolated_TTA

def azimut(f_lat, f_lon):

    dvor_lat = math.radians(41 + 18 / 60 + 25.6 / 3600)  # 41°18'25.6"N
    dvor_lon = math.radians(2 + 6 / 60 + 28.1 / 3600)  # 002°06'28.1"E

    lat_rad = math.radians(f_lat)
    lon_rad = math.radians(f_lon)

    d_lon = lon_rad - lat_rad

    x = math.sin(d_lon) * math.cos(lat_rad)
    y = (math.cos(dvor_lat) * math.sin(lat_rad) - math.sin(dvor_lat) * math.cos(lat_rad) * math.cos(d_lon))

    bearing = math.degrees(math.atan2(y, x))
    return bearing % 360


def crosses_radial(flight):
    #Miramos si cruza el radial 234 desde el dvor mirando el azmiut de aeronave

    #Filtramos los records que si tienen lat or lon
    valid_records = [rec for rec in flight.records
                     if rec.lat is not None
                        and rec.lon is not None
                        and not math.isnan(rec.lat)
                        and not math.isnan(rec.lon)]
    radial = 234
    prev_az = None

    for rec in valid_records:
        az = azimut(rec.lat, rec.lon)

        if prev_az is not None:
            angular_diff = (az - prev_az + 180) % 360 - 180

            #Comprobar si R234 queda entre medio de los dos radiales anteriores
            d_prev = (radial - prev_az + 180) % 360 - 180
            d_actual = (radial - az + 180) % 360 - 180

            if d_prev * d_actual < 0 and abs(angular_diff) < 90:
                return True

    return False




def export_turns_to_excel(turn_list, filename="assessment_virajes_LEBL.xlsx"):
    data = []

    for t in turn_list:
        if t.turn_start:
            # Si se detectó viraje, guardamos los datos numéricos
            data.append({
                "Callsign": t.flight,
                "Estado": "Viraje Detectado",
                "Departure time": t.dep_time,
                "Time (ToD)": t.turn_time,
                "Crosses R-234": t.cross_radial,
                "Latitude": t.turn_lat,
                "Longitude": t.turn_lon,
                "Heading (deg)": t.heading,
                "Roll Angle (deg)": t.roll_angle,
                "Track Angle (TTA)": t.TTA,
                "Altitude (ft)": t.altitude,
                "SID": t.SID,
                "Wake": t.wake
            })
        else:
            # Si NO se detectó, añadimos la fila indicando el problema
            data.append({
                "Callsign": t.flight,
                "Estado": "No se ha detectado viraje en el rango seleccionado",
                "Departure Time": "-",
                "Time (ToD)": "-",
                "Crosses R-234": "-",
                "Latitude": "-",
                "Longitude": "-",
                "Heading (deg)": "-",
                "Roll Angle (deg)": "-",
                "Track Angle (TTA)": "-",
                "Altitude (ft)": "-",
                "SID": "-",
                "Wake": "-"

            })


    # Crear DataFrame
    df = pd.DataFrame(data)
    # Exportar a Excel
    df.to_excel(filename, index=False)

    return filename


def export_to_kml(turn_list, filename="puntos_viraje.kml"):

    # Cabecera estándar de KML
    kml_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '  <Document>',
        '    <name>Inicios de Viraje LEBL 24L</name>'
    ]

    for t in turn_list:
        if t.turn_start:
            # Añadimos un marcador por cada vuelo
            kml_content.append('    <Placemark>')
            kml_content.append(f'      <name>{t.flight}</name>')
            kml_content.append(
                f'      <description>Alt: {t.altitude}ft | RA: {t.roll_angle:.1f} | HDG: {t.heading}</description>')
            kml_content.append('      <Point>')
            # Nota: KML usa formato Longitud,Latitud,Altitud
            kml_content.append(f'        <coordinates>{t.turn_lon},{t.turn_lat},0</coordinates>')
            kml_content.append('      </Point>')
            kml_content.append('    </Placemark>')

    kml_content.append('  </Document>')
    kml_content.append('</kml>')

    # Guardar el archivo
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(kml_content))

def parse_float(value):
    #Convierte a float strings con coma como separacion
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace(',', '.'))