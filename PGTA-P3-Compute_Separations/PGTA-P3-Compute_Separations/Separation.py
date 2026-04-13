import math

import numpy as np

from FlightPlan import FlightPlan
from Flights import FlightRecord,Flight

class SeparationSample:
    "Separacion entre dos vuelos en un sample"
    def __init__(self):
        self.relative_time: float = 0.0     #Tiempo relativo entre primer y segundo vuelo
        self.dist_m: float = 0.0            #Distancia en metros
        self.dist_nm: float = 0.0           #Distancia en millas náuticas
        self.diff_alt_ft: float = 0.0
        

class FlightPairSeparation:
    "Separacion completa entre dos vuelos"
    def __init__(self):
        self.runway: str = ""
        self.leader_callsign: str = ""
        self.follower_callsign: str = ""
        self.leader_atot: int = 0
        self.follower_atot: int = 0
        self.samples: list[SeparationSample] = []

def get_consecutive_flights(flight_plans: list[FlightPlan]):
    "Obtiene lista de vuelos consecutivos"
    runways = {}
    #Obtener lista de runways (06L y 24R)
    for fp in flight_plans:
        if fp.runway not in runways:
            runways[fp.runway] = []
        runways[fp.runway].append(fp)

    pairs = []
    for rwy, fps in runways.items():
        # Ordenar los vuelos de esta pista por su hora de despegue
        fps.sort(key=lambda x: x.departure_sec)
        # Crear pares (líder, seguidor)
        for i in range(len(fps) - 1):
            pairs.append((fps[i], fps[i + 1]))

    return pairs

def calculate_separation(leader_fp: FlightPlan, follower_fp: FlightPlan, leader_flight: Flight, follower_flight: Flight):
    pair_separation = FlightPairSeparation()
    pair_separation.runway = leader_fp.runway
    pair_separation.leader_callsign = leader_fp.callsign
    pair_separation.follower_callsign = follower_fp.callsign
    pair_separation.leader_atot = leader_fp.departure_sec
    pair_separation.follower_atot = follower_fp.departure_sec
    

    #Extaer reecords
    leader_recs = leader_flight.records
    follower_recs = follower_flight.records

    #Evitar errores
    if not leader_recs or not follower_recs:
        return pair_separation

    #Extraer vectores tiempo y posicion del lider de los records
    leader_times = [rec.ToD for rec in leader_recs]
    leader_x = [rec.x for rec in leader_recs]
    leader_y = [rec.y for rec in leader_recs]
    leader_alts = [rec.h_ft for rec in leader_recs]
    
    for f_rec in follower_recs:
        
        t = f_rec.ToD
        #Interpolar posiciones
        inter_x = np.interp(t, leader_times, leader_x)
        inter_y = np.interp(t, leader_times, leader_y)
        inter_alt_leader = np.interp(t, leader_times, leader_alts)
        alt_follower = f_rec.h_ft
        vertical_diff = abs(inter_alt_leader - alt_follower)

        #Calculo distancias
        d_x = inter_x - f_rec.x
        d_y = inter_y - f_rec.y
        dist_m = math.sqrt(d_x**2 + d_y**2)
        dist_nm = dist_m / 1852.0

        #Crear sample
        sample = SeparationSample()
        sample.relative_time = t - follower_fp.departure_sec
        sample.dist_m = dist_m
        sample.dist_nm = dist_nm
        sample.diff_alt_ft = float(vertical_diff)
        pair_separation.samples.append(sample)


    return pair_separation


