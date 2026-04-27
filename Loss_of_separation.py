from inspect import Parameter

import pandas as pd


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


class Separation:
    def __init__(self):
        self.pair: str = ""
        self.runway: str = ""
        self.tma_loss: str = "NO"
        self.twr_loss: str = "NO"
        self.tma_wake_loss: str = "NO"
        self.twr_wake_loss: str = "NO"
        self.tma_details: list[TmaLoss] = []
        self.twr_details: list[TwrLoss] = []
        self.tma_wake_details: list[TmaWakeLoss] = []
        self.twr_wake_details: list[TwrWakeLoss] = []


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
                twr_event.distance_twr_nm = sample.distTWR
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

    sep = 0
    #CASE LEADER IS SUPERPESADA
    if l_wake == "Super Pesada":
        if f_wake == "Pesada":
            sep = 6
        elif f_wake == "Media":
            sep = 7
        elif f_wake == "Ligera":
            sep = 8
    #CASE LEADER IS PESADA
    elif l_wake == "Pesada":
        if f_wake == "Pesada":
            sep = 4
        elif f_wake == "Media":
            sep = 5
        elif f_wake == "Ligera":
            sep = 6
    #CASE LEADER IS MEDIA
    elif l_wake == "Media":
        if f_wake == "Ligera":
            sep = 5
    return sep

def wake(flights):
    results = []

    for pair in flights:
        pair_flights = Separation()
        pair_flights.pair = pair.pair
        pair_flights.runway = pair.runway
        min_sep = Get_Cases(pair)

        for sample in pair.geometric_values:
            if sample.distance_nm < min_sep:
                pair_flights.tma_loss = "YES"

                tma_wake_event = TmaWakeLoss()
                tma_wake_event.time = sample.time
                tma_wake_event.horizontal_separation_nm = sample.distance_nm
                tma_wake_event.altitude_separation_ft = sample.altitude_diff
                tma_wake_event.loss_details = ("WAKE OPERATIONAL SEPARATION")
                pair_flights.tma_wake_details.append(tma_wake_event)

            TWR_sample = (
                    sample.distance_nm == pair.TWR_dist_diff
                    and sample.altitude_diff == pair.TWR_alt_diff
                    and sample.distance_follower_tower_nm == pair.distTWR
            )
            if TWR_sample and sample.distance_nm < min_sep:
                pair_flights.twr_loss = "YES"
                twr_wake_event = TwrWakeLoss()
                twr_wake_event.time = sample.time
                twr_wake_event.horizontal_separation_nm = sample.distance_nm
                twr_wake_event.altitude_separation_ft = sample.altitude_diff
                twr_wake_event.loss_details = ("WAKE OPERATIONAL SEPARATION")
                pair_flights.twr_wake_details.append(twr_wake_event)
        results.append(pair_flights)
    return results

def export_losses_to_csv(radar_results, wake_results, filename="infraciones_separacion.csv"):
    min_losses = {}
    all_results = [
        ("RADAR", radar_results),
        ("WAKE", wake_results)
    ]

    for category, results in all_results:
        for entry in results:
            details = (entry.tma_details + entry.twr_details +
                       entry.tma_wake_details + entry.twr_wake_details)

            for loss in details:
                key = (category, entry.pair)
                dist = loss.horizontal_separation_nm

                if key not in min_losses or dist < min_losses[key]['Distancia_NM']:
                    min_losses[key] = {
                        "Tipo_Infraccion": category,
                        "Par_Vuelos": entry.pair,
                        "Pista": entry.runway,
                        "Tiempo_s": loss.time,
                        "Distancia_NM": dist,
                        "Altitud_ft": loss.altitude_separation_ft,
                        "Detalle": loss.loss_details
                    }
    data_for_csv = list(min_losses.values())

    # Creamos el DataFrame y exportamos
    if data_for_csv:
        df = pd.DataFrame(data_for_csv)
        df.to_csv(filename, index=False, sep=';', encoding='utf-8')


""""
def Get_Cases_LoA(pair):
    l_sid = pair.leader_sid
    f_sid = pair.follower_sid"""

