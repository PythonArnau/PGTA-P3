import math
import re
import numpy as np


# ---------------------------------------------------------------------------
# Constants  (mirrors GeoUtils static/const fields exactly)
# ---------------------------------------------------------------------------
METERS2FEET         = 3.28084
FEET2METERS         = 0.3048
NM2METERS           = 1852.0
METERS2NM           = 1.0 / NM2METERS        # = 1 / GeoUtils.NM2METERS
DEGS2RADS           = math.pi / 180.0
RADS2DEGS           = 180.0 / math.pi
ALMOST_ZERO         = 1e-10
REQUIERED_PRECISION = 1e-8                    # typo kept intentionally from original


# ---------------------------------------------------------------------------
# Coordinate classes
# ---------------------------------------------------------------------------

class CoordinatesWGS84:
    """Geodesic coordinates: lat, lon (radians), height (meters)."""

    def __init__(self, lat=0.0, lon=0.0, height=0.0):
        self.Lat    = lat
        self.Lon    = lon
        self.Height = height

    @classmethod
    def from_degrees_str(cls, lat, lon, h):
        """Mirrors: CoordinatesWGS84(string lat, string lon, double h)"""
        return cls(float(lat) * DEGS2RADS, float(lon) * DEGS2RADS, h)

    def __repr__(self):
        d1, d2, d3, n = GeoUtils.Radians2LatLon(self.Lat)
        s = f"{int(d1):02d}:{int(d2):02d}:{d3:.4f}{'N' if n == 0 else 'S'} "
        d1, d2, d3, n = GeoUtils.Radians2LatLon(self.Lon)
        s += f"{int(d1):03d}:{int(d2):02d}:{d3:.4f}{'E' if n == 0 else 'W'} "
        s += f"{self.Height:.4f}m\n"
        s += f"lat:{self.Lat * RADS2DEGS:.9f} lon:{self.Lon * RADS2DEGS:.9f}"
        return s


class CoordinatesXYZ:
    """Cartesian / geocentric coordinates (meters)."""

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.X = x
        self.Y = y
        self.Z = z

    def __repr__(self):
        return f" X: {self.X:.4f}m Y: {self.Y:.4f}m Z: {self.Z:.4f}m"


class CoordinatesUVH:
    """Stereographic coordinates (u, v, height)."""

    def __init__(self):
        self.U      = 0.0
        self.V      = 0.0
        self.Height = 0.0


class CoordinatesXYH:
    """System x, y, height coordinates."""

    def __init__(self):
        self.X      = 0.0
        self.Y      = 0.0
        self.Height = 0.0


class CoordinatesPolar:
    """Polar coordinates: rho (m), theta (rad), elevation (rad)."""

    def __init__(self, rho=0.0, theta=0.0, elevation=0.0):
        self.Rho       = rho
        self.Theta     = theta
        self.Elevation = elevation

    def __repr__(self):
        return f" R: {self.Rho:.4f}m T: {self.Theta:.4f}rad E: {self.Elevation:.4f}rad"

    def ToStringStandard(self):
        return (f" R: {self.Rho * METERS2NM:.4f}NM"
                f" T: {self.Theta * RADS2DEGS:.4f}\xba"
                f" E: {self.Elevation * RADS2DEGS:.4f}\xba")


# ---------------------------------------------------------------------------
# GeoUtils class
# ---------------------------------------------------------------------------

class GeoUtils:
    """
    Python translation of GeoUtils.cs (v2.0 09/10/15).
    numpy ndarray is used in place of GeneralMatrix.
    All method names, variable names, and logic are kept identical to the original.
    """

    def __init__(self, E=None, A=None, centerProjection=None):
        # Instance field defaults (mirrors C# field initialisers)
        self.A  = 6378137.0
        self.B  = 6356752.3142
        self.E2 = 0.00669437999013
        self.R_S = 0.0
        self.centerProjection = None

        # Private matrix fields
        self._T1 = None   # GeneralMatrix T1
        self._R1 = None   # GeneralMatrix R1

        # Private hashtable caches (initialised to None like C# fields)
        self._rotationMatrixHT      = None
        self._translationMatrixHT   = None
        self._positionRadarMatrixHT = None
        self._rotationRadarMatrixHT = None

        # Constructor overload: GeoUtils(double E, double A)
        if E is not None and A is not None and centerProjection is None:
            self.E2 = E * E
            self.A  = A
            self.setCenterProjection(CoordinatesWGS84())

        # Constructor overload: GeoUtils(double E, double A, CoordinatesWGS84)
        elif E is not None and A is not None and centerProjection is not None:
            self.E2 = E * E
            self.A  = A
            self.setCenterProjection(centerProjection)

        # Default constructor GeoUtils() -> nothing extra

    # ------------------------------------------------------------------
    # Static parsing methods
    # ------------------------------------------------------------------

    @staticmethod
    def LatLonStringBoth2Radians(line, height=None):
        """
        Overload with height: calls base overload then sets Height.
        Overload without height: parses the coordinate string directly.
        """
        if height is not None:
            res = GeoUtils._LatLonStringBoth2Radians_base(line)
            res.Height = height
            return res
        return GeoUtils._LatLonStringBoth2Radians_base(line)

    @staticmethod
    def _LatLonStringBoth2Radians_base(line):
        pattern = (r"([-+]?)([0-9]+):([0-9]+):([0-9][0-9]*[.]*[0-9]+)([NS]?)"
                   r"\s+([-+]?)([0-9]+):([0-9]+):([0-9][0-9]*[.]*[0-9]+)([EW]?)"
                   r"[\s]*([0-9][0-9]*[.]*[0-9]+)?[.]*")

        latMinus = lonMinus = latNS = lonEW = ""
        lat1 = lat2 = lat3 = lon1 = lon2 = lon3 = height = 0.0

        try:
            # we use float() because Python always uses dot as decimal separator
            # (equivalent to InvariantInfo in C#)
            matches = re.match(pattern, line)
            if matches is None:
                raise ValueError("No match")

            latMinus = matches.group(1)
            lat1     = float(matches.group(2))
            lat2     = float(matches.group(3))
            lat3     = float(matches.group(4))
            latNS    = matches.group(5)

            lonMinus = matches.group(6)
            lon1     = float(matches.group(7))
            lon2     = float(matches.group(8))
            lon3     = float(matches.group(9))
            lonEW    = matches.group(10)

            if matches.group(11) is not None:
                height = float(matches.group(11))
            else:
                height = 0.0

        except Exception as e:
            raise RuntimeError(
                f"expecting line({line}) to be accomply with the following regex:\n"
                f"{pattern}\n"
                "more or less the following valid wgs84 strings will be correctly parsed "
                "(no negative heights):\n"
                "-00:20:23.98 +003:45:33 897.09m\n"
                "0:20:23.98S 03:45:33E 897\n"
                "00:20:23.98S 3:45:33E\n"
                f"ERROR LatLonStringBoth2Radians(string line): {e}"
            )

        res = CoordinatesWGS84()
        n = 0
        if (len(latMinus) > 0 and latMinus[0] == "-") or latNS == "S":
            n = 1
            if lat1 < 0:
                lat1 *= -1  # quitamos el menos porque ya lo vamos a hacer con el parametro n
        res.Lat = GeoUtils.LatLon2Radians(lat1, lat2, lat3, n)

        n = 0
        if (len(lonMinus) > 0 and lonMinus[0] == "-") or lonEW == "W":
            n = 1
            if lon1 < 0:
                lon1 *= -1  # quitamos el menos porque ya lo vamos a hacer con el parametro n
        res.Lon = GeoUtils.LatLon2Radians(lon1, lon2, lon3, n)
        res.Height = height
        return res

    @staticmethod
    def LatLon2Degrees(d1, d2, d3, ns):
        d = d1 + (d2 / 60.0) + (d3 / 3600.0)
        if ns == 1:
            d *= -1.0
        return d

    @staticmethod
    def LatLon2Radians(d1, d2, d3, ns):
        d = d1 + (d2 / 60.0) + (d3 / 3600.0)
        if ns == 1:
            d *= -1.0
        return d * DEGS2RADS

    @staticmethod
    def LatLonString2Degrees(s1, s2, s3, ns):
        d = 0.0
        try:
            d1 = float(s1)
            d2 = float(s2)
            d3 = float(s3)
            d = GeoUtils.LatLon2Degrees(d1, d2, d3, ns)
        except ValueError:
            pass
        return d

    @staticmethod
    def Degrees2LatLon(d):
        """Returns (d1, d2, d3, ns) -- mirrors C# out parameters."""
        if d < 0:
            d *= -1.0
            ns = 1
        else:
            ns = 0
        d1 = math.floor(d)
        d2 = math.floor((d - d1) * 60.0)
        d3 = (((d - d1) * 60.0) - d2) * 60.0
        return d1, d2, d3, ns

    @staticmethod
    def Radians2LatLon(d):
        """Returns (d1, d2, d3, ns) -- mirrors C# out parameters."""
        d *= RADS2DEGS
        if d < 0:
            d *= -1.0
            ns = 1
        else:
            ns = 0
        d1 = math.floor(d)
        d2 = math.floor((d - d1) * 60.0)
        d3 = (((d - d1) * 60.0) - d2) * 60.0
        return d1, d2, d3, ns

    @staticmethod
    def CenterCoordinates(l):
        maxLat = maxLon = maxHeight = -999.0
        minLat = minLon = 999.0
        if l is not None and len(l) > 0:
            for c in l:
                if maxLat    < c.Lat:    maxLat    = c.Lat
                if maxLon    < c.Lon:    maxLon    = c.Lon
                if minLat    > c.Lat:    minLat    = c.Lat
                if minLon    > c.Lon:    minLon    = c.Lon
                if maxHeight < c.Height: maxHeight = c.Height  # wont be used for setCenterProjection
            res        = CoordinatesWGS84()
            res.Lat    = (maxLat + minLat) / 2.0
            res.Lon    = (maxLon + minLon) / 2.0
            res.Height = maxHeight
            return res
        else:
            return None

    # ------------------------------------------------------------------
    # Instance: geodesic <-> geocentric
    # ------------------------------------------------------------------

    def change_geodesic2geocentric(self, c):
        if c is None:
            return None
        res   = CoordinatesXYZ()
        nu    = self.A / math.sqrt(1 - self.E2 * math.sin(c.Lat) ** 2)
        res.X = (nu + c.Height) * math.cos(c.Lat) * math.cos(c.Lon)
        res.Y = (nu + c.Height) * math.cos(c.Lat) * math.sin(c.Lon)
        res.Z = (nu * (1 - self.E2) + c.Height) * math.sin(c.Lat)
        return res

    def change_geocentric2geodesic(self, c):
        if c is None:
            return None
        res = CoordinatesWGS84()
        # semi-minor earth axis
        # double b = self.A * math.sqrt(1 - self.E2)
        b = 6356752.3142

        if (abs(c.X) < ALMOST_ZERO) and (abs(c.Y) < ALMOST_ZERO):
            if abs(c.Z) < ALMOST_ZERO:
                # the point is at the center of earth :)
                res.Lat = math.pi / 2.0
            else:
                res.Lat = (math.pi / 2.0) * ((c.Z / abs(c.Z)) + 0.5)
            res.Lon    = 0
            res.Height = abs(c.Z) - b
            return res

        d_xy    = math.sqrt(c.X * c.X + c.Y * c.Y)
        # from formula 20
        res.Lat = math.atan((c.Z / d_xy) /
                            (1 - (self.A * self.E2) / math.sqrt(d_xy * d_xy + c.Z * c.Z)))
        # from formula 24
        nu = self.A / math.sqrt(1 - self.E2 * math.sin(res.Lat) ** 2)
        # from formula 20
        res.Height = (d_xy / math.cos(res.Lat)) - nu

        # iteration from formula 20b
        Lat_over = -0.1 if res.Lat >= 0 else 0.1

        loop_count = 0
        while (abs(res.Lat - Lat_over) > REQUIERED_PRECISION) and (loop_count < 50):
            loop_count += 1
            Lat_over   = res.Lat
            res.Lat    = math.atan(
                (c.Z * (1 + res.Height / nu)) /
                (d_xy * ((1 - self.E2) + (res.Height / nu)))
            )
            nu         = self.A / math.sqrt(1 - self.E2 * math.sin(res.Lat) ** 2)
            res.Height = d_xy / math.cos(res.Lat) - nu

        res.Lon = math.atan2(c.Y, c.X)
        # if loop_count == 50: # exception
        return res

    # ------------------------------------------------------------------
    # Instance: center projection
    # ------------------------------------------------------------------

    def setCenterProjection(self, c):
        if c is None:
            return None

        # we create a new instance of c2. we need to modify c, and we don't
        # want the change to be bounced back to the caller. (classes are always
        # passed as ref)
        # we set the height = 0 because the center of our projections will be
        # the ground. this is because all the height are referred to ground (AMSL?),
        # not to the top of a mountain.
        c2 = CoordinatesWGS84(c.Lat, c.Lon, 0)  # c.Height
        self.centerProjection = c2
        nu = self.A / math.sqrt(1 - self.E2 * math.sin(c2.Lat) ** 2)  # calculated but not used -- same as original

        self.R_S = (self.A * (1.0 - self.E2)) / \
                   (1 - self.E2 * math.sin(c2.Lat) ** 2) ** 1.5

        # alternative implementation as per wikipedia article.
        # doesn't give the same result! probably doesn't work. NOT TO BE USED, NEVER!
        # R(f)^2 = ( a^4 cos(f)^2 + b^4 sin(f)^2 ) / ( a^2 cos(f)^2 + b^2 sin(f)^2 ).

        self._T1 = GeoUtils.CalculateTranslationMatrix(c2, self.A, self.E2)
        self._R1 = GeoUtils.CalculateRotationMatrix(c2.Lat, c2.Lon)

        return self.centerProjection

    def getCenterProjection(self):
        return self.centerProjection

    # ------------------------------------------------------------------
    # Instance: geocentric <-> system cartesian
    # ------------------------------------------------------------------

    def change_geocentric2system_cartesian(self, geo):
        if self.centerProjection is None or self._R1 is None \
                or self._T1 is None or geo is None:
            return None

        coefInput = np.array([[geo.X], [geo.Y], [geo.Z]], dtype=float)  # inputMatrix

        coefInput -= self._T1               # inputMatrix.SubtractEquals(this.T1)
        R2 = self._R1 @ coefInput           # this.R1.Multiply(inputMatrix)

        return CoordinatesXYZ(R2[0, 0], R2[1, 0], R2[2, 0])

    def change_system_cartesian2geocentric(self, car):
        if car is None:
            return None

        coefInput = np.array([[car.X], [car.Y], [car.Z]], dtype=float)  # inputMatrix

        R2 = self._R1.T                     # this.R1.Transpose()
        R3 = R2 @ coefInput                 # R2.Multiply(inputMatrix)
        R3 = R3 + self._T1                  # R3.AddEquals(this.T1)

        return CoordinatesXYZ(R3[0, 0], R3[1, 0], R3[2, 0])

    # ------------------------------------------------------------------
    # Instance: system cartesian <-> stereographic
    # ------------------------------------------------------------------

    def change_system_xyh2system_z(self, c):
        z = 0.0
        if c is None:
            return 0.0

        xh   = c.X / (self.R_S + c.Height)
        yh   = c.Y / (self.R_S + c.Height)
        temp = xh * xh + yh * yh
        if temp > 1:
            z = -(self.R_S + self.centerProjection.Height)
        else:
            z = (self.R_S + c.Height) * math.sqrt(1.0 - temp) - \
                (self.R_S + self.centerProjection.Height)
        return z

    def change_system_cartesian2stereographic(self, c):
        if c is None:
            return None
        # don't know why we have to do this ?
        # z = self.change_system_xyh2system_z(c)

        res        = CoordinatesUVH()
        d_xy2      = c.X * c.X + c.Y * c.Y
        res.Height = math.sqrt(
            d_xy2 +
            (c.Z + self.centerProjection.Height + self.R_S) *
            (c.Z + self.centerProjection.Height + self.R_S)
        ) - self.R_S
        k     = (2 * self.R_S) / \
                (2 * self.R_S + self.centerProjection.Height + c.Z + res.Height)
        res.U = k * c.X
        res.V = k * c.Y
        return res

    def change_stereographic2system_cartesian(self, c):
        if c is None:
            return None

        res   = CoordinatesXYZ()
        d_uv2 = c.U * c.U + c.V * c.V
        res.Z = (c.Height + self.R_S) * \
                ((4 * self.R_S * self.R_S - d_uv2) /
                 (4 * self.R_S * self.R_S + d_uv2)) - \
                (self.R_S + self.centerProjection.Height)
        k     = (2 * self.R_S) / \
                (2 * self.R_S + self.centerProjection.Height + res.Z + c.Height)
        res.X = c.U / k
        res.Y = c.V / k
        # we should not use Z because z=0 by the equations, but we need it
        # if we're going back and fore
        # res.Z = 0
        return res

    # ------------------------------------------------------------------
    # Static: elevation and azimuth
    # ------------------------------------------------------------------

    @staticmethod
    def CalculateElevation(centerCoordinates, R, rho, h):
        if (rho < ALMOST_ZERO) or (R == -1.0) or (centerCoordinates is None):
            # when rho < 0 and rho = 0 a division by zero could happen
            return 0
        else:
            temp = (2 * R *
                    (h - centerCoordinates.Height) + h * h -
                    centerCoordinates.Height * centerCoordinates.Height - rho * rho) / \
                   (2 * rho * (R + centerCoordinates.Height))
            if (temp > -1.0) and (temp < 1.0):
                return math.asin(temp)
            else:
                return math.pi / 2.0

    @staticmethod
    def CalculateAzimuth(x, y):
        if abs(y) < ALMOST_ZERO:
            theta = (x / abs(x)) * math.pi / 2.0
        else:
            theta = math.atan2(x, y)

        if theta < 0.0:
            theta += 2 * math.pi
        return theta

    # ------------------------------------------------------------------
    # Instance: earth radius
    # ------------------------------------------------------------------

    def CalculateEarthRadius(self, geo):
        ret = float("nan")   # Double.NaN
        if geo is not None:
            # Radius of curvature in Meridian
            ret = (self.A * (1.0 - self.E2)) / \
                  (1 - self.E2 * math.sin(geo.Lat) ** 2) ** 1.5
        return ret

    # ------------------------------------------------------------------
    # Static: matrix helpers
    # ------------------------------------------------------------------

    @staticmethod
    def CalculateRotationMatrix(lat, lon):
        coefR1 = np.zeros((3, 3), dtype=float)

        coefR1[0][0] = -(math.sin(lon))
        coefR1[0][1] =   math.cos(lon)
        coefR1[0][2] = 0
        coefR1[1][0] = -(math.sin(lat) * math.cos(lon))
        coefR1[1][1] = -(math.sin(lat) * math.sin(lon))
        coefR1[1][2] =   math.cos(lat)
        coefR1[2][0] =   math.cos(lat) * math.cos(lon)
        coefR1[2][1] =   math.cos(lat) * math.sin(lon)
        coefR1[2][2] =   math.sin(lat)
        return coefR1

    @staticmethod
    def CalculateTranslationMatrix(c, A, E2):
        nu = A / math.sqrt(1 - E2 * math.sin(c.Lat) ** 2)
        coefT1 = np.array([
            [(nu + c.Height) * math.cos(c.Lat) * math.cos(c.Lon)],
            [(nu + c.Height) * math.cos(c.Lat) * math.sin(c.Lon)],
            [(nu * (1 - E2) + c.Height) * math.sin(c.Lat)],
        ], dtype=float)
        return coefT1

    @staticmethod
    def CalculatePositionRadarMatrix(T1, t, r):
        R1  = T1 - t      # T1.Subtract(t)
        res = r @ R1      # r.Multiply(R1)
        return res

    @staticmethod
    def CalculateRotationRadarMatrix(R1, r):
        R2  = R1.T        # R1.Transpose()
        res = r @ R2      # r.Multiply(R2)
        return res

    # ------------------------------------------------------------------
    # Static: radar spherical <-> radar cartesian
    # ------------------------------------------------------------------

    @staticmethod
    def change_radar_spherical2radar_cartesian(polarCoordinates):
        if polarCoordinates is None:
            return None

        res   = CoordinatesXYZ()
        res.X = polarCoordinates.Rho * math.cos(polarCoordinates.Elevation) * \
                math.sin(polarCoordinates.Theta)
        res.Y = polarCoordinates.Rho * math.cos(polarCoordinates.Elevation) * \
                math.cos(polarCoordinates.Theta)
        res.Z = polarCoordinates.Rho * math.sin(polarCoordinates.Elevation)
        return res

    @staticmethod
    def change_radar_cartesian2radar_spherical(cartesianCoordinates):
        if cartesianCoordinates is None:
            return None

        res           = CoordinatesPolar()
        res.Rho       = math.sqrt(cartesianCoordinates.X * cartesianCoordinates.X +
                                  cartesianCoordinates.Y * cartesianCoordinates.Y +
                                  cartesianCoordinates.Z * cartesianCoordinates.Z)
        res.Theta     = GeoUtils.CalculateAzimuth(cartesianCoordinates.X,
                                                  cartesianCoordinates.Y)
        res.Elevation = math.asin(cartesianCoordinates.Z / res.Rho)
        return res

    # ------------------------------------------------------------------
    # Instance: radar cartesian <-> geocentric
    # ------------------------------------------------------------------

    def change_radar_cartesian2geocentric(self, radarCoordinates, cartesianCoordinates):
        # at_radar_local_to_geocentric
        translationMatrix = self._ObtainTranslationMatrix(radarCoordinates)
        rotationMatrix    = self._ObtainRotationMatrix(radarCoordinates)

        coefInput = np.array([
            [cartesianCoordinates.X],
            [cartesianCoordinates.Y],
            [cartesianCoordinates.Z],
        ], dtype=float)

        R1 = rotationMatrix.T           # rotationMatrix.Transpose()
        R2 = R1 @ coefInput             # R1.Multiply(inputMatrix)
        R2 = R2 + translationMatrix     # R2.AddEquals(translationMatrix)

        return CoordinatesXYZ(R2[0, 0], R2[1, 0], R2[2, 0])

    def change_geocentric2radar_cartesian(self, radarCoordinates, geocentricCoordinates):
        # at_radar_local_to_geocentric
        translationMatrix = self._ObtainTranslationMatrix(radarCoordinates)
        rotationMatrix    = self._ObtainRotationMatrix(radarCoordinates)

        coefInput = np.array([
            [geocentricCoordinates.X],
            [geocentricCoordinates.Y],
            [geocentricCoordinates.Z],
        ], dtype=float)

        coefInput -= translationMatrix          # inputMatrix.SubtractEquals(translationMatrix)
        R1 = rotationMatrix @ coefInput         # rotationMatrix.Multiply(inputMatrix)

        return CoordinatesXYZ(R1[0, 0], R1[1, 0], R1[2, 0])

    # ------------------------------------------------------------------
    # Instance: radar cartesian <-> system cartesian
    # ------------------------------------------------------------------

    def change_radar_cartesian2system_cartesian(self, radarCoordinates, cartesianCoordinates):
        # at_radar_local_to_system
        positionRadarMatrix = self._ObtainPositionRadarMatrix(radarCoordinates)
        rotationRadarMatrix = self._ObtainRotationRadarMatrix(radarCoordinates)

        coefInput = np.array([
            [cartesianCoordinates.X],
            [cartesianCoordinates.Y],
            [cartesianCoordinates.Z],
        ], dtype=float)

        coefInput -= positionRadarMatrix        # inputMatrix.SubtractEquals(positionRadarMatrix)
        R1 = rotationRadarMatrix @ coefInput    # rotationRadarMatrix.Multiply(inputMatrix)

        return CoordinatesXYZ(R1[0, 0], R1[1, 0], R1[2, 0])

    def change_system_cartesian2radar_cartesian(self, radarCoordinates, cartesianCoordinates):
        # at_system_to_radar_local
        positionRadarMatrix = self._ObtainPositionRadarMatrix(radarCoordinates)
        rotationRadarMatrix = self._ObtainRotationRadarMatrix(radarCoordinates)

        coefInput = np.array([
            [cartesianCoordinates.X],
            [cartesianCoordinates.Y],
            [cartesianCoordinates.Z],
        ], dtype=float)

        R1 = rotationRadarMatrix @ coefInput    # rotationRadarMatrix.Multiply(inputMatrix)
        R1 = R1 + positionRadarMatrix           # R1.AddEquals(positionRadarMatrix)

        return CoordinatesXYZ(R1[0, 0], R1[1, 0], R1[2, 0])

    # ------------------------------------------------------------------
    # Private cache helpers  (mirror C# ObtainXxx methods)
    # C# uses object reference equality for dict keys -- we use id(obj)
    # ------------------------------------------------------------------

    def _ObtainRotationMatrix(self, radarCoordinates):
        if self._rotationMatrixHT is None:
            self._rotationMatrixHT = {}
        key = id(radarCoordinates)
        if key in self._rotationMatrixHT:
            rotationMatrix = self._rotationMatrixHT[key]
        else:
            rotationMatrix = GeoUtils.CalculateRotationMatrix(radarCoordinates.Lat,
                                                              radarCoordinates.Lon)
            self._rotationMatrixHT[key] = rotationMatrix
        return rotationMatrix

    def _ObtainTranslationMatrix(self, radarCoordinates):
        if self._translationMatrixHT is None:
            self._translationMatrixHT = {}
        key = id(radarCoordinates)
        if key in self._translationMatrixHT:
            translationMatrix = self._translationMatrixHT[key]
        else:
            translationMatrix = GeoUtils.CalculateTranslationMatrix(radarCoordinates,
                                                                     self.A, self.E2)
            self._translationMatrixHT[key] = translationMatrix
        return translationMatrix

    def _ObtainPositionRadarMatrix(self, radarCoordinates):
        if self._positionRadarMatrixHT is None:
            self._positionRadarMatrixHT = {}
        key = id(radarCoordinates)
        if key in self._positionRadarMatrixHT:
            p = self._positionRadarMatrixHT[key]
        else:
            p = GeoUtils.CalculatePositionRadarMatrix(
                self._T1,
                self._ObtainTranslationMatrix(radarCoordinates),
                self._ObtainRotationMatrix(radarCoordinates),
            )
            self._positionRadarMatrixHT[key] = p
        return p

    def _ObtainRotationRadarMatrix(self, radarCoordinates):
        if self._rotationRadarMatrixHT is None:
            self._rotationRadarMatrixHT = {}
        key = id(radarCoordinates)
        if key in self._rotationRadarMatrixHT:
            p = self._rotationRadarMatrixHT[key]
        else:
            p = GeoUtils.CalculateRotationRadarMatrix(
                self._R1,
                self._ObtainRotationMatrix(radarCoordinates),
            )
            self._rotationRadarMatrixHT[key] = p
        return p
