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



def PrintResults(file, res):

    data = []

    for pair in res:
        
        lead, foll = pair.pair.split('-')

        tma_data = {
            'TMA_Type': [d.loss_details for d in pair.tma_details],
            'TMA_Dist': [d.horizontal_separation_nm for d in pair.tma_details],
            'TMA_Alt': [d.altitude_separation_ft for d in pair.tma_details],
            'Time': [d.time for d in pair.tma_details]
        }
        
        twr_data = {
            'TWR_Type': [d.loss_details for d in pair.twr_details],
            'TWR_Dist': [d.horizontal_separation_nm for d in pair.twr_details],
            'Dist2TWR': [d.distance_twr_nm for d in pair.twr_details],
            'TWR_Alt': [d.altitude_separation_ft for d in pair.twr_details],
            'Time': [d.time for d in pair.twr_details]
        }

        df_tma = pd.DataFrame(tma_data)
        df_twr = pd.DataFrame(twr_data)

        if df_tma.empty:
            df_tma = pd.DataFrame({'TMA_Type': ['-'], 'TMA_Dist':['-'], 'TMA_Alt': ['-'], 'Time':['-']})
        if df_twr.empty:
            df_twr = pd.DataFrame({'TMR_Type': ['-'], 'TMR_Dist':['-'], 'Dist2TWR':['-'], 'TMR_Alt': ['-'], 'Time':['-']})

        df_pair = pd.concat([df_tma, df_twr], axis=1)

        empty_row = pd.DataFrame([[np.nan] * len(df_pair.columns)], columns=df_pair.columns)
        df_pair = pd.concat([df_pair, empty_row], ignore_index=True) #Le añado una linia en blaco despues de una pareja

        df_pair.insert(0, 'Leader', lead)
        df_pair.insert(1, 'Follower', foll)
        df_pair.insert(2, 'Runway', pair.runway)
        df_pair.insert(3, 'TMA loss', pair.tma_loss)
        df_pair.insert(4, 'TWR loss', pair.twr_loss)

        df_pair.loc[df_pair.index > 0, ['Leader', 'Follower', 'Runway', 'TMA loss', 'TWR loss']] = ""

        data.append(df_pair)

    final_df = pd.concat(data, ignore_index=True)
    final_df.to_excel(file, index=False)