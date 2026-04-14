import pandas as pd
import re
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
        self.sid_group: str = ""


def timedelta_to_sec(td) -> int:
    """Convierte un timedelta (formato Excel) a segundos desde medianoche."""
    return int(td.total_seconds())


def timedelta_to_str(td) -> str:
    """Convierte un timedelta a string 'HH:MM:SS'."""
    total = int(td.total_seconds())
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"  

def read_sids(file_path24: str, file_path06: str):
    p24 = pd.read_excel(file_path24)
    p06 = pd.read_excel(file_path06)

    SID_G1_24 = p24['Misma_SID_G1'].dropna().tolist()
    SID_G2_24 = p24['Misma_SID_G2'].dropna().tolist()
    SID_G3_24 = p24['Misma_SID_G3'].dropna().tolist()

    SIDs_24L = {
        'G1': SID_G1_24,
        'G2': SID_G2_24,
        'G3': SID_G3_24
    }

    SID_G1_06 = p06['Misma_SID_G1'].dropna().tolist()
    SID_G2_06 = p06['Misma_SID_G2'].dropna().tolist()
    SID_G3_06 = p06['Misma_SID_G3'].dropna().tolist()

    SIDs_06R = {
        'G1': SID_G1_06,
        'G2': SID_G2_06,
        'G3': SID_G3_06
    }
    return(SIDs_24L, SIDs_06R)

def load_flightplan(file_path: str, sids24, sids06):
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
        fp.runway = str(row['PistaDesp']).strip()
        #print(repr(fp.runway))
        #print(repr(str(row['ProcDesp']).strip()))

        if str(row['ProcDesp']).strip() == '-':     # Esto básicamente busca si un punto de la ruta coincide con el nombre de alguna SID.
            if fp.runway == 'LEBL-24L':             # Al encontrar el primer punto que cumpla esto guardamos resultados (SID, grupo)
                words = fp.route.strip().split()
                found = False
                for word in words:
                    remove_par = re.search(r'\((\w+)\)', word)
                    if remove_par:
                        word = remove_par.group(1)
                    for group, list in sids24.items():
                        for s in list:
                            if s.split('-')[0] == word:
                                #print(f"ENCONTRADO: {s} en {group}")
                                fp.sid = str(s)
                                fp.sid_group = str(group)
                                found = True
                            if found: break
                        if found: break
                    if found: break           
            
            elif fp.runway == 'LEBL-06R':
                words = fp.route.strip().split()
                found = False
                for word in words:
                    remove_par = re.search(r'\((\w+)\)', word)
                    if remove_par:
                        word = remove_par.group(1)

                    for group, list in sids06.items():
                        for s in list:
                            if s.split('-')[0] == word:
                                #print(f"ENCONTRADO: {s} en {group}")
                                fp.sid = str(s)
                                fp.sid_group = str(group)
                                found = True
                            if found: break
                        if found: break
                    if found: break
        else:                                               # Para las que ya tengan SID, hacemos lo mismo pero para determinar
            fp.sid = str(row['ProcDesp']).strip()           # el grupo de sid al que pertenece.

            if fp.runway == 'LEBL-24L':
                found = False
                for group, list in sids24.items():
                    for s in list:
                        s = s.replace('-','1')
                        if s == fp.sid:
                            fp.sid = str(s)
                            fp.sid_group = str(group)
                            found = True
                            break  
                    if found: break
            
            if fp.runway == 'LEBL-06R':
                found = False
                for group, list in sids06.items():
                    for s in list:
                        s = s.replace('-','1')
                        if s == fp.sid:
                            fp.sid = s
                            fp.sid_group = str(group)
                            found = True
                            break  
                    if found: break
            
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

    departure_times = {fp.callsign: fp.departure_sec for fp in flight_plans}
    runways = {fp.callsign: fp.runway for fp in flight_plans}
    routes = {fp.callsign: fp.route for fp in flight_plans}
    sids = {fp.callsign: fp.sid for fp in flight_plans}
    sid_groups = {fp.callsign: fp.sid_group for fp in flight_plans}
    wakes = {fp.callsign: fp.wake for fp in flight_plans}
    wake_recars = {fp.callsign: fp.wake_recar for fp in flight_plans}

    for f in flights_vec:
        cs = f.callsign
        if cs in callsings_vec and (runways[cs] == "LEBL-24L" or runways[cs] == "LEBL-06R"):
            #Le añado el departure time,... para usarlo más tarde
            f.departure_sec = departure_times[cs]
            f.route = routes[cs]
            f.sid = sids[cs]
            f.runway = runways[cs]
            f.sid_group = sid_groups[cs]
            f.wake = wakes[cs]
            f.wake_recar = wake_recars[cs]

            filt_flights_vec.append(f)
    return filt_flights_vec
