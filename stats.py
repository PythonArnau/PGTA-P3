def count_airlines_unique(pairs):
    unique_aircraft = set()   
    airline_counts = {}       

    for p in pairs:
        unique_aircraft.add(p[0].callsign)  
        unique_aircraft.add(p[1].callsign)  

    for ac in unique_aircraft:
        airline = ac[:3]  
        airline_counts[airline] = airline_counts.get(airline, 0) + 1

    return airline_counts


def TMA_TWR_airlines(pairs, airline_counts):
    TMA_radar_count = {k: 0 for k in airline_counts}
    TWR_radar_count = {n: 0 for n in airline_counts}

    followers_TMA = []
    followers_TWR = []

    for p in pairs:
        leader, follower = p.pair.split("-")
        leader_airline = leader[:3]
        follower_airline = follower[:3]
        
        if hasattr(p, "tma_loss"):
            if p.tma_loss == "YES":
                if leader not in followers_TMA:
                    TMA_radar_count[leader_airline] += 1
                
                TMA_radar_count[follower_airline] += 1
                followers_TMA.append(follower)

        if p.twr_loss == "YES":
            if leader not in followers_TWR:
                TWR_radar_count[leader_airline] += 1
            
            TWR_radar_count[follower_airline] += 1
            followers_TWR.append(follower)
    
    return TMA_radar_count, TWR_radar_count


def count_AC(flights):

    AC_count = {}

    for fl in flights:
        AC = fl.aircraft
        AC_count[AC] = AC_count.get(AC, 0) + 1
    
    return AC_count


def TMA_TWR_AC(flights, pairs, AC_count):
    TMA_AC = {k:0 for k in AC_count}
    TWR_AC = {n:0 for n in AC_count}

    callsigns = [fl.callsign for fl in flights]

    followers_TMA = []
    followers_TWR = []

    for p in pairs:

        leader, follower = p.pair.split("-")

        idx1 = callsigns.index(leader)
        idx2 = callsigns.index(follower)

        ac_l = flights[idx1].aircraft
        ac_f = flights[idx2].aircraft

        if hasattr(p, "tma_loss"):
            if p.tma_loss == "YES":
                if leader not in followers_TMA:
                    TMA_AC[ac_l] += 1
                
                TMA_AC[ac_f] += 1
                followers_TMA.append(follower)
            
        
        if p.twr_loss == "YES":
            if leader not in followers_TWR:
                TWR_AC[ac_l] += 1
            
            TWR_AC[ac_f] += 1
            followers_TWR.append(follower)

    return TMA_AC, TWR_AC


def countWake(pairs):
    wake_count={
        "Super Pesada": 0,
        "Pesada": 0,
        "Media": 0,
        "Ligera": 0
    }

    wake_count_pairs={
        "Super Pesada-Super Peasada": 0,
        "Super Pesada-Peasada": 0,
        "Super Pesada-Media": 0,
        "Super Pesada-Ligera": 0,
        "Pesada-Peasada": 0,
        "Pesada-Media": 0,
        "Pesada-Ligera": 0,
        "Media-Ligera": 0,
    }

    followers = []

    for p in pairs:
        leader = p[0].callsign
        follower = p[1].callsign

        wake_lead = p[0].wake
        wake_foll = p[1].wake

        wake_comb = wake_lead + "-" + wake_foll

        if wake_comb in wake_count_pairs:
            wake_count_pairs[wake_comb] += 1        

        if leader not in followers:
            wake_count[wake_lead] += 1

        wake_count[wake_foll] += 1
        followers.append(follower)
    
    return wake_count, wake_count_pairs


def TMA_TWR_wake(pairs, wake_count, wake_count_pairs):
    min_sep = {
        "8": 0,
        "7": 0,        
        "6": 0,
        "5": 0,
        "4": 0,
        "NO APLICA": 0
    }

    min_sep_TMA ={
        "8": 0,
        "7": 0,        
        "6": 0,
        "5": 0,
        "4": 0,
        "NO APLICA": 0
    }

    min_sep_TWR ={
        "8": 0,
        "7": 0,        
        "6": 0,
        "5": 0,
        "4": 0,
        "NO APLICA": 0
    }

    TMA_count = {k:0 for k in wake_count}
    TWR_count = {n:0 for n in wake_count}

    TMA_pair_count = {r:0 for r in wake_count_pairs}
    TWR_pair_count = {t:0 for t in wake_count_pairs}

    followersTMA = []
    followersTWR = []

    for p in pairs:

        leader, follower = p.pair.split("-")
        w_l = p.wake_lead
        w_f = p.wake_foll

        ms = p.min_hor_sep

        if ms is None:
            ms = "NO APLICA"
        else:
            ms = str(ms)

        min_sep[ms] += 1

        wake_pair = w_l + "-" + w_f

        if p.tma_loss == "YES":

            min_sep_TMA[ms] += 1

            if wake_pair in TMA_pair_count:
                TMA_pair_count[wake_pair] += 1
            
            if leader not in followersTMA:
                TMA_count[w_l] += 1

            TMA_count[w_f] += 1
            followersTMA.append(follower)

        if p.twr_loss == "YES":

            min_sep_TWR[ms] += 1

            if wake_pair in TWR_pair_count:
                TWR_pair_count[wake_pair] += 1
            
            if leader not in followersTWR:
                TWR_count[w_l] += 1
            
            TWR_count[w_f] += 1
            followersTWR.append(follower)

    return TMA_count, TMA_pair_count, TWR_count, TWR_pair_count, min_sep, min_sep_TMA, min_sep_TWR

        
def countLOA(pairs):

    min_sep = {
        "11": 0,
        "9": 0,
        "8": 0,
        "7": 0,
        "6": 0,
        "5": 0,
        "4": 0,
        "3": 0,
    }

    loa_class = {
        "HP": 0,
        "R": 0,
        "LP": 0,
        "NR+": 0,
        "NR-": 0,
        "NR": 0
    }

    loa_class_pair = {
        "HP-HP": 0,
        "HP-R": 0,
        "HP-LP": 0,
        "HP-NR+": 0,
        "HP-NR-": 0,
        "HP-NR": 0,
        "R-HP": 0,
        "R-R": 0,
        "R-LP" :0,
        "R-NR+": 0,
        "R-NR-": 0,
        "R-NR": 0,
        "LP-HP": 0,
        "LP-R": 0,
        "LP-LP": 0,
        "LP-NR+": 0,
        "LP-NR-": 0,
        "LP-NR": 0,
        "NR+-HP": 0,
        "NR+-R": 0,
        "NR+-LP": 0,
        "NR+-NR+": 0,
        "NR+-NR-": 0,
        "NR+-NR": 0,
        "NR--HP": 0,
        "NR--R": 0,
        "NR--LP": 0,
        "NR--NR+": 0,
        "NR--NR-": 0,
        "NR--NR": 0,
        "NR-HP": 0,
        "NR-R": 0,
        "NR-LP": 0,
        "NR-NR+": 0,
        "NR-NR-": 0,
        "NR-NR": 0,
    }

    sids = {
        "G1": 0,
        "G2": 0,
        "G3": 0
    }

    sids_group = {
        "G1-G1": 0,
        "G1-G2": 0,
        "G1-G3": 0,
        "G2-G2": 0,
        "G2-G3": 0,
        "G3-G3": 0
    }

    followers = []

    for p in pairs:
        leader, follower = p.pair.split("-")

        ms = str(p.min_hor_sep)
        min_sep[ms] += 1

        cl_l = p.lead_class
        cl_f = p.foll_class

        cl_comb = cl_l + "-" + cl_f

        sid_l = p.sid_lead_g
        sid_f = p.sid_foll_g

        sid_comb = sid_l + "-" + sid_f
        rev = sid_f + "-" + sid_l

        if cl_comb in loa_class_pair:
            loa_class_pair[cl_comb] += 1
        
        if sid_comb in sids_group:
            sids_group[sid_comb] += 1
        elif rev in sids_group:
            sids_group[rev] += 1

        if leader not in followers:
            loa_class[cl_l] += 1
            if sid_l != "":
                sids[sid_l] += 1
        
        loa_class[cl_f] += 1
        if sid_f != "":
            sids[sid_f] += 1
        followers.append(follower)
        
    return loa_class, loa_class_pair, sids, sids_group, min_sep


def LOA_TWR(pairs, loa_class, loa_class_pair, sids, sids_group, min_sep):
    loa_TWR_class = {k:0 for k in loa_class}
    loa_TWR_pair_class = {n:0 for n in loa_class_pair}
    sids_TWR = {r:0 for r in sids}
    sids_TWR_group = {t:0 for t in sids_group}
    min_sep_TWR = {m:0 for m in min_sep}

    followers = []

    for p in pairs:

        leader,follower = p.pair.split("-")

        ms = str(p.min_hor_sep)

        l_class = p.lead_class
        f_class = p.foll_class

        class_comb = l_class + "-" + f_class

        s_l = p.sid_lead_g
        s_f = p.sid_foll_g

        sid_comb = s_l + "-" + s_f
        rev = s_f + "-" + s_l

        if p.twr_loss == "YES":
            min_sep_TWR[ms] += 1

            if sid_comb in sids_TWR_group:
                sids_TWR_group[sid_comb] += 1
            elif rev in sids_TWR_group:
                sids_TWR_group[rev] += 1
            
            if class_comb in loa_TWR_pair_class:
                loa_TWR_pair_class[class_comb] += 1
            
            if leader not in followers:
                loa_TWR_class[l_class] += 1
                if s_l != "":
                    sids_TWR[s_l] += 1
            
            loa_TWR_class[f_class] += 1
            if s_f != "":
                sids_TWR[s_f] += 1
            followers.append(follower)
    
    return loa_TWR_class, loa_TWR_pair_class, sids_TWR, sids_TWR_group, min_sep_TWR






    


