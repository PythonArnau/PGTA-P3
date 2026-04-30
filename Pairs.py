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
        self.geometric_values: list[subParameters] = []

class subParameters:
    def __init__(self):
        self.time: float = 0.0
        self.distance_nm: float = 0.0
        self.altitude_diff: float = 0.0
        self.distance_follower_tower_nm: float = 0.0
        self.ahead_or_behind_tower: str = ""

def LeaderFollower(flights):

    vuelos06R = []
    vuelos24L = []
    for f in flights:
        if f.runway == "LEBL-06R":
            vuelos06R.append(f)
        elif f.runway == "LEBL-24L":
            vuelos24L.append(f)
    
    vuelos_ordenados06 = sorted(vuelos06R, key=lambda f: f.departure_sec) #lambda lo que hace es especificar que para cada f de la lista los ordene por departure_sec
    vuelos_ordenados24 = sorted(vuelos24L, key=lambda f: f.departure_sec)

    pairs = []
    for i in range(len(vuelos_ordenados06)-1):
        leader = vuelos_ordenados06[i]
        follower = vuelos_ordenados06[i+1]

        pairs.append((leader, follower))
    
    for i in range(len(vuelos_ordenados24)-1):
        leader = vuelos_ordenados24[i]
        follower = vuelos_ordenados24[i+1]

        pairs.append((leader, follower))

    pairs_ordenadas = sorted(pairs, key=lambda p: p[0].departure_sec)

    return pairs_ordenadas


def GetParameteres(pairs, TWR06, TWR24):
    all_pairs = []
    for p in pairs:
        First = True
        param = Parameters()
        param.pair = p[0].callsign + "-" + p[1].callsign
        param.leader = p[0].callsign
        param.follower = p[1].callsign
        param.runway = p[0].runway
        param.sid_lead = p[0].sid
        param.sid_lead_group = p[0].sid_group
        param.sid_foll = p[1].sid
        param.sid_foll_group = p[1].sid_group

        time_leader = [rec.ToD for rec in p[0].records]
        x_leader = [rec.x for rec in p[0].records]
        y_leader = [rec.y for rec in p[0].records]
        h_ft_leader = [rec.h_ft for rec in p[0].records]

        for f_rec in p[1].records:
            #if f_rec.ToD <= time_leader[-1]:
                time_follower = f_rec.ToD
                x_follower = f_rec.x
                y_follower = f_rec.y
                h_follower = f_rec.h_ft

                #actual_leader_x = np.interp(time_follower, time_leader, x_leader)
                #actual_leader_y = np.interp(time_follower, time_leader, y_leader)
                #actual_leader_h = np.interp(time_follower, time_leader, h_ft_leader)

                f_x = interpolate.interp1d(time_leader, x_leader, fill_value="extrapolate", kind='linear')
                f_y = interpolate.interp1d(time_leader, y_leader, fill_value="extrapolate", kind='linear')
                f_z = interpolate.interp1d(time_leader, h_ft_leader, fill_value='extrapolate', kind='linear')

                actual_leader_x = f_x(time_follower)
                actual_leader_y = f_y(time_follower)
                actual_leader_h = f_z(time_follower)

                d_x = actual_leader_x - x_follower
                d_y = actual_leader_y - y_follower
                d_h = abs(actual_leader_h - h_follower)

                dist_m = np.sqrt(d_x ** 2 + d_y ** 2)
                dist_nm = dist_m / 1852

                if p[0].runway == "LEBL-06R":
                    TWRx = TWR06[0].U
                    TWRy = TWR06[0].V

                    d_xx = TWRx - x_follower

                    if TWRx > x_follower:
                        status = "BEHIND"
                    else:
                        status = "AHEAD"

                    d_yy = TWRy - y_follower

                    dist_mT = np.sqrt(d_xx ** 2 + d_yy ** 2)
                    dist_nmT = dist_mT / 1852

                    if dist_nmT >= 0.5 and status == "AHEAD" and First:
                        distTWRcalc = dist_nmT
                        TWR_hor_sep = dist_nm
                        TWR_alt_diff = d_h
                        First = False


                elif p[0].runway == "LEBL-24L":
                    TWRx = TWR24[0].U
                    TWRy = TWR24[0].V

                    d_xx = TWRx - x_follower

                    if TWRx < x_follower:
                        status = "BEHIND"
                    else:
                        status = "AHEAD"

                    d_yy = TWRy - y_follower

                    dist_mT = np.sqrt(d_xx ** 2 + d_yy ** 2)
                    dist_nmT = dist_mT / 1852

                    if dist_nmT >= 0.5 and status == "AHEAD" and First:
                        distTWRcalc = dist_nmT
                        TWR_hor_sep = dist_nm
                        TWR_alt_diff = d_h
                        First = False

                sub = subParameters()
                sub.time = float(time_follower)
                sub.distance_nm = float(dist_nm)
                sub.distance_follower_tower_nm = float(dist_nmT)
                sub.altitude_diff = float(d_h)
                sub.ahead_or_behind_tower = status
                param.geometric_values.append(sub)
        
        param.distTWR = float(distTWRcalc)
        param.TWR_dist_diff = float(TWR_hor_sep)
        param.TWR_alt_diff = float(TWR_alt_diff)

        all_pairs.append(param)

    return all_pairs


        







