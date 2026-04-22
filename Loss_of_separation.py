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


class Separation:
    def __init__(self):
        self.pair: str = ""
        self.runway: str = ""
        self.tma_loss: str = "NO"
        self.twr_loss: str = "NO"
        self.tma_details: list[TmaLoss] = []
        self.twr_details: list[TwrLoss] = []


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