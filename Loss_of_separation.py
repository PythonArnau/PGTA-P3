import pandas as pd
import numpy as np
import datetime


class SeparationLoss:
    def __init__(self):
        self.loss_details: str = ""
        self.time: str = ""
        self.horizontal_separation_nm: float = 0.0
        self.altitude_separation_ft: float = 0.0


class TmaLoss(SeparationLoss):
    pass                            #Con esto decimos que no añadimos nada más sinó que usamos los campos de SeparationLoss


class TwrLoss(SeparationLoss):
    def __init__(self):
        super().__init__()                      #Con esto decimos que le añadimos el campo de abajo a los campos de SeparationLoss
        self.distance_twr_nm: float = 0.0


class Separation:
    def __init__(self):
        self.pair: str = ""
        self.runway: str = ""
        self.tma_loss: str = "NO"
        self.twr_loss: str = "NO"
        self.tma_details: list[TmaLoss] = []
        self.twr_details: list[TwrLoss] = []

class Wake_sep(Separation):
    def __init__(self):
        super().__init__()
        self.wake_lead: str = ""
        self.wake_foll: str = ""
        self.min_hor_sep: float = 0.0

class LOA_separation(Separation):
    def __init__(self):
        super().__init__()
        del self.tma_loss
        del self.tma_details

        self.lead_class: str = ""
        self.foll_class: str = ""
        self.min_hor_sep: float = 0.0


def to_hhmmss(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))


def radar(flights):
    results = []

    for pair in flights:
        pair_flights = Separation()
        pair_flights.pair = pair.pair
        pair_flights.runway = pair.runway
        pair_flights.sid_lead = pair.sid_lead
        pair_flights.sid_lead_g = pair.sid_lead_group
        pair_flights.sid_foll = pair.sid_foll
        pair_flights.sid_foll_g = pair.sid_foll_group

        if pair.TMA_dist is not None and pair.TMA_dist < 3:
            pair_flights.tma_loss = "YES"

            tma_event = TmaLoss()
            tma_event.time = to_hhmmss(pair.TMA_time)
            tma_event.horizontal_separation_nm = float(pair.TMA_dist)
            tma_event.altitude_separation_ft = float(pair.TMA_alt)
            tma_event.loss_details = (
                "HORIZONTAL SEPARATION"
                if pair.TMA_alt >= 1000
                else "OPERATIONAL SEPARATION"
            )
            pair_flights.tma_details.append(tma_event)

        elif pair.TMA_dist is not None and pair.TMA_dist > 3:
            pair_flights.tma_loss = "NO"

            tma_event = TmaLoss()
            tma_event.time = to_hhmmss(pair.TMA_time)
            tma_event.horizontal_separation_nm = float(pair.TMA_dist)
            tma_event.altitude_separation_ft = float(pair.TMA_alt)
            tma_event.loss_details = ""
            pair_flights.tma_details.append(tma_event)
        
        elif pair.TMA_dist is None:
            pair_flights.tma_loss = "NO"

            tma_event = TmaLoss()
            tma_event.loss_details = "LEADER OUT OF GEO FILTER"
            tma_event.horizontal_separation_nm = None
            tma_event.altitude_separation_ft = None
            tma_event.time = None

            pair_flights.tma_details.append(tma_event)
            

        if pair.TWR_dist_diff is not None and pair.TWR_dist_diff < 3:
            pair_flights.twr_loss = "YES"

            twr_event = TwrLoss()
            twr_event.time = to_hhmmss(pair.TWR_time)
            twr_event.horizontal_separation_nm = float(pair.TWR_dist_diff)
            twr_event.altitude_separation_ft = float(pair.TWR_alt_diff)
            twr_event.distance_twr_nm = float(pair.distTWR)
            twr_event.loss_details = (
                "HORIZONTAL SEPARATION"
                if pair.TWR_alt_diff >= 1000
                else "OPERATIONAL SEPARATION"
            )
            pair_flights.twr_details.append(twr_event)
        
        elif pair.TWR_dist_diff is not None and pair.TWR_dist_diff > 3:
            pair_flights.twr_loss = "NO"

            twr_event = TwrLoss()
            twr_event.time = to_hhmmss(pair.TWR_time)
            twr_event.horizontal_separation_nm = float(pair.TWR_dist_diff)
            twr_event.altitude_separation_ft = float(pair.TWR_alt_diff)
            twr_event.distance_twr_nm = float(pair.distTWR)
            twr_event.loss_details = ""
            pair_flights.twr_details.append(twr_event)
        
        elif pair.TWR_dist_diff is None:
            pair_flights.twr_loss = "NO"

            twr_event = TmaLoss()
            twr_event.loss_details = "LEADER OUT OF GEO FILTER"
            twr_event.horizontal_separation_nm = None
            twr_event.altitude_separation_ft = None
            twr_event.distance_twr_nm = float(pair.distTWR)
            twr_event.time = None

            pair_flights.twr_details.append(twr_event)


        results.append(pair_flights)

    return results


def get_min_horizontal_separation(wake_lead, wake_foll):
    
    if wake_lead == "Super Pesada":
        if wake_foll == "Pesada": return 6
        elif wake_foll == "Media": return 7
        elif wake_foll == "Ligera": return 8
    elif wake_lead == "Pesada":
        if wake_foll == "Pesada": return 4
        elif wake_foll == "Media": return 5
        elif wake_foll == "Ligera": return 6
    elif wake_lead == "Media":
        if wake_foll == "Ligera": return 5
    return None

def check_wake_loss(distance, altitude, min_sep):
    
    if distance is None or min_sep is None:
        return None
    if distance < min_sep:
        return "OPERATIONAL LOSS" if altitude < 1000 else "HORIZONTAL LOSS"
    return ""

def wake_sep(flights):

    result = []

    for pair in flights:

        actual_pair = Wake_sep()
        actual_pair.pair = pair.pair
        actual_pair.runway = pair.runway
        actual_pair.wake_lead = pair.wake_lead
        actual_pair.wake_foll = pair.wake_foll
        actual_pair.sid_lead = pair.sid_lead
        actual_pair.sid_lead_g = pair.sid_lead_group
        actual_pair.sid_foll = pair.sid_foll
        actual_pair.sid_foll_g = pair.sid_foll_group
      
        min_sep = get_min_horizontal_separation(pair.wake_lead, pair.wake_foll)
        actual_pair.min_hor_sep = min_sep

        dist_twr = pair.TWR_dist_diff
        alt_twr = pair.TWR_alt_diff
        time_twr = pair.TWR_time

        if dist_twr is not None:
            dist_twr = float(dist_twr)
            alt_twr = float(alt_twr)
            loss_details_twr = check_wake_loss(dist_twr, alt_twr, min_sep)
        else:
            loss_details_twr = None

        twr_det = TwrLoss()
        if loss_details_twr:
            actual_pair.twr_loss = "YES"
            twr_det.loss_details = loss_details_twr
            twr_det.horizontal_separation_nm = dist_twr
            twr_det.altitude_separation_ft = alt_twr
            twr_det.distance_twr_nm = float(pair.distTWR) if pair.distTWR else None
            twr_det.time = to_hhmmss(time_twr)
        elif dist_twr is None:
            actual_pair.twr_loss = "NO"
            twr_det.loss_details = "LEADER OUT OF GEO FILTERS"
            twr_det.horizontal_separation_nm = None
            twr_det.altitude_separation_ft = None
            twr_det.distance_twr_nm = pair.distTWR
            twr_det.time = time_twr
        else:
            actual_pair.twr_loss = "NO"
            twr_det.loss_details = ""
            twr_det.horizontal_separation_nm = dist_twr
            twr_det.altitude_separation_ft = alt_twr
            twr_det.distance_twr_nm = float(pair.distTWR) if pair.distTWR else None
            twr_det.time = to_hhmmss(time_twr)

        actual_pair.twr_details.append(twr_det)

        dist_tma = pair.TMA_dist
        alt_tma = pair.TMA_alt
        time_tma = pair.TMA_time

        if dist_tma is not None:
            dist_tma = float(dist_tma)
            alt_tma = float(alt_tma)
            loss_details_tma = check_wake_loss(dist_tma, alt_tma, min_sep)
        else:
            loss_details_tma = None

        tma_det = TmaLoss()
        if loss_details_tma:
            actual_pair.tma_loss = "YES"
            tma_det.horizontal_separation_nm = dist_tma
            tma_det.altitude_separation_ft = alt_tma
            tma_det.time = to_hhmmss(time_tma)
            tma_det.loss_details = loss_details_tma
        elif dist_tma is None:
            actual_pair.tma_loss = "NO"
            tma_det.loss_details = "LEADER OUT OF GEO FILTERS"
            tma_det.horizontal_separation_nm = None
            tma_det.altitude_separation_ft = None
            tma_det.time = time_tma
        else:
            actual_pair.tma_loss = "NO"
            tma_det.loss_details = ""
            tma_det.horizontal_separation_nm = dist_tma
            tma_det.altitude_separation_ft = alt_tma
            tma_det.time = to_hhmmss(time_tma)

        actual_pair.tma_details.append(tma_det)
        
        result.append(actual_pair)
    
    return result


def get_loa_evaluation(dist, class_L, class_F, sid_L, sid_F):

    if dist is None:
        return None, None

    def min_sep(same_sid, hp, r, lp, nrp, nrm):
        if same_sid:
            return hp
        else:
            return r

    if class_L == "HP":
        if class_F in ("HP", "R", "LP"):
            min_required = 5 if sid_L == sid_F else 3
        else:
            min_required = 3

    elif class_L == "R":
        if class_F == "HP":
            min_required = 7 if sid_L == sid_F else 5
        elif class_F in ("R", "LP"):
            min_required = 5 if sid_L == sid_F else 3
        else:
            min_required = 3

    elif class_L == "LP":
        if class_F == "HP":
            min_required = 8 if sid_L == sid_F else 6
        elif class_F == "R":
            min_required = 6 if sid_L == sid_F else 4
        elif class_F == "LP":
            min_required = 5 if sid_L == sid_F else 3
        else:
            min_required = 3

    elif class_L == "NR+":
        if class_F == "HP":
            min_required = 11 if sid_L == sid_F else 8
        elif class_F in ("R", "LP"):
            min_required = 9 if sid_L == sid_F else 6
        elif class_F == "NR+":
            min_required = 5 if sid_L == sid_F else 3
        else:
            min_required = 3

    elif class_L == "NR-":
        if class_F == "NR+":
            min_required = 9 if sid_L == sid_F else 6
        elif class_F == "NR-":
            min_required = 5 if sid_L == sid_F else 3
        elif class_F == "NR":
            min_required = 3
        else:
            min_required = 9

    elif class_L == "NR":
        if class_F == "NR":
            min_required = 5 if sid_L == sid_F else 3
        else:
            min_required = 9

    else:
        return None, None

    if dist < min_required:
        return "LOA loss", min_required
    else:
        return "", min_required


def LOA_sep(flights, table):

    result = []

    table_class = pd.read_excel(table)
    categories = {
        "HP": set(table_class['HP'].dropna()),
        "NR": set(table_class['NR'].dropna()),
        "NR+": set(table_class['NR+'].dropna()),
        "NR-": set(table_class['NR-'].dropna()),
        "LP": set(table_class['LP'].dropna())
    }

    for pair in flights:

        act_flight = LOA_separation()
        act_flight.pair = pair.pair
        act_flight.runway = pair.runway
        act_flight.sid_lead = pair.sid_lead
        act_flight.sid_lead_g = pair.sid_lead_group
        act_flight.sid_foll = pair.sid_foll
        act_flight.sid_foll_g = pair.sid_foll_group

        dist = pair.TWR_dist_diff
        alt = pair.TWR_alt_diff
        time = pair.TWR_time

        if dist is None:
            loa_det = TwrLoss()
            loa_det.loss_details = "LEADER OUT OF GEO FILTERS"
            loa_det.horizontal_separation_nm = None
            loa_det.altitude_separation_ft = None
            loa_det.distance_twr_nm = pair.distTWR
            loa_det.time = time
            act_flight.twr_loss = "NO"
            act_flight.twr_details.append(loa_det)
            result.append(act_flight)
            continue

        dist = float(dist)

        class_lead = next((name for name, s in categories.items() if pair.AC_lead in s), "R")
        class_foll = next((name for name, s in categories.items() if pair.AC_foll in s), "R")

        act_flight.lead_class = class_lead
        act_flight.foll_class = class_foll

        loss_details, min_required = get_loa_evaluation(
            dist, class_lead, class_foll, pair.sid_lead_group, pair.sid_foll_group
        )

        loa_det = TwrLoss()
        loa_det.horizontal_separation_nm = dist
        loa_det.altitude_separation_ft = float(alt)
        loa_det.distance_twr_nm = float(pair.distTWR)
        loa_det.time = to_hhmmss(time)
        act_flight.min_hor_sep = min_required

        if loss_details:
            act_flight.twr_loss = "YES"
            loa_det.loss_details = loss_details
        else:
            act_flight.twr_loss = "NO"
            loa_det.loss_details = ""

        act_flight.twr_details.append(loa_det)
        result.append(act_flight)

    return result


def PrintResults(file, res):

    data = []

    for pair in res:
        
        lead, foll = pair.pair.split('-')

        if "LOA" not in file:

            # Extraer listas
            dist_list = [d.horizontal_separation_nm for d in pair.tma_details]
            alt_list  = [d.altitude_separation_ft for d in pair.tma_details]
            type_list = [d.loss_details for d in pair.tma_details]
            time_list = [d.time for d in pair.tma_details]

            if not dist_list or dist_list[0] is None:
                tma_data = {
                    'TMA_Type': None,
                    'TMA_Dist': None,
                    'TMA_Alt': None,
                    'Time': None
                }
            else:
                
                idx = min(range(len(dist_list)), key=lambda i: dist_list[i])

                tma_data = {
                    'TMA_Type': type_list[idx],
                    'TMA_Dist': dist_list[idx],
                    'TMA_Alt': alt_list[idx],
                    'Time': time_list[idx]
                }

        twr = pair.twr_details[0]

        twr_data = {
            'TWR_Type': twr.loss_details,
            'TWR_Dist': twr.horizontal_separation_nm,
            'Dist2TWR': twr.distance_twr_nm,
            'TWR_Alt': twr.altitude_separation_ft,
            'Time': twr.time
        }


        if "LOA" not in file:
            df_pair = pd.concat([pd.DataFrame([tma_data]), pd.DataFrame([twr_data])], axis=1)
        else:
            df_pair = pd.DataFrame([twr_data])


        if "Radar" in file:
            df_pair.insert(0, 'Leader', lead)
            df_pair.insert(1, 'Sid_lead', pair.sid_lead)
            df_pair.insert(2, 'Sid_lead_G', pair.sid_lead_g)
            df_pair.insert(3, 'Follower', foll)
            df_pair.insert(4, 'Sid_foll', pair.sid_foll)
            df_pair.insert(5, 'Sid_foll_G', pair.sid_foll_g)
            df_pair.insert(6, 'Runway', pair.runway)
            df_pair.insert(7, 'TMA loss', pair.tma_loss)
            df_pair.insert(8, 'TWR loss', pair.twr_loss)

        if "Wake" in file:
            df_pair.insert(0, 'Leader', lead)
            df_pair.insert(1, 'Sid_lead', pair.sid_lead)
            df_pair.insert(2, 'Sid_lead_G', pair.sid_lead_g)
            df_pair.insert(3, 'Wake_lead', pair.wake_lead)
            df_pair.insert(4, 'Follower', foll)
            df_pair.insert(5, 'Sid_foll', pair.sid_foll)
            df_pair.insert(6, 'Sid_foll_G', pair.sid_foll_g)
            df_pair.insert(7, 'Wake_foll', pair.wake_foll)
            df_pair.insert(8, 'Runway', pair.runway)
            df_pair.insert(9, 'TMA loss', pair.tma_loss)
            df_pair.insert(10, 'TWR loss', pair.twr_loss)
            df_pair.insert(11, 'min dist', pair.min_hor_sep)

        if "LOA" in file:
            df_pair.insert(0, 'Leader', lead)
            df_pair.insert(1, 'Sid_lead', pair.sid_lead)
            df_pair.insert(2, 'Sid_lead_G', pair.sid_lead_g)
            df_pair.insert(3, 'Lead_class', pair.lead_class)
            df_pair.insert(4, 'Follower', foll)
            df_pair.insert(5, 'Sid_foll', pair.sid_foll)
            df_pair.insert(6, 'Sid_foll_G', pair.sid_foll_g)
            df_pair.insert(7, 'Foll_class', pair.foll_class)
            df_pair.insert(8, 'Runway', pair.runway)
            df_pair.insert(9, 'TWR loss', pair.twr_loss)
            df_pair.insert(11, 'min dist', pair.min_hor_sep)
            

        data.append(df_pair)

    final_df = pd.concat(data, ignore_index=True)
    final_df.to_excel(file, index=False)


