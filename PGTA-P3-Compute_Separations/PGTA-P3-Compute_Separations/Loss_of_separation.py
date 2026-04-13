import pandas as pd

def Radar(flights, alt):
    info_separation= {
        "Pair" : [], 
        "Relative Time" : [],
        "Horizontal Separation" : [],
        "Altitude Separation" : [],
        "Separation Loss" : []
    }
    for pair in flights:
        info_separation["Pair"].append(f"{pair.leader_callsign}-{pair.follower_callsign}")
        for sample in pair.samples:
            info_separation["Relative Time"].append(sample.relative_time)
            info_separation["Horizontal Separation"].append(sample.dist_nm)
            info_separation["Altitude Separation"].append(sample.diff_alt_ft)

            if (sample.dist_nm < 3) and (sample.diff_alt_ft >= 1000):
                 info_separation["Separation Loss"].append("HORIZONTAL SEPARATION LOSS")
            
            elif (sample.dist_nm < 3) and (sample.diff_alt_ft < 1000):
                 info_separation["Separation Loss"].append("OPERATIONAL LOSS")
            
            elif sample.dist_nm >= 3:
                 info_separation["Separation Loss"].append("NO")
                 


