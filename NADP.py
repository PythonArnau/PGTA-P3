import matplotlib.pyplot as plt
import numpy as np
from Loss_of_separation import to_hhmmss


def get_IAS_at_x(flight, alt):
    desired_IAS = None
    time = None
    
    alt_f = [float(rec.h_ft) for rec in flight.records]
    ias_f = [float(rec.IAS) for rec in flight.records]

    time_f = [rec.ToD for rec in flight.records]

    for i in range(len(flight.records)-1):

        if alt_f[i] is None or alt_f[i+1] is None or ias_f[i] is None or ias_f[i+1] is None:
            continue

        if alt_f[i+1] == alt_f[i]: 
            continue
        
        if alt_f[i] < alt <= alt_f[i+1]:
            frac = (alt - alt_f[i]) / (alt_f[i+1] - alt_f[i])

            alt_ias = ias_f[i] + frac * (ias_f[i + 1] - ias_f[i])
            desired_IAS = alt_ias

            time = time_f[i] + frac * (time_f[i + 1] - time_f[i])
            time = to_hhmmss(time)

            return desired_IAS, time, alt
    return desired_IAS, time, alt
        

def NADP_definition(flights):

    threshold = 15

    IAS_at_800 = []
    time_at_800 = []
    alt_at_800 = []
    IAS_at_3000 = []
    time_at_3000 = []
    alt_at_3000 = []

    Delta_IAS = []
    NADP_dep = []
    Dep_time = []
    sid = []
    sid_g = []
    wake = []
    aircraft = []

    callsings = []
    discarted_flights = []

    for f in flights:
        IAS_800, time_800, alt_800 = get_IAS_at_x(f, 800)
        IAS_3000, time_3000, alt_3000 = get_IAS_at_x(f, 3000)

        if IAS_800 is not None and IAS_3000 is not None:
            IAS_at_800.append(IAS_800)
            time_at_800.append(time_800)
            alt_at_800.append(alt_800)
            IAS_at_3000.append(IAS_3000)
            time_at_3000.append(time_3000)
            alt_at_3000.append(alt_3000)
            callsings.append(f.callsign)

            d_IAS = IAS_3000 - IAS_800
            Delta_IAS.append(d_IAS)

            if abs(d_IAS) < threshold:
                NADP_dep.append("NADP 1")

            else:
                NADP_dep.append("NADP 2")

            sid.append(f.sid)
            sid_g.append(f.sid_group)
            dep_str = to_hhmmss(f.departure_sec)
            Dep_time.append(dep_str)
            wake.append(f.wake)
            aircraft.append(f.aircraft)
        
        else:
            discarted_flights.append(f.callsign)
            pass

    plt.figure()

    plt.bar(callsings, Delta_IAS)

    plt.title("NADP IAS comparison")
    plt.show()

    thres_dup = [threshold for fl in Delta_IAS]

    NADP_full_info = {
        "Callsign": callsings,
        "Departure Time": Dep_time,
        "SID": sid,
        "SID group": sid_g,
        "Wake": wake,
        "Aircraft": aircraft,
        "IAS 800ft": IAS_at_800,
        "Time IAS800": time_at_800,
        "Altitude IAS800": alt_at_800,
        "IAS 3000ft": IAS_at_3000,
        "Time IAS3k": time_at_3000,
        "Altitude IAS3k": alt_at_3000,
        "\u0394 IAS": Delta_IAS,
        "Threshold": thres_dup,
        "NADP Type": NADP_dep
    }


    return NADP_full_info, discarted_flights
