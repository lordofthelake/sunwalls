package io.noemata.sunwalls;

import java.util.Calendar;
import java.util.TimeZone;

/** Sun position (NOAA approximation) and frame matching, same idea as macOS solar wallpapers. */
public final class Sun {
    // Defaults: Berlin. The app can store another location in prefs.
    public static final double DEFAULT_LAT = 52.52, DEFAULT_LON = 13.405;

    /** Altitude/azimuth (degrees) each frame was drawn for: 52.5°N at the equinox. Must match the renderer. */
    static final double[][] FRAMES = {
        {-37.12, 350.58}, {-17.72, 65.39}, {-9.07, 78.0}, {-2.28, 87.02},
        {4.56, 95.96}, {17.72, 114.61}, {31.82, 143.96}, {37.5, 180.0},
        {31.82, 216.04}, {21.75, 238.67}, {11.28, 254.93}, {4.56, 264.04},
        {-2.28, 272.98}, {-9.07, 282.0}, {-17.72, 294.61}, {-28.88, 315.96}};

    /** returns {altitude, azimuth} in degrees for the given UTC millis. */
    public static double[] position(long utcMillis, double lat, double lon) {
        Calendar c = Calendar.getInstance(TimeZone.getTimeZone("UTC"));
        c.setTimeInMillis(utcMillis);
        int doy = c.get(Calendar.DAY_OF_YEAR);
        double hour = c.get(Calendar.HOUR_OF_DAY) + c.get(Calendar.MINUTE) / 60.0 + c.get(Calendar.SECOND) / 3600.0;
        double g = 2 * Math.PI / 365.0 * (doy - 1 + (hour - 12) / 24.0);
        double eqt = 229.18 * (0.000075 + 0.001868 * Math.cos(g) - 0.032077 * Math.sin(g)
                - 0.014615 * Math.cos(2 * g) - 0.040849 * Math.sin(2 * g));
        double decl = 0.006918 - 0.399912 * Math.cos(g) + 0.070257 * Math.sin(g) - 0.006758 * Math.cos(2 * g)
                + 0.000907 * Math.sin(2 * g) - 0.002697 * Math.cos(3 * g) + 0.00148 * Math.sin(3 * g);
        double tst = hour * 60 + eqt + 4 * lon;               // true solar time, minutes
        double ha = Math.toRadians(tst / 4 - 180);           // hour angle
        double phi = Math.toRadians(lat);
        double cosZen = Math.sin(phi) * Math.sin(decl) + Math.cos(phi) * Math.cos(decl) * Math.cos(ha);
        cosZen = Math.max(-1, Math.min(1, cosZen));
        double zen = Math.acos(cosZen);
        double alt = 90 - Math.toDegrees(zen);
        double az = Math.toDegrees(Math.atan2(Math.sin(ha),
                Math.cos(ha) * Math.sin(phi) - Math.tan(decl) * Math.cos(phi))) + 180;
        return new double[]{alt, (az + 360) % 360};
    }

    /** Pick the frame on the same side of the day (morning/afternoon) whose sun altitude is closest.
     *  Altitude decides the light; azimuth only tells sunrise from sunset, so summer's far-north
     *  sunrises and sunsets still map to the dawn and dusk frames. */
    public static int frameFor(long utcMillis, double lat, double lon) {
        double[] p = position(utcMillis, lat, lon);
        boolean morning = p[1] < 180;
        int best = 0; double bestD = 1e9;
        for (int i = 0; i < FRAMES.length; i++) {
            boolean fm = FRAMES[i][1] < 180, noonOrMidnight = (i == 0 || i == 7);
            if (!noonOrMidnight && fm != morning) continue;
            double d = Math.abs(FRAMES[i][0] - p[0]);
            if (d < bestD) { bestD = d; best = i; }
        }
        return best;
    }

    private static double[] vec(double altDeg, double azDeg) {
        double a = Math.toRadians(altDeg), z = Math.toRadians(azDeg);
        return new double[]{Math.cos(a) * Math.sin(z), Math.cos(a) * Math.cos(z), Math.sin(a)};
    }
}
