import numpy as np
import math
import pandas as pd
from Flights import FlightRecord, Flight, load_csv, Generate_Flights

# Cargar todos los records del CSV y generar flights
records = load_csv("P3_04h_08h.csv")
Flights = Generate_Flights(records)

