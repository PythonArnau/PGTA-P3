from geo_utils import GeoUtils, CoordinatesWGS84, CoordinatesUVH
import numpy as np

# TMA LEBL: 41°6'56.560"N  1°41'33.010"E
LAT_TMA  = GeoUtils.LatLon2Radians(41, 6, 56.560, 0)  
LON_TMA  = GeoUtils.LatLon2Radians(1, 41, 33.010, 0)  

def Calc_Stereographical_Coords(lat, lon, alt):
    # Inicializar GeoUtils con el centro de proyección = tangencia TMA
    center = CoordinatesWGS84(LAT_TMA, LON_TMA, 0)  # height=0 lo fija setCenterProjection
    geo = GeoUtils()
    geo.setCenterProjection(center)

    coords = []
    for i in range(len(lat)):
        # 1. Geodésico → geocéntrico
        wgs = CoordinatesWGS84(
            lat[i] * np.pi / 180,   
            lon[i] * np.pi / 180,
            alt[i]
        )
        geocentric = geo.change_geodesic2geocentric(wgs)

        # 2. Geocéntrico → cartesiano del sistema
        system_cart = geo.change_geocentric2system_cartesian(geocentric)

        # 3. Cartesiano del sistema → estereográfico
        uvh = geo.change_system_cartesian2stereographic(system_cart)

        cd = CoordinatesUVH()
        cd.U      = uvh.U
        cd.V      = uvh.V
        cd.Height = alt[i]   
        coords.append(cd)

    return coords


def TowerCoords(lat, lon):
    # Mismo proceso pero centrado en el ARP LEBL, sin altura
    center = CoordinatesWGS84(LAT_TMA, LON_TMA, 0)
    geo = GeoUtils()
    geo.setCenterProjection(center)

    wgs         = CoordinatesWGS84(lat * np.pi / 180, lon * np.pi / 180, 0.0)
    geocentric  = geo.change_geodesic2geocentric(wgs)
    system_cart = geo.change_geocentric2system_cartesian(geocentric)
    uvh         = geo.change_system_cartesian2stereographic(system_cart)

    cd = CoordinatesUVH()
    cd.U      = uvh.U
    cd.V      = uvh.V
    cd.Height = 0.0
    return [cd]