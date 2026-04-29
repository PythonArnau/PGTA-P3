import pandas as pd
import numpy as np


class SeparationLoss:
    def __init__(self):
        self.loss_details: str = ""
        self.time: float = 0.0
        self.horizontal_separation_nm: float = 0.0
        self.altitude_separation_ft: float = 0.0


class TmaLoss(SeparationLoss):
    pass                            #Con esto decimos que no añadimos nada más sinó que usamos los campos de SeparationLoss


class TwrLoss(SeparationLoss):
    def __init__(self):
        super().__init__()                      #Con esto decimos que le añadimos el campo de abajo a los campos de SeparationLoss
        self.distance_twr_nm: float = 0.0

class TmaWakeLoss(SeparationLoss):
    pass

class TwrWakeLoss(SeparationLoss):
    def __init__(self):
        super().__init__()
        self.distance_twr_nm: float = 0.0

class LoALoss(SeparationLoss):
    pass

class Separation:
    def __init__(self):
        self.pair: str = ""
        self.runway: str = ""
        self.tma_loss: str = "NO"
        self.twr_loss: str = "NO"
        self.tma_wake_loss: str = "NO"
        self.twr_wake_loss: str = "NO"
        self.Loa_loss: str = "NO"
        self.tma_details: list[TmaLoss] = []
        self.twr_details: list[TwrLoss] = []
        self.tma_wake_details: list[TmaWakeLoss] = []
        self.twr_wake_details: list[TwrWakeLoss] = []
        self.LoA_details: list[LoALoss] = []


def radar(flights):
    results = []

    for pair in flights:
        pair_flights = Separation()
        pair_flights.pair = pair.pair
        pair_flights.runway = pair.runway

        for sample in pair.geometric_values:

            if sample.distance_nm < 3:
                pair_flights.tma_loss = "YES"

                tma_event = TmaLoss()
                tma_event.time = sample.time
                tma_event.horizontal_separation_nm = sample.distance_nm
                tma_event.altitude_separation_ft = sample.altitude_diff
                tma_event.loss_details = (
                    "HORIZONTAL SEPARATION"
                    if sample.altitude_diff >= 1000
                    else "OPERATIONAL SEPARATION"
                )
                pair_flights.tma_details.append(tma_event)

            TWR_sample = (
                sample.distance_nm == pair.TWR_dist_diff
                and sample.altitude_diff == pair.TWR_alt_diff
                and sample.distance_follower_tower_nm == pair.distTWR
            )                                                               #Miramos si el sample es el de TWR

            if TWR_sample and sample.distance_nm < 3:
                pair_flights.twr_loss = "YES"

                twr_event = TwrLoss()
                twr_event.time = sample.time
                twr_event.horizontal_separation_nm = sample.distance_nm
                twr_event.altitude_separation_ft = sample.altitude_diff
                twr_event.distance_twr_nm = sample.distance_follower_tower_nm
                twr_event.loss_details = (
                    "HORIZONTAL SEPARATION"
                    if sample.altitude_diff >= 1000
                    else "OPERATIONAL SEPARATION"
                )
                pair_flights.twr_details.append(twr_event)

        results.append(pair_flights)

    return results


def Get_Cases(pair):
    l_wake = pair.leader_wake
    f_wake = pair.follower_wake

    # CASE LEADER IS SUPER PESADA
    if l_wake == "Super Pesada":
        if f_wake == "Pesada":
            return 6
        elif f_wake == "Media":
            return 7
        elif f_wake == "Ligera":
            return 8
    # CASE LEADER IS PESADA
    elif l_wake == "Pesada":
        if f_wake == "Pesada":
            return 4
        elif f_wake == "Media":
            return 5
        elif f_wake == "Ligera":
            return 6
    # CASE LEADER IS MEDIA
    elif l_wake == "Media":
        if f_wake == "Ligera":
            return 5

    # No wake separation rule applies for this combination
    return None

def wake(flights):
    results = []

    for pair in flights:
        pair_flights = Separation()
        pair_flights.pair = pair.pair
        pair_flights.runway = pair.runway
        min_sep = Get_Cases(pair)

        # No wake rule applies for this leader/follower category combination
        if min_sep is None:
            results.append(pair_flights)
            continue

        for sample in pair.geometric_values:
            if sample.distance_nm < min_sep:
                pair_flights.tma_wake_loss = "YES"

                tma_wake_event = TmaWakeLoss()
                tma_wake_event.time = sample.time
                tma_wake_event.horizontal_separation_nm = sample.distance_nm
                tma_wake_event.altitude_separation_ft = sample.altitude_diff
                tma_wake_event.loss_details = "WAKE OPERATIONAL SEPARATION"
                pair_flights.tma_wake_details.append(tma_wake_event)

            TWR_sample = (
                    sample.distance_nm == pair.TWR_dist_diff
                    and sample.altitude_diff == pair.TWR_alt_diff
                    and sample.distance_follower_tower_nm == pair.distTWR
            )
            if TWR_sample and sample.distance_nm < min_sep:
                pair_flights.twr_wake_loss = "YES"
                twr_wake_event = TwrWakeLoss()
                twr_wake_event.time = sample.time
                twr_wake_event.horizontal_separation_nm = sample.distance_nm
                twr_wake_event.altitude_separation_ft = sample.altitude_diff
                twr_wake_event.loss_details = "WAKE OPERATIONAL SEPARATION"
                pair_flights.twr_wake_details.append(twr_wake_event)

        results.append(pair_flights)

    return results


def _min_event(details):
    """Return the event with the minimum horizontal separation from a list of loss events."""
    return min(details, key=lambda d: d.horizontal_separation_nm)


def PrintResults(file, res, wake_res):
    wake_dict = {w.pair: w for w in wake_res}
    rows = []

    for pair in res:
        wake_pair = wake_dict.get(pair.pair)
        lead, foll = pair.pair.split('-')

        # --- Radar TMA ---
        tma_loss     = pair.tma_loss
        tma_min      = _min_event(pair.tma_details) if pair.tma_details else None

        # --- Radar TWR ---
        twr_loss     = pair.twr_loss
        twr_min      = _min_event(pair.twr_details) if pair.twr_details else None

        # --- Wake TMA ---
        tma_wake_loss = wake_pair.tma_wake_loss if wake_pair else "NO"
        tma_wake_min  = _min_event(wake_pair.tma_wake_details) if (wake_pair and wake_pair.tma_wake_details) else None

        # --- Wake TWR ---
        twr_wake_loss = wake_pair.twr_wake_loss if wake_pair else "NO"
        twr_wake_min  = _min_event(wake_pair.twr_wake_details) if (wake_pair and wake_pair.twr_wake_details) else None

        row = {
            'Leader':           lead,
            'Follower':         foll,
            'Runway':           pair.runway,
            'Radar TMA Loss':   tma_loss,
            'Radar TWR Loss':   twr_loss,
            'TMA Wake Loss':    tma_wake_loss,
            'TWR Wake Loss':    twr_wake_loss,
            # Radar TMA detail columns
            'Radar TMA - Detail':       tma_min.loss_details                if tma_min else '-',
            'Radar TMA - Min Dist (nm)':tma_min.horizontal_separation_nm    if tma_min else '-',
            'Radar TMA - Altitude (ft)':tma_min.altitude_separation_ft      if tma_min else '-',
            'Radar TMA - Time':         tma_min.time                        if tma_min else '-',
            # Radar TWR detail columns
            'Radar TWR - Detail':       twr_min.loss_details                if twr_min else '-',
            'Radar TWR - Min Dist (nm)':twr_min.horizontal_separation_nm    if twr_min else '-',
            'Radar TWR - Altitude (ft)':twr_min.altitude_separation_ft      if twr_min else '-',
            'Radar TWR - Time':         twr_min.time                        if twr_min else '-',
            'Radar TWR - Dist2TWR (nm)':twr_min.distance_twr_nm             if twr_min else '-',
            # Wake TMA detail columns
            'Wake TMA - Detail':        tma_wake_min.loss_details               if tma_wake_min else '-',
            'Wake TMA - Min Dist (nm)': tma_wake_min.horizontal_separation_nm   if tma_wake_min else '-',
            'Wake TMA - Altitude (ft)': tma_wake_min.altitude_separation_ft     if tma_wake_min else '-',
            'Wake TMA - Time':          tma_wake_min.time                       if tma_wake_min else '-',
            # Wake TWR detail columns
            'Wake TWR - Detail':        twr_wake_min.loss_details               if twr_wake_min else '-',
            'Wake TWR - Min Dist (nm)': twr_wake_min.horizontal_separation_nm   if twr_wake_min else '-',
            'Wake TWR - Altitude (ft)': twr_wake_min.altitude_separation_ft     if twr_wake_min else '-',
            'Wake TWR - Time':          twr_wake_min.time                       if twr_wake_min else '-',
            'Wake TWR - Dist2TWR (nm)': twr_wake_min.distance_twr_nm            if twr_wake_min else '-',
        }
        rows.append(row)

    final_df = pd.DataFrame(rows)
    final_df.to_excel(file, index=False)