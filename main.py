import numpy as np
import math
import pandas as pd
from openpyxl import Workbook

import threshold
from Flights import FlightRecord, Flight, load_csv, Generate_Flights, AddCoords, Flights_with_deadreckoning, Flights_with_deadreckoning2, howManyAC
from FlightPlan import FlightPlan, load_flightplan, obtain_callsigns, filter_flight, read_sids
from Asterix_pos import ExtractLatLonAlt, AddAsterixCSV
from Separation import get_consecutive_flights, calculate_separation
from Pairs import LeaderFollower2, GetParameters2
from Loss_of_separation import radar, wake_sep, LOA_sep, PrintResults, export_combined_separation_excel
from Pos import Calc_Stereographical_Coords, TowerCoords
from geo_utils2 import latlon_to_xy
from collect_stats import getStatistics
from printTWRpos import export2kml, exportFlightPaths2kml
from stats import count_airlines_unique, TMA_TWR_airlines, count_AC, TMA_TWR_AC, countWake, TMA_TWR_wake, countLOA, LOA_TWR
from getexcel import getKPIs
from NADP import NADP_definition
from virajes import detect_turn, export_turns_to_excel, export_to_kml
from threshold import detect_threshold, export_threshold_excel, export_threshold_kml, export_threshold_excel

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
Flights_interp = Flights_with_deadreckoning2(Flights)

# Cargar planes de vuelo y eliminar vuelos que no hayan salido de LEBL
SIDs24L, SIDs06R = read_sids('Tabla_misma_SID_24L.xlsx', 'Tabla_misma_SID_06R.xlsx')
flight_plans = load_flightplan("P3_DEP_LEBL.xlsx", SIDs24L, SIDs06R)
AircsFP = [fp.callsign for fp in flight_plans]
AircsFPm = dict.fromkeys(AircsFP)
filtered_flights = filter_flight(Flights, flight_plans)

NADP_results, discarted_NADP = NADP_definition(filtered_flights)
df = pd.DataFrame(NADP_results)
df.to_excel("NADP_results.xlsx", index=False)
exportFlightPaths2kml("Fligths.kml", filtered_flights)

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
export2kml('TWRdetect.kml', distances_pairs, latTWR06, lonTWR06, latTWR24, lonTWR24)

radar_separation_check = radar(distances_pairs)
wake_separation_check = wake_sep(distances_pairs)
loa_separation_check = LOA_sep(distances_pairs, "Tabla_Clasificacion_aeronaves.xlsx")
PrintResults("RadarSeparation.xlsx", radar_separation_check )
PrintResults("WakeSeparation.xlsx", wake_separation_check)
PrintResults("LOASeparation.xlsx", loa_separation_check)
export_combined_separation_excel(
    "CombinedSeparation.xlsx",
    distances_pairs,
    radar_separation_check,
    wake_separation_check,
    loa_separation_check,
)


#Turn Assessment
turns_list = detect_turn(filtered_flights, 1.5, 5)
export_turns_to_excel(turns_list,filename="assessment_virajes_LEBL.xlsx")
export_to_kml(turns_list, filename="puntos_viraje.kml")

threshold_list = detect_threshold(filtered_flights)
export_threshold_excel(threshold_list, filepath="assessment_threshold_LEBL.xlsx")
export_threshold_kml(threshold_list, filepath="puntos_threshold.kml")

"""
airlines = count_airlines_unique(pairs2)
TMA_rad_airl, TWR_rad_airl = TMA_TWR_airlines(radar_separation_check, airlines)
TMA_wake_airl, TWR_wake_airl = TMA_TWR_airlines(wake_separation_check, airlines)
TMA_loa_airl, TWR_loa_airl = TMA_TWR_airlines(loa_separation_check, airlines)

ACs = count_AC(filtered_flights)
TMA_rad_ac, TWR_rad_ac = TMA_TWR_AC(filtered_flights, radar_separation_check, ACs)
TMA_wake_ac, TWR_wake_ac = TMA_TWR_AC(filtered_flights, wake_separation_check, ACs)
TMA_loa_ac, TWR_loa_ac = TMA_TWR_AC(filtered_flights, loa_separation_check, ACs)

wake_class, wake_class_pairs = countWake(pairs2)
wake_class_TMA, wake_class_pair_TMA, wake_class_TWR, wake_class_pair_TWR, wake_sep, wake_sep_TMA, wake_sep_TWR = TMA_TWR_wake(wake_separation_check, wake_class, wake_class_pairs)

loa_class, loa_class_pair, sids, sids_pair, min_sep = countLOA(loa_separation_check)
loa_TWR_class, loa_TWR_pair_class, sids_TWR, sids_pair_TWR, min_sep_TWR = LOA_TWR(loa_separation_check, loa_class, loa_class_pair, sids, sids_pair, min_sep)

wb = Workbook()
ws = wb.active

dicts = [
    ("airlines", airlines),
    ("TMA_rad_airl", TMA_rad_airl),
    ("TWR_rad_airl", TWR_rad_airl),
    ("TMA_wake_airl", TMA_wake_airl),
    ("TWR_wake_airl", TWR_wake_airl),
    ("TWR_loa_airl", TWR_loa_airl),

    ("ACs", ACs),
    ("TMA_rad_ac", TMA_rad_ac),
    ("TWR_rad_ac", TWR_rad_ac),
    ("TMA_wake_ac", TMA_wake_ac),
    ("TWR_wake_ac", TWR_wake_ac),
    ("TWR_loa_ac", TWR_loa_ac),

    ("wake_class", wake_class),
    ("wake_class_pairs", wake_class_pairs),
    ("wake_class_TMA", wake_class_TMA),
    ("wake_class_pair_TMA", wake_class_pair_TMA),
    ("wake_class_TWR", wake_class_TWR),
    ("wake_class_pair_TWR", wake_class_pair_TWR),
    ("wake_sep", wake_sep),
    ("wake_sep_TMA", wake_sep_TMA),
    ("wake_sep_TWR", wake_sep_TWR),

    ("loa_class", loa_class),
    ("loa_class_pair", loa_class_pair),
    ("sids", sids),
    ("sids_pair", sids_pair),
    ("min_sep", min_sep),

    ("loa_TWR_class", loa_TWR_class),
    ("loa_TWR_pair_class", loa_TWR_pair_class),
    ("sids_TWR", sids_TWR),
    ("sids_pair_TWR", sids_pair_TWR),
    ("min_sep_TWR", min_sep_TWR)
]

getKPIs(dicts, ws)

wb.save("KPIs.xlsx")"""

