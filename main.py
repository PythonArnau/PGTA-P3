import numpy as np
import math
import pandas as pd
import latlon as ltln
from Flights import FlightRecord, Flight, load_csv, Generate_Flights, AddCoords
from FlightPlan import FlightPlan, load_flightplan, obtain_callsigns, filter_flight, read_sids
from Asterix_pos import ExtractLatLonAlt, AddAsterixCSV
from Separation import get_consecutive_flights, calculate_separation
from Pairs import LeaderFollower, GetParameteres
from Loss_of_separation import radar, PrintResults
from Pos import Calc_Stereographical_Coords, TowerCoords

# Cargar todos los records del CSV y generar flights
records = load_csv("P3_04h_08h.csv")

# Calcular las posiciones estereográficas teniendo como referencia el ARP LEBL
latv, lonv, altv = ExtractLatLonAlt(records)
stereographCoord = Calc_Stereographical_Coords(latv,lonv,altv)
AddCoords(records, stereographCoord)
AddAsterixCSV("P3_04h_08h.csv", stereographCoord)

print(vars(records[0]))
Flights = Generate_Flights(records)

# Cargar planes de vuelo y eliminar vuelos que no hayan salido de LEBL
SIDs24L, SIDs06R = read_sids('Tabla_misma_SID_24L.xlsx', 'Tabla_misma_SID_06R.xlsx')
flight_plans = load_flightplan("P3_DEP_LEBL.xlsx", SIDs24L, SIDs06R)
filtered_flights = filter_flight(Flights, flight_plans)

# Coordenadas de las torres
latTWR06 = ltln.Latitude(degree=41, minute=17, second=31.99)
lonTWR06 = ltln.Longitude(degree=2, minute=6, second=11.81)
TWR06R = TowerCoords(latTWR06.decimal_degree, lonTWR06.decimal_degree)

latTWR24 = ltln.Latitude(degree=41, minute=16, second=56.32)
lonTWR24 = ltln.Longitude(degree=2, minute=4, second=27.66)
TWR24L = TowerCoords(latTWR24.decimal_degree, lonTWR24.decimal_degree)

#nueva función para calcular las pairs en funcion de departure time y pista
pairs2 = LeaderFollower(filtered_flights)
distances_pairs = GetParameteres(pairs2, TWR06R, TWR24L)
radar_separation_check = radar(distances_pairs)
PrintResults("RadarSeparation.xlsx", radar_separation_check )

#manera antigua de calcular las pairs
pairs = get_consecutive_flights(flight_plans)
flights_dict = {f.callsign: f for f in filtered_flights}
#print(f"Total de vuelos con datos radar: {len(flights_dict)}")

all_separations = []
for leader_fp, follower_fp in pairs:
    if leader_fp.callsign in flights_dict and follower_fp.callsign in flights_dict:
        leader_flight = flights_dict[leader_fp.callsign]
        follower_flight = flights_dict[follower_fp.callsign]
        separation = calculate_separation(leader_fp, follower_fp,leader_flight, follower_flight, TWR06R, TWR24L)
        all_separations.append(separation)

print(vars(all_separations[0]))