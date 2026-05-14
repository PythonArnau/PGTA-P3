import numpy as np
import pandas as pd
from openpyxl import load_workbook, Workbook
import inspect
import matplotlib.pyplot as plt
from collections import Counter


def getTMA(pairs):

    conflicts = 0

    for pair in pairs:

        if pair.tma_loss == "YES":
            conflicts = conflicts + 1
    
    percentage = conflicts / len(pairs)

    return(percentage)


def getTWR(pairs):

    conflicts = 0

    for pair in pairs:

        if pair.twr_loss == "YES":
            conflicts = conflicts + 1
    
    percentage = conflicts / len(pairs)

    return(percentage)


def createExcel(radar, wake, LOA, ac, ac_rad, ac_wake, ac_loa):
    
    param = inspect.signature(createExcel).parameters
    n = len(param)

    rad = pd.DataFrame({"TMA_radar": [radar[0]], "TWR_radar":[radar[1]]})
    wa = pd.DataFrame({"TMA_wake": [wake[0]], "TWR_wake": [wake[1]]})
    loa = pd.DataFrame({"TMA_wake": [LOA[0]]})
    ACs = pd.DataFrame({"Aircraft": [ac[0]], "Amount": [ac[1]]})
    ACs_rad = pd.DataFrame({"Aircraft": [ac_rad[0]], "Amount_TMA": [ac_rad[1]],"Amount_TWR": [ac_rad[2]]})
    ACs_wake = pd.DataFrame({"Aircraft": [ac_wake[0]], "Amount_TMA": [ac_wake[1]],"Amount_TWR": [ac_wake[2]]})
    ACs_loa = pd.DataFrame({"Aircraft": [ac_loa[0]], "Amount_TWR": [ac_loa[1]]})

    with pd.ExcelWriter("Statistics.xlsx", engine="openpyxl") as writer:
        
        rad.to_excel(writer, sheet_name="Hoja 1", index = False, startrow = 0)
        wa.to_excel(writer, sheet_name="Hoja 1", index = False, startrow = len(rad) + 2)
        loa.to_excel(writer, sheet_name="Hoja 1", index = False, startrow = len(rad) + 2 + len(wa) + 2)
        ACs.to_excel(writer, sheet_name="Hoja 1", index = False, startrow = len(rad) + 2 + len(wa) + 2 + len(loa) + 2)
        ACs_rad.to_excel(writer, sheet_name="Hoja 1", index = False, startrow = len(rad) + 2 + len(wa) + 2 + len(loa) + 2 + len(ACs) + 2)
        ACs_wake.to_excel(writer, sheet_name="Hoja 1", index = False, startrow = len(rad) + 2 + len(wa) + 2 + len(loa) + 2 + len(ACs) + 2 + len(ACs_rad) + 2)
        ACs_loa.to_excel(writer, sheet_name="Hoja 1", index = False, startrow = len(rad) + 2 + len(wa) + 2 + len(loa) + 2 + len(ACs) + 2 + len(ACs_rad) + 2 + len(ACs_wake) + 2)


def createPlots(radar, wake, LOA, acs, acs_rad, acs_wake, acs_loa):
    
    params = inspect.signature(createPlots).parameters
    keys = list(params.keys())  
    frame = inspect.currentframe()
    arguments = inspect.getargvalues(frame)

    labl = ["TMA", "TWR"]
    

    for i in range(len(params)):
        vecs = arguments.locals[keys[i]] 
        if keys[i] == "radar" or keys[i] == "wake" or keys[i] == "LOA":
            if len(vecs)>1:
                plt.bar(labl, vecs)
                plt.title(keys[i])
            
            else:
                plt.bar(labl[1], vecs)
                plt.title(keys[i])

        elif keys[i] == "acs":
            plt.bar(vecs[0], vecs[1])
            plt.title("Aircraft stats")

        elif keys[i] == "acs_rad" or keys[i] == "acs_wake" or keys[i] == "acs_loa":
            if keys[i] != "acs_loa":
                fig, ax = plt.subplots()
                ax.bar(vecs[0], vecs[1], label = "TMA")
                ax.bar(vecs[0], vecs[2], label = "TWR")
                ax.legend()
            else:
                plt.bar(vecs[0], vecs[1])
            
            plt.title(f"{keys[i]} violation stats")
        
        plt.grid
        plt.savefig(f"grafico_{keys[i]}.png", dpi=150)
        plt.close()


def getAC_violation(AC, num, type, flights):
    
    num2 = [0] * len(num)
    num2TWR = [0] * len(num)

    for pair in type:
            if hasattr(pair, "tma_loss"):
                if pair.tma_loss == "YES":
                    pr = pair.pair.split("-")
                    ac1 = next((item.aircraft for item in flights if item.callsign == pr[0]), None)
                    ac2 = next((item.aircraft for item in flights if item.callsign == pr[1]), None)
                    ac_slot1 = AC.index(ac1)
                    ac_slot2 = AC.index(ac2)

                    act_num21 = num2[ac_slot1]
                    num21 = act_num21 + 1
                    num2[ac_slot1] = num21

                    act_num22 = num2[ac_slot2]
                    num22 = act_num22 + 1
                    num2[ac_slot2] = num22

            if pair.twr_loss == "YES":
                pr = pair.pair.split("-")
                ac1 = next((item.aircraft for item in flights if item.callsign == pr[0]), None)
                ac2 = next((item.aircraft for item in flights if item.callsign == pr[1]), None)
                ac_slot1 = AC.index(ac1)
                ac_slot2 = AC.index(ac2)

                act_num21 = num2TWR[ac_slot1]
                num21 = act_num21 + 1
                num2TWR[ac_slot1] = num21

                act_num22 = num2TWR[ac_slot2]
                num22 = act_num22 + 1
                num2TWR[ac_slot2] = num22

    return num2, num2TWR


def getAC(pairs):

    AC = []
    Callsigns = []
    num = []

    
    for pair in pairs:
        call_lead = pair.leader
        call_foll = pair.follower

        if call_lead not in Callsigns: 
            Callsigns.append(call_lead)

            if pair.AC_lead not in AC:
                AC.append(pair.AC_lead)
                num.append(1)
            
            else:
                idx = AC.index(pair.AC_lead)
                act_num = num[idx]
                sum = act_num + 1
                num[idx] = sum

        if call_foll not in Callsigns:
            Callsigns.append(call_foll)

            if pair.AC_foll not in AC:
                AC.append(pair.AC_foll)
                num.append(1)

            else:
                idx = AC.index(pair.AC_foll)
                act_num = num[idx]
                sum = act_num + 1
                num[idx] = sum
    
    return AC, num


def getAirlines(flights):

    Airlines = []
    num = []

    
    for flight in flights:
       
        if flight.callsign[:3] not in Airlines:
            Airlines.append(flight.callsign[:3])
            num.append(1)
        
        else:
            idx = Airlines.index(flight.callsign[:3])
            act_num = num[idx]
            new_num = act_num + 1
            num[idx] = new_num

    percent = [x / sum(num) for x in num]

    return Airlines, num, percent


def getCircleGraph(x, y, title):
    if sum(y) != 0:
        n_x, n_y = filterData(x, y)
        explode = [0] * len(n_y)
        idx = n_y.index(max(n_y))
        explode[idx] = 0.1
        explode = tuple(explode)

        fig, ax = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax.pie(n_y, explode=explode, autopct='%1.1f%%',
                                           shadow=True, startangle=90)
       
        ax.legend(wedges, n_x, title=title, loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)

        for autotext in autotexts:
            autotext.set_fontsize(7)

        ax.axis("equal")
        plt.title(title)
        plt.savefig(f"grafico_{title}.png", dpi=150, bbox_inches="tight")
        plt.close()
    
    else:
        print("No data available to make the plot")


def filterData(x, y):
    n_x = x.copy()  
    n_y = y.copy()  

    for i in y:  
        if i == 0:
            idx = n_y.index(i)
            n_x.pop(idx)
            n_y.pop(idx)
    
    return (n_x, n_y)


def getViolatingAirlines(Airlines, pairs):

    numTMA  = [0] * len(Airlines)
    numTWR  = [0] * len(Airlines)
    ACs = []

    for pair in pairs:
        pr = pair.pair.split('-')
        ac1 = pr[0]
        ac2 = pr[1]
        
        if ac1 not in ACs:
            ACs.append(ac1)
            airline1 = pr[0][:3]
            idx = Airlines.index(airline1)

            if hasattr(pair, "tma_loss"):
                if pair.tma_loss == "YES":
                    
                    act_num = numTMA[idx]
                    new_num = act_num + 1
                    numTMA[idx] = new_num
            
            if pair.twr_loss == "YES":
                
                act_num = numTWR[idx]
                new_num = act_num + 1
                numTWR[idx] = new_num
        
        if ac2 not in ACs:
            ACs.append(ac2)
            airline2 = pr[1][:3]
            idx = Airlines.index(airline2)

            if hasattr(pair, "tma_loss"):
                if pair.tma_loss == "YES":
                    
                    act_num = numTMA[idx]
                    new_num = act_num + 1
                    numTMA[idx] = new_num
            
            if pair.twr_loss == "YES":
                
                act_num = numTWR[idx]
                new_num = act_num + 1
                numTWR[idx] = new_num
        
        if sum(numTMA) != 0:
            percentTMA = [x / sum(numTMA) for x in numTMA]
        else:
            percentTMA = numTMA

        if sum(numTWR) != 0:
            percentTWR = [y / sum(numTWR) for y in numTWR]
        else:
            percentTWR = numTWR

    return numTMA, numTWR, percentTMA, percentTWR


def getDoubleBarGraph(x, y1, y2, title, lbl1, lbl2):
    fig, ax = plt.subplots(figsize=(len(x) * 0.5, 6))
    ax.bar(x, y1, label = lbl1)
    ax.bar(x, y2, label = lbl2)
    ax.legend()

    plt.title(f"{title} violation stats")
        
    plt.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
    plt.xticks(rotation=45, ha="right")
    plt.savefig(f"grafico_{title}.png", dpi=150, bbox_inches="tight")
    plt.close()


def getBarGraph(x, y, title):

    plt.bar(x, y)
    plt.title(f"{title}")
    plt.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
    plt.xticks(rotation=45, ha="right")
    plt.savefig(f"grafico_{title}.png", dpi=150, bbox_inches="tight")
    plt.close()


def getLOAclass_and_sid(pairs):

    loa_icao = ["HP", "R", "LP", "NR+", "NR-", "NR"]
    loa_sid = ["G1", "G2", "G3"]
    pair_loa_sid = []
    pair_loa_icao = []
    for w in loa_icao:
        i = 0
        for i in range(len(loa_icao)):
            pairing = w + "-" + loa_icao[i]
            reverse = loa_icao[i] + "-" + w
            if pairing not in pair_loa_icao and reverse not in pair_loa_icao:
                pair_loa_icao.append(pairing)

    for s in loa_sid:
        j = 0
        for j in range(len(loa_sid)):
            pring = s + "-" + loa_sid[j]
            rvrse = loa_sid[j] + "-" + s
            if pring not in pair_loa_sid and rvrse not in pair_loa_sid:
                pair_loa_sid.append(pring)
    
    pair_loa_icao.sort()
    pair_loa_sid.sort()

    count_loa = [0] * len(pair_loa_icao)
    count_loa_same_sid = [0] * len(pair_loa_sid)
    count_individual_loa = [0] * len(loa_icao)
    count_individual_sid = [0] * len(loa_sid)

    count_loa_violating = [0] * len(pair_loa_icao)
    count_sid_violating = [0] * len(pair_loa_sid)
    
    acs_list = []
    for pair in pairs:
        acs = pair.pair.split("-")

        loa_lead = pair.lead_class
        ac_lead = acs[0]
        sid_g_lead = pair.sid_lead_g
        
        loa_foll = pair.foll_class
        ac_foll = acs[1]
        sid_g_foll = pair.sid_foll_g

        if ac_lead not in acs_list:
            acs_list.append(ac_lead)
            idx1 = loa_icao.index(loa_lead)
            count_individual_loa[idx1] = count_individual_loa[idx1] + 1
            if sid_g_lead in loa_sid:
                idx2 = loa_sid.index(sid_g_lead)
                count_individual_sid[idx2] = count_individual_sid[idx2] + 1
        
        if ac_foll not in acs_list:
            acs_list.append(ac_foll)
            idx1 = loa_icao.index(loa_foll)
            count_individual_loa[idx1] = count_individual_loa[idx1] + 1
            if sid_g_foll in loa_sid:
                idx2 = loa_sid.index(sid_g_foll)
                count_individual_sid[idx2] = count_individual_sid[idx2] + 1

        loa_pairing = loa_lead + "-" + loa_foll
        reverse_pairing = loa_foll + "-" + loa_lead
        if loa_pairing in pair_loa_icao:
            idx = pair_loa_icao.index(loa_pairing)
            count_loa[idx] = count_loa[idx] + 1
            if pair.twr_loss == "YES":
                count_loa_violating[idx] = count_loa_violating[idx] + 1

        elif reverse_pairing in pair_loa_icao:
            idx = pair_loa_icao.index(reverse_pairing)
            count_loa[idx] = count_loa[idx] + 1
            if pair.twr_loss == "YES":
                count_loa_violating[idx] = count_loa_violating[idx] + 1

        sid_pairing = sid_g_lead + "-" + sid_g_foll
        reverse_sid_pairing = sid_g_foll + "-" + sid_g_lead
        if sid_pairing in pair_loa_sid:
            idx = pair_loa_sid.index(sid_pairing)
            count_loa_same_sid[idx] = count_loa_same_sid[idx] + 1
            if pair.twr_loss == "YES":
                count_sid_violating[idx] = count_sid_violating[idx] + 1

        elif reverse_sid_pairing in pair_loa_sid:
            idx = pair_loa_sid.index(reverse_sid_pairing)
            count_loa_same_sid[idx] = count_loa_same_sid[idx] + 1
            if pair.twr_loss == "YES":
                count_sid_violating[idx] = count_sid_violating[idx] + 1

    return loa_icao, pair_loa_icao, loa_sid, pair_loa_sid, count_individual_loa, count_loa, count_loa_violating, count_individual_sid, count_loa_same_sid, count_sid_violating





def getStatistics(radar, wake, LOA, pairs, flights):

    conflicts_TMA_radar = getTMA(radar)
    conflicts_TWR_radar = getTWR(radar)

    rad_conflicts = [conflicts_TMA_radar, conflicts_TWR_radar]

    conflicts_TMA_wake = getTMA(wake)
    conflicts_TWR_wake = getTWR(wake)

    wake_conflicts = [conflicts_TMA_wake, conflicts_TWR_wake]

    conflicts_TWR_loa = getTWR(LOA)

    LOA_conflicts = [conflicts_TWR_loa]

    Aircrafts, number = getAC(pairs)
    AC_recs = [Aircrafts, number]

    num_rad, num_radTWR = getAC_violation(Aircrafts, number, radar, flights)
    AC_rad_recs = [Aircrafts, num_rad, num_radTWR]

    num_wake, num_wakeTWR = getAC_violation(Aircrafts, number, wake, flights)
    AC_wake_recs = [Aircrafts, num_wake, num_wakeTWR]

    num_loa, num_loaTWR = getAC_violation(Aircrafts, number, LOA, flights)
    AC_loa_recs = [Aircrafts, num_loaTWR]

    Airlines, num_airlines, percent_airlines = getAirlines(flights)
    getCircleGraph(Airlines, percent_airlines, "airlines")
    getBarGraph(Airlines, num_airlines, "num_airlines")

    num_airlines_TMA_rad, num_airlines_TWR_rad, per_airl_TMA_rad, per_airl_TWR_rad = getViolatingAirlines(Airlines, radar)
    getCircleGraph(Airlines, per_airl_TMA_rad, "Airlines radar violation TMA")
    getCircleGraph(Airlines, per_airl_TWR_rad, "Airlines radar violation TWR")

    num_airlines_TMA_wake, num_airlines_TWR_wake, per_airl_TMA_wake, per_airl_TWR_wake = getViolatingAirlines(Airlines, wake)
    getCircleGraph(Airlines, per_airl_TMA_wake, "Airlines wake violation TMA")
    getCircleGraph(Airlines, per_airl_TWR_wake, "Airlines wake violation TWR")

    num_airlines_TMA_loa, num_airlines_TWR_loa, per_airl_TMA_loa, per_airl_TWR_loa = getViolatingAirlines(Airlines, LOA)
    getCircleGraph(Airlines, per_airl_TWR_loa, "Airlines LOA violation TWR")

    loa_class, pair_loa_class, sid_g, pair_sid_group, num_loa, num_pair_loa, num_violating_loa, num_sid, num_pair_sid, num_violating_sid = getLOAclass_and_sid(LOA)
    getBarGraph(loa_class, num_loa, "LOA classes")
    getDoubleBarGraph(pair_loa_class, num_pair_loa, num_violating_loa, "Pair LOA classes", "Loa Pairs analyzed", "TWR")
    getBarGraph(sid_g, num_sid, "SIDs")
    getDoubleBarGraph(pair_sid_group, num_pair_sid, num_violating_sid, "Pair SIDs", "Tot SIDs analyzed", "TWR")

    createExcel(rad_conflicts, wake_conflicts, LOA_conflicts, AC_recs, AC_rad_recs, AC_wake_recs, AC_loa_recs)
    createPlots(rad_conflicts, wake_conflicts, LOA_conflicts, AC_recs, AC_rad_recs, AC_wake_recs, AC_loa_recs)



