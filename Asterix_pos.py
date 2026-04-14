import pandas as pd
import geoutils as ge
import latlon as ltln
from pyproj import Proj, Transformer

class Stereographical_Coords:
    def __init__(self):
        self.x: float = 0.0
        self.y: float = 0.0
        self.z: float = 0.0

def Calc_Stereographical_Coords(lat, lon, alt):
    # Coordenadas referencia (ARP LEBL)
    arp_lebl = ltln.LatLon(ltln.Latitude(degree=41, minute=17, second=19), ltln.Longitude(degree=2, minute=4, second=42)) 
    print(arp_lebl)

    latref = float(arp_lebl.lat)
    longref = float(arp_lebl.lon)
    altref = 4.0

    transformer = Transformer.from_crs("EPSG:4326", "+proj=stere +lat_0="+str(latref)+" +lon_0="+str(longref)+" +ellps=WGS84", always_xy=True)

    coords=[]

    i=0
    lat_length=len(lat)
    for l in range(lat_length):
        x, y = transformer.transform(lon[i],lat[i])
        z = alt[i] - altref
        cd = Stereographical_Coords()
        cd.x = x
        cd.y = y
        cd.z = z

        coords.append(cd)
        i = i+1

    return coords

def ExtractLatLonAlt(dictionary):
    lat_vec = []
    lon_vec = []
    alt_vec = []
    for object in dictionary:
        lat_vec.append(object.lat)
        lon_vec.append(object.lon)
        alt_vec.append(object.h_m)
    
    return lat_vec, lon_vec, alt_vec

def AddAsterixCSV(csv_file:str, coords):
    x_vec = []
    y_vec = []
    z_vec = []

    for coord in coords:
        x_vec.append(coord.x)
        y_vec.append(coord.y)
        z_vec.append(coord.z)
    
    df = pd.read_csv(csv_file, sep=';', decimal=',')

    df['x'] = x_vec
    df['y'] = y_vec
    df['z'] = z_vec

    df.to_csv(csv_file, sep=';', decimal=',', index=False)


def TowerCoords(lat, lon):
    # Coordenadas referencia (ARP LEBL)
    arp_lebl = ltln.LatLon(ltln.Latitude(degree=41, minute=17, second=19), ltln.Longitude(degree=2, minute=4, second=42)) 
    print(arp_lebl)

    latref = float(arp_lebl.lat)
    longref = float(arp_lebl.lon)

    transformer = Transformer.from_crs("EPSG:4326", "+proj=stere +lat_0="+str(latref)+" +lon_0="+str(longref)+" +ellps=WGS84", always_xy=True)

    coords=[]

    x, y = transformer.transform(lon,lat)
       
    cd = Stereographical_Coords()
    cd.x = x
    cd.y = y
    cd.z = 0

    coords.append(cd)
    
    return coords
    

    