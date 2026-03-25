import numpy as np
import math
import pandas as pd
from Flights import FlightRecord, Flight, load_csv, Generate_Flights
from FlightPlan import FlightPlan, load_flightplan, obtain_callsigns, filter_flight

# Cargar todos los records del CSV y generar flights
records = load_csv("P3_04h_08h.csv")
Flights = Generate_Flights(records)

# Cargar planes de vuelo y eliminar vuelos que no hayan salido de LEBL
flight_plans = load_flightplan("P3_DEP_LEBL.xlsx")
filtered_flights = filter_flight(Flights, flight_plans)


