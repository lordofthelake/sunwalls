package io.noemata.sunwalls;

import android.content.Context;
import android.content.SharedPreferences;

final class Prefs {
    static final String[] THEMES = {"ringfall", "tidewater", "meridian", "canopy"};
    static final String[] NAMES = {"Ringfall", "Tidewater", "Meridian", "Canopy"};
    static SharedPreferences get(Context c) { return c.getSharedPreferences("cfg", Context.MODE_PRIVATE); }
    static String theme(Context c) { return get(c).getString("theme", "tidewater"); }
    static double lat(Context c) { return Double.longBitsToDouble(get(c).getLong("lat", Double.doubleToLongBits(Sun.DEFAULT_LAT))); }
    static double lon(Context c) { return Double.longBitsToDouble(get(c).getLong("lon", Double.doubleToLongBits(Sun.DEFAULT_LON))); }
    static String asset(String theme, int frame) { return String.format("%s_%02d.jpg", theme, frame); }
}
