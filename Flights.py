from typing import Optional
import pandas as pd
import numpy as np
from geo_utils2 import xy_to_latlon

class FlightRecord:
    def __init__(self):
        self.cat: str = ""  # Categoría ASTERIX (ej. "CAT048")
        self.sac: int = 0  # System Area Code
        self.sic: int = 0  # System Identification Code

        # --- I140 Time of Day ---
        self.ToD: Optional[float] = None  # Tiempo del día [s desde medianoche]
        self.ToD_str: str = ""  # Tiempo original "HH:MM:SS:mmm"

        # --- Coordenadas geodésicas ---
        self.lat: Optional[float] = None  # Latitud [°]
        self.lon: Optional[float] = None  # Longitud [°]
        self.h_m: Optional[float] = None  # Altitud [m]
        self.h_ft: Optional[float] = None  # Altitud [ft]

        # --- I040 Posición polar ---
        self.rho: Optional[float] = None  # Distancia al radar [NM]
        self.theta: Optional[float] = None  # Azimut [°]

        # --- Mode 3/A ---
        self.mode3A: str = ""  # Código transponder (octal, ej. "1000")

        # --- I090 Flight Level ---
        self.FL: Optional[float] = None  # Flight Level (sin corrección < 6000 ft)

        # --- I240 Target Identification ---
        self.callsign: str = ""  # TI: Indicativo OACI del vuelo (ej. "IBE3456")
        self.transponder: str = ""  # TA: Código transponder OACI (ej. "34310D")

        # --- I250 BDS 4.0 Barometric Pressure ---
        self.BP: Optional[float] = None  # Ajuste QNH [hPa]

        # --- I250 BDS 5.0 ---
        self.RA: Optional[float] = None  # Roll Angle [°]
        self.TTA: Optional[float] = None  # True Track Angle [°]
        self.GS: Optional[float] = None  # Ground Speed ASTERIX [kt, resolución entera]
        self.GS_kt: Optional[float] = None  # Ground Speed BDS [kt, mayor resolución]
        self.TAR: Optional[float] = None  # Track Angle Rate [°/s]
        self.TAS: Optional[float] = None  # True Airspeed [kt]

        # --- I250 BDS 6.0 ---
        self.HDG: Optional[float] = None  # Magnetic Heading ASTERIX [°]
        self.HDG_bds: Optional[float] = None  # Magnetic Heading BDS [°, mayor resolución]
        self.IAS: Optional[float] = None  # Indicated Airspeed [kt]
        self.MACH: Optional[float] = None  # Número de Mach
        self.BAR: Optional[float] = None  # Barometric Altitude Rate [ft/min]
        self.IVV: Optional[float] = None  # Inertial Vertical Velocity [ft/min]

        # --- I161 Track Number ---
        self.track_number: int = 0  # Número de pista radar

        # --- I230 Flight Status ---
        self.status: str = ""  # Estado del vuelo

        #Stereographical Coords added lately
        self.x:Optional[float] = None
        self.y:Optional[float] = None
        self.z:Optional[float] = None

def time_to_sec(time_string):
    parts = time_string.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])


def load_csv(file_path: str):

    #CARGA EL ARCHIVO CSV Y DEVUELVE UN VECTOR DE RECORDS

    df = pd.read_csv(file_path, sep=';', decimal=',')

    records = []

    for _, row in df.iterrows():
        rec = FlightRecord()

        # Mapeo de columnas básicas
        rec.cat = str(row['CAT'])
        rec.sac = int(row['SAC'])
        rec.sic = int(row['SIC'])

        # Tiempo (I140)
        rec.ToD_str = str(row['Time'])
        rec.ToD = time_to_sec(rec.ToD_str)

        # Coordenadas y Altitud
        rec.lat = row['LAT']
        rec.lon = row['LON']
        rec.h_m = row['H(m)']
        rec.h_ft = row['H(ft)']
        rec.FL = row['FL']

        # Radar (I040) e Identificación (I240)
        rec.rho = row['RHO']
        rec.theta = row['THETA']
        rec.mode3A = str(row['Mode3/A'])
        rec.callsign = str(row['TI'])
        rec.transponder = str(row['TA'])

        # BDS 4.0, 5.0, 6.0
        rec.BP = row['BP']
        rec.RA = row['RA']
        rec.TTA = row['TTA']
        rec.GS = row['GS']
        rec.GS_kt = row['GS(kt)']
        rec.TAR = row['TAR']
        rec.TAS = row['TAS']
        rec.HDG = row['HDG']
        rec.HDG_bds = row['HDG.1']
        rec.IAS = row['IAS']
        rec.MACH = row['MACH']
        rec.BAR = row['BAR']
        rec.IVV = row['IVV']

        # Track Number (I161) y Status (I230)
        rec.track_number = int(row['TN'])
        rec.status = str(row['STAT'])

        records.append(rec)

    return records

class Flight:
    """Corresponde a todos los records que pertenecen al mismo callsign"""
    def __init__(self, callsign: str = ""):
        self.callsign = callsign
        self.records: list[FlightRecord] = []

    def Add_record(self, record: FlightRecord):
        self.records.append(record)


def howManyAC(records):
    call = []
    ta =[]
    
    for i in records:
        if i.transponder not in ta:
            call.append(i.callsign)
            ta.append(i.transponder)
    return call


def Generate_Flights(records: list[FlightRecord]):
    # Crear un diccionario para agrupar records por callsign
    flights_dict = {}
    for i in records:
        callsign = i.callsign
        track_num = i.transponder
        if callsign not in flights_dict:
            flights_dict[callsign] = Flight(callsign)
            
        flights_dict[callsign].Add_record(i)
    return list(flights_dict.values())


def Flights_with_deadreckoning(flights):

    for flight in flights:
        new_record_list = []
        for i in range(len(flight.records) - 1):
            r = flight.records[i]
            r_next = flight.records[i+1]
            
            new_record_list.append(r)

            diff = int(r_next.ToD - r.ToD)
            if diff > 1:
                gs_kt = float(r.GS_kt)
                heading_deg = float(r.HDG_bds)
                try:
                    ivv = float(r.IVV)
                except ValueError:
                    ivv = ((float(r.h_ft) - float(r_next.h_ft)) / diff) * 60

                gs_nm_s = gs_kt/3600
                hdg_rad = np.radians(heading_deg)

                ivv = None
                if r.IVV is not None and not (isinstance(r.IVV, str) and str(r.IVV).strip() == ""):
                    try:
                        ivv = float(r.IVV)
                    except (TypeError, ValueError):
                        ivv = None

                if ivv is None:
                    if not pd.isna(r.h_ft) and not pd.isna(r_next.h_ft):
                        ivv = ((float(r.h_ft) - float(r_next.h_ft)) / diff) * 60
                    else:
                        ivv = 0.0

                ivv_s = ivv / 60

                for s in range(1,diff):
                    new_rec = FlightRecord()

                    dx = (gs_nm_s * np.sin(hdg_rad) * s)
                    dy = (gs_nm_s * np.cos(hdg_rad) * s)
                    dh = (ivv_s * s)

                    new_rec.x = r.x + dx
                    new_rec.y = r.y + dy
                    new_rec.h_ft = float(r.h_ft) + dh if not pd.isna(r.h_ft) else None
                    new_rec.ToD = r.ToD + s
                    new_rec.status = "PROJECTED"
                    new_rec.callsign = r.callsign

                    new_rec.lat, new_rec.lon = xy_to_latlon(new_rec.x, new_rec.y)

                    new_record_list.append(new_rec)
                
        new_record_list.append(flight.records[-1])

        flight.records = new_record_list

def Flights_with_deadreckoning2(flights):
    for flight in flights:
        
        ias_originales = [r.IAS for r in flight.records]
        
        ias_filtradas = pd.Series(ias_originales).interpolate(method='linear').bfill().ffill().tolist()
        
        for idx, nueva_ias in enumerate(ias_filtradas):
            
            flight.records[idx].IAS = nueva_ias if not pd.isna(nueva_ias) else None

        new_record_list = []
        
        for i in range(len(flight.records) - 1):
            r = flight.records[i]
            r_next = flight.records[i+1]
            
            # Añadimos el punto real actual
            new_record_list.append(r)

            diff = int(r_next.ToD - r.ToD)
            if diff > 1:
                # --- CALCULO DE PASOS UNITARIOS (POR SEGUNDO) ---
                # Delta de posiciones en las coordenadas del plano (x, y)
                dx_total = float(r_next.x) - float(r.x)
                dy_total = float(r_next.y) - float(r.y)
                
                dx_per_sec = dx_total / diff
                dy_per_sec = dy_total / diff

                # Delta de Altitud (Corregido el orden de la resta)
                if not pd.isna(r.h_ft) and not pd.isna(r_next.h_ft):
                    dh_per_sec = (float(r_next.h_ft) - float(r.h_ft)) / diff
                else:
                    dh_per_sec = 0.0

                # Delta de IAS (Velocidad Indicada)
                # Nos aseguramos de que ambos registros tengan IAS antes de interpolar
                has_ias = (r.IAS is not None and r_next.IAS is not None and 
                           not pd.isna(r.IAS) and not pd.isna(r_next.IAS))
                if has_ias:
                    dias_per_sec = (float(r_next.IAS) - float(r.IAS)) / diff
                else:
                    dias_per_sec = None

                # --- GENERACIÓN DE PUNTOS INTERMEDIOS ---
                for s in range(1, diff):
                    new_rec = FlightRecord() # Asegúrate de que esta clase esté disponible
                    
                    # Interpolación limpia (sin saltos al final del tramo)
                    new_rec.x = float(r.x) + (dx_per_sec * s)
                    new_rec.y = float(r.y) + (dy_per_sec * s)
                    
                    if not pd.isna(r.h_ft):
                        new_rec.h_ft = float(r.h_ft) + (dh_per_sec * s)
                    else:
                        new_rec.h_ft = None
                        
                    if has_ias:
                        new_rec.IAS = float(r.IAS) + (dias_per_sec * s)
                    else:
                        new_rec.IAS = r.IAS # Mantiene el valor original o None si no hay datos
                    
                    new_rec.ToD = r.ToD + s
                    new_rec.status = "INTERPOLATED"
                    new_rec.callsign = r.callsign

                    # Convertimos las nuevas x, y interpoladas a Lat/Lon para Google Earth
                    new_rec.lat, new_rec.lon = xy_to_latlon(new_rec.x, new_rec.y)

                    new_record_list.append(new_rec)
                
        # Añadimos el último registro del vuelo
        if flight.records:
            new_record_list.append(flight.records[-1])

        flight.records = new_record_list

def AddCoords(dictionary, coords):
    for i,flights in enumerate(dictionary):
        flights.x = coords[0][i]
        flights.y = coords[1][i]
        
