import numpy as np
from Pairs import Parameters, subParameters
from Flights import FlightRecord

def get_pos_1_sec(x_now, y_now, t_now, gs_kt, heading_deg):
    gs_nm_s = gs_kt / 3600
    rad = np.radians(heading_deg)
    for s in range(1, 4):
        f_rec = FlightRecord()
        dx = gs_nm_s * np.sin(heading_deg) * s
        dy = gs_nm_s * np.cos(heading_deg) * s

        f_rec.x = x_now + dx
        f_rec.y = y_now + dy
        f_rec.ToD = t_now + s