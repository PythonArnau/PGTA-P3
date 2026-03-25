import pandas as pd
import Flights

class FlightPlan:
    def __init__(self):
        self.id: int = 0
        self.callsign: str = ""
        self.destination: str = ""
        self.departure: str = ""
        self.departure_sec: int = 0
        self.route: str = ""
        self.aircraft: str = ""
        self.wake: str = ""
        self.wake_recar: str = ""
        self.sid: str = ""
        self.runway: str = ""


def timedelta_to_sec(td) -> int:
    """Convierte un timedelta (formato Excel) a segundos desde medianoche."""
    return int(td.total_seconds())


def timedelta_to_str(td) -> str:
    """Convierte un timedelta a string 'HH:MM:SS'."""
    total = int(td.total_seconds())
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def load_flightplan(file_path: str):
    """
    Carga planes de vuelo desde un fichero Excel (.xlsx).
    Columnas esperadas: id, Indicativo, Origen, Destino, HoraDespegue,
                        RutaSACTA, TipoAeronave, Estela, EstelaRECAT,
                        ProcDesp, ATOT, PistaDesp
    """
    df = pd.read_excel(file_path)

    flight_plans = []

    for _, row in df.iterrows():
        fp = FlightPlan()
        fp.id = row['id']
        fp.callsign = str(row['Indicativo']).strip()
        fp.destination = str(row['Destino']).strip()
        fp.departure = timedelta_to_str(row['HoraDespegue'])
        fp.departure_sec = timedelta_to_sec(row['HoraDespegue'])
        fp.route = str(row['RutaSACTA']).strip()
        fp.aircraft = str(row['TipoAeronave']).strip()
        fp.wake = str(row['Estela']).strip()
        fp.wake_recar = str(row['EstelaRECAT']).strip()
        fp.sid = str(row['ProcDesp']).strip()
        fp.runway = str(row['PistaDesp']).strip()

        flight_plans.append(fp)

    return flight_plans

def obtain_callsigns(flight_plans):
    """Obtiene vector de los callsigns de los planes de vuelo"""
    callsigns_vec = []
    for fp in flight_plans:
        cs = fp.callsign
        if cs not in callsigns_vec:
            callsigns_vec.append(cs)
    return callsigns_vec

def filter_flight(flights_vec, flight_plans):
    filt_flights_vec = []
    callsings_vec = obtain_callsigns(flight_plans)
    for fp in flights_vec:
        cs = fp.callsign
        if cs in callsings_vec:
            filt_flights_vec.append(fp)
    return filt_flights_vec
