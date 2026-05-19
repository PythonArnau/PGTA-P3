import numpy as np
import math
import pandas as pd
import latlon as ltln
from Flights import FlightRecord, Flight, load_csv, Generate_Flights, AddCoords, Flights_with_deadreckoning, howManyAC
from FlightPlan import FlightPlan, load_flightplan, obtain_callsigns, filter_flight, read_sids
from Asterix_pos import ExtractLatLonAlt, AddAsterixCSV
from Separation import get_consecutive_flights, calculate_separation
from Pairs import LeaderFollower2, GetParameters2
from Loss_of_separation import radar, wake_sep, LOA_sep, PrintResults
from Pos import Calc_Stereographical_Coords, TowerCoords
from geo_utils2 import latlon_to_xy
from collect_stats import getStatistics
from virajes import detect_turn, export_turns_to_excel, export_to_kml

# Cargar todos los records del CSV y generar flights
records = load_csv("P3_04h_08h.csv")

# Calcular las posiciones estereográficas teniendo como referencia el ARP LEBL
latv, lonv, altv = ExtractLatLonAlt(records)
#stereographCoord = Calc_Stereographical_Coords(latv,lonv,altv)
stereographCoord = latlon_to_xy(latv,lonv)
AddCoords(records, stereographCoord)
AddAsterixCSV("P3_04h_08h.csv", stereographCoord)

#Radardata, plandata = load_and_filter_data()

print(vars(records[0]))
AircS = howManyAC(records)

Flights = Generate_Flights(records)
Flights_interp = Flights_with_deadreckoning(Flights)

# Cargar planes de vuelo y eliminar vuelos que no hayan salido de LEBL
SIDs24L, SIDs06R = read_sids('Tabla_misma_SID_24L.xlsx', 'Tabla_misma_SID_06R.xlsx')
flight_plans = load_flightplan("P3_DEP_LEBL.xlsx", SIDs24L, SIDs06R)
AircsFP = [fp.callsign for fp in flight_plans]
AircsFPm = dict.fromkeys(AircsFP)
filtered_flights = filter_flight(Flights, flight_plans)

# Coordenadas de las torres
latTWR06 = 41 + 17/60 + 31.99/3600
lonTWR06 = 2 + 6/60 + 11.81/3600
TWR06R = latlon_to_xy(latTWR06, lonTWR06)

latTWR24 = 41 + 16/60 + 56.32/3600
lonTWR24 = 2 + 4/60 + 27.66/3600
TWR24L = latlon_to_xy(latTWR24, lonTWR24)

#nueva función para calcular las pairs en funcion de departure time y pista
pairs2 = LeaderFollower2(filtered_flights, TWR06R, TWR24L)
name_pairs = []
run = []
for p in pairs2:
    name = str(p[0].callsign) + "-" + str(p[1].callsign)
    rwy = str(p[0].runway + "-" + p[1].runway)
    run.append(rwy)
    name_pairs.append(name)
#distances_pairs = GetParameteres(pairs2, TWR06R, TWR24L)
distances_pairs = GetParameters2(pairs2, TWR06R, TWR24L)

"""
radar_separation_check = radar(distances_pairs)
wake_separation_check = wake_sep(distances_pairs)
loa_separation_check = LOA_sep(distances_pairs, "Tabla_Clasificacion_aeronaves.xlsx")
PrintResults("RadarSeparation.xlsx", radar_separation_check )
PrintResults("WakeSeparation.xlsx", wake_separation_check)
PrintResults("LOASeparation.xlsx", loa_separation_check)

getStatistics(radar_separation_check, wake_separation_check, loa_separation_check, distances_pairs, filtered_flights)
"""

#Turn Assessment
turns_list = detect_turn(filtered_flights, 1.5, 5)
export_turns_to_excel(turns_list,filename="assessment_virajes_LEBL.xlsx")
export_to_kml(turns_list, filename="puntos_viraje.kml")