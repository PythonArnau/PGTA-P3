import numpy as np
import math
import pandas as pd
from Flights import FlightRecord, Flight, load_csv, Generate_Flights, AddCoords
from FlightPlan import FlightPlan, load_flightplan, obtain_callsigns, filter_flight, read_sids
from Asterix_pos import Calc_Stereographical_Coords, ExtractLatLonAlt, AddAsterixCSV

# Cargar todos los records del CSV y generar flights
records = load_csv("P3_04h_08h.csv")
print(vars(records[0]))
Flights = Generate_Flights(records)

# Cargar planes de vuelo y eliminar vuelos que no hayan salido de LEBL
SIDs24L, SIDs06R = read_sids('Tabla_misma_SID_24L.xlsx', 'Tabla_misma_SID_06R.xlsx')
flight_plans = load_flightplan("P3_DEP_LEBL.xlsx", SIDs24L, SIDs06R)
filtered_flights = filter_flight(Flights, flight_plans)

# Calcular las posiciones estereográficas teniendo como referencia el ARP LEBL
latv, lonv, altv = ExtractLatLonAlt(records)
stereographCoord = Calc_Stereographical_Coords(latv,lonv,altv)
AddCoords(records, stereographCoord)
AddAsterixCSV("P3_04h_08h.csv", stereographCoord)



