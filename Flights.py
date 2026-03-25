from typing import Optional
import pandas as pd

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

def Generate_Flights(records: list[FlightRecord]):
    # Crear un diccionario para agrupar records por callsign
    flights_dict = {}
    for i in records:
        callsign = i.callsign
        if callsign not in flights_dict:
            flights_dict[callsign] = Flight(callsign)
        flights_dict[callsign].Add_record(i)
    return list(flights_dict.values())