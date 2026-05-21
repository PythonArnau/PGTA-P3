import numpy as np
from scipy import interpolate

class Parameters:
    def __init__(self):
        self.pair: str = ""
        self.leader: str = ""
        self.sid_lead: str = ""
        self.sid_lead_group: str = ""
        self.follower: str = ""
        self.sid_foll: str = ""
        self.sid_foll_group: str = ""
        self.runway: str = ""
        self.distTWR: float = 0.0
        self.TWR_dist_diff: float = 0.0
        self.TWR_alt_diff: float = 0.0
        self.TWR_time: float = 0.0
        self.TMA_dist: float = 0.0
        self.TMA_alt: float = 0.0
        self.TMA_time: float = 0.0
        self.wake_lead: str = ""
        self.wake_foll: str = ""
        self.AC_lead: str = ""
        self.AC_foll: str = ""
        self.lat05_f: float = 0.0
        self.lon05_f: float = 0.0


def _same_sid_group(leader, follower):
    return leader.sid_group and follower.sid_group and leader.sid_group == follower.sid_group


def temporalOverlap(pair, twr):
    detection = first_detection_at_05NM(pair, twr)
    if detection:
        t = detection[0]
        tL_end = pair[0].records[-1].ToD
        return t < tL_end
    return False


def LeaderFollower2(flights, TWR06, TWR24):

    runways = {}
    for f in flights:
        runways.setdefault(f.runway, []).append(f)
    
    pairs = []
    for runway, runway_flights in runways.items():
        print(runway)
        runway_flights_sorted = sorted(runway_flights, key=lambda fl: fl.departure_sec)
        twr = TWR06 if runway == "LEBL-06R" else TWR24

        for i in range(len(runway_flights_sorted)-1):
            current_flight = runway_flights_sorted[i]
            next_flight = runway_flights_sorted[i + 1]
            #if temporalOverlap((current_flight, next_flight), twr):
            pairs.append((current_flight, next_flight))
    
    pairs_sorted = sorted(pairs, key=lambda pa: pa[0].departure_sec)

    return pairs_sorted


def LeaderFollower(flights):

    runways = {}
    for f in flights:
        runways.setdefault(f.runway, []).append(f)
    
    pairs = []
    for runway, runway_flights in runways.items():
        print(runway)
        runway_flights_sorted = sorted(runway_flights, key=lambda fl: fl.departure_sec)

        for i in range(len(runway_flights_sorted)-1):
            current_flight = runway_flights_sorted[i]
            next_flight = runway_flights_sorted[i + 1]
            if temporalOverlap(current_flight, next_flight):
                pairs.append((current_flight, next_flight))
    
    pairs_sorted = sorted(pairs, key=lambda pa: pa[0].departure_sec)

    return pairs_sorted
        

def first_detection_at_05NM(pair, twr):
    tx, ty = twr
    dist =[np.sqrt((r.x - tx)**2 + (r.y - ty)**2) for r in pair[1].records]

    for i in range(len(dist) - 1):
        if dist[i] < 0.5 <= dist[i+1]:
            frac = (0.5 - dist[i]) / (dist[i+1] - dist[i])
            
            times_f = [rec.ToD for rec in pair[1].records]
            t = times_f[i] + frac * (times_f[i + 1] - times_f[i])

            x_f = [rec.x for rec in pair[1].records]
            y_f = [rec.y for rec in pair[1].records]
            h_f = [rec.h_ft for rec in pair[1].records]
            lat_f = [rec.lat for rec in pair[1].records]
            lon_f = [rec.lon for rec in pair[1].records]

            x = x_f[i] + frac * (x_f[i + 1] - x_f[i])
            y = y_f[i] + frac * (y_f[i + 1] - y_f[i])
            h = h_f[i] + frac * (h_f[i + 1] - h_f[i])
            lat = lat_f[i] + frac * (lat_f[i + 1] - lat_f[i])
            lon = lon_f[i] + frac * (lon_f[i + 1] - lon_f[i])
            return t, x, y, h, lat, lon
        
    return None


def GetParameters2(pairs, TWR06, TWR24):
    
    all_pairs = []
    
    for p in pairs:
        param = Parameters()
        param.pair = p[0].callsign + "-" + p[1].callsign
        param.leader = p[0].callsign
        param.follower = p[1].callsign
        param.runway = p[0].runway
        param.sid_lead = p[0].sid
        param.sid_lead_group = p[0].sid_group
        param.sid_foll = p[1].sid
        param.sid_foll_group = p[1].sid_group
        param.wake_lead = p[0].wake
        param.wake_foll = p[1].wake
        param.AC_lead = p[0].aircraft
        param.AC_foll = p[1].aircraft
        
        twr = TWR06 if p[0].runway == "LEBL-06R" else TWR24
        tx, ty = twr
        
        detection_05 = first_detection_at_05NM(p, twr)
        if not detection_05:
            param.TWR_dist_diff = None
            param.TWR_alt_diff = None
            param.TWR_time = None
            param.TMA_dist = None
            param.TMA_alt = None
            param.TMA_time = None
            all_pairs.append(param)
            continue  # Sin detección a 0.5 NM, saltar pareja
        
        t_05, x_05, y_05, h_05, lat_05, lon_05 = detection_05
        param.lat05_f = lat_05
        param.lon05_f = lon_05
        tL_end = p[0].records[-1].ToD
        
        time_leader = [rec.ToD for rec in p[0].records]
        x_leader = [rec.x for rec in p[0].records]
        y_leader = [rec.y for rec in p[0].records]
        h_ft_leader = [rec.h_ft for rec in p[0].records]
        
        f_x = interpolate.interp1d(time_leader, x_leader, fill_value="extrapolate", kind='linear')
        f_y = interpolate.interp1d(time_leader, y_leader, fill_value="extrapolate", kind='linear')
        f_z = interpolate.interp1d(time_leader, h_ft_leader, fill_value='extrapolate', kind='linear')

        if t_05 <= tL_end:
            lx_05 = f_x(t_05)
            ly_05 = f_y(t_05)
            lh_05 = f_z(t_05)
            
            dist_at_05 = np.sqrt((lx_05 - x_05)**2 + (ly_05 - y_05)**2)
            alt_at_05 = abs(lh_05 - h_05)
            
            param.distTWR = 0.5
            param.TWR_dist_diff = dist_at_05
            param.TWR_alt_diff = alt_at_05
            param.TWR_time = t_05
        
        else:
            param.distTWR = 0.5
            param.TWR_dist_diff = None
            param.TWR_alt_diff = None
            param.TWR_time = t_05
        
        min_dist = float("inf")
        min_alt = None
        min_time = None

        if p[0].callsign == "VLG4SW":
            print("hols")
            
        for f_rec in p[1].records:
            t_follower = f_rec.ToD
            if t_follower == 18943:
                print("hols")
            
            if t_05 < t_follower <= tL_end:
                x_follower = f_rec.x
                y_follower = f_rec.y
                h_follower = f_rec.h_ft
                
                lx = f_x(t_follower)
                ly = f_y(t_follower)
                lh = f_z(t_follower)
                
                d_x = lx - x_follower
                d_y = ly - y_follower
                d_h = abs(lh - h_follower)
                dist_nm = np.sqrt(d_x ** 2 + d_y ** 2)
                
                dist_foll_twr = np.sqrt((tx - x_follower)**2 + (ty - y_follower)**2)
                
                if dist_nm < min_dist:
                    min_dist = dist_nm
                    min_alt = d_h
                    min_time = t_follower

        if min_time == None:
            min_dist = None
          
        param.TMA_dist = min_dist
        param.TMA_alt = min_alt
        param.TMA_time = min_time
        
        all_pairs.append(param)
    
    return all_pairs









