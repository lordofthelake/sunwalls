package io.noemata.sunwalls;

import android.Manifest;
import android.app.Activity;
import android.app.WallpaperManager;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.location.Location;
import android.location.LocationManager;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.InputStream;
import java.util.Locale;

public class MainActivity extends Activity {
    private ImageView preview;
    private TextView info;
    private final Button[] themeButtons = new Button[Prefs.THEMES.length];

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);

        FrameLayout root = new FrameLayout(this);
        preview = new ImageView(this);
        preview.setScaleType(ImageView.ScaleType.CENTER_CROP);
        root.addView(preview, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(20);
        panel.setPadding(pad, pad, pad, pad);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(0xAA0B1028); bg.setCornerRadius(dp(24));
        panel.setBackground(bg);

        TextView title = new TextView(this);
        title.setText("Sunwalls"); title.setTextColor(Color.WHITE); title.setTextSize(22); title.setTypeface(Typeface.DEFAULT_BOLD);
        panel.addView(title);
        info = new TextView(this);
        info.setTextColor(0xCCFFFFFF); info.setTextSize(13); info.setPadding(0, dp(4), 0, dp(14));
        panel.addView(info);

        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        for (int i = 0; i < Prefs.THEMES.length; i++) {
            String t = Prefs.THEMES[i];
            Button btn = pill(Prefs.NAMES[i]); btn.setTextSize(12);
            btn.setOnClickListener(new Click(this, "theme:" + t));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, dp(48), 1); lp.setMargins(dp(3), 0, dp(3), 0);
            row.addView(btn, lp);
            themeButtons[i] = btn;
        }
        panel.addView(row);

        Button loc = pill("Use my location");
        loc.setOnClickListener(new Click(this, "loc"));
        LinearLayout.LayoutParams llp = new LinearLayout.LayoutParams(-1, -2); llp.topMargin = dp(10);
        panel.addView(loc, llp);

        Button set = pill("Set as wallpaper");
        set.setOnClickListener(new Click(this, "set"));
        ((GradientDrawable) set.getBackground()).setColor(0xFFF2C6A0);
        set.setTextColor(0xFF1B1F3A);
        panel.addView(set, llp);

        FrameLayout.LayoutParams plp = new FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM);
        plp.setMargins(dp(16), 0, dp(16), dp(40));
        root.addView(panel, plp);
        setContentView(root);
        refresh();
    }

    @Override protected void onResume() { super.onResume(); refresh(); }

    private Button pill(String text) {
        Button b = new Button(this);
        b.setText(text); b.setAllCaps(false); b.setTextColor(Color.WHITE); b.setTextSize(13);
        b.setSingleLine(true); b.setEllipsize(android.text.TextUtils.TruncateAt.END); b.setPadding(dp(4), 0, dp(4), 0); b.setMinWidth(0); b.setMinimumWidth(0);
        GradientDrawable d = new GradientDrawable(); d.setCornerRadius(dp(18)); d.setColor(0x33FFFFFF);
        b.setBackground(d); b.setStateListAnimator(null);
        return b;
    }

    private void refresh() {
        String theme = Prefs.theme(this);
        double lat = Prefs.lat(this), lon = Prefs.lon(this);
        long now = System.currentTimeMillis();
        int idx = Sun.frameFor(now, lat, lon);
        double[] p = Sun.position(now, lat, lon);
        try (InputStream in = getAssets().open(Prefs.asset(theme, idx))) {
            preview.setImageBitmap(BitmapFactory.decodeStream(in));
        } catch (Exception ignored) {}
        info.setText(String.format(Locale.US, "Sun %.0f° high, %.0f° azimuth · frame %d/16 · %.2f, %.2f",
                p[0], p[1], idx + 1, lat, lon));
        for (int i = 0; i < themeButtons.length; i++)
            ((GradientDrawable) themeButtons[i].getBackground()).setColor(Prefs.THEMES[i].equals(theme) ? 0x88FFFFFF : 0x33FFFFFF);
    }

    void onAction(String what) {
        if (what.startsWith("theme:")) { Prefs.get(this).edit().putString("theme", what.substring(6)).apply(); refresh(); }
        else if (what.equals("loc")) askLocation();
        else {
            Intent in = new Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER);
            in.putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT, new ComponentName(this, SunWallpaperService.class));
            startActivity(in);
        }
    }

    private void askLocation() {
        if (checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION}, 1);
            return;
        }
        LocationManager lm = getSystemService(LocationManager.class);
        Location best = null;
        for (String prov : lm.getProviders(true)) {
            try {
                Location l = lm.getLastKnownLocation(prov);
                if (l != null && (best == null || l.getTime() > best.getTime())) best = l;
            } catch (SecurityException ignored) {}
        }
        if (best == null) { info.setText("No recent location yet — open Maps once, then try again."); return; }
        // store rounded to ~1 km; only the sun angle matters
        Prefs.get(this).edit()
                .putLong("lat", Double.doubleToLongBits(Math.round(best.getLatitude() * 100) / 100.0))
                .putLong("lon", Double.doubleToLongBits(Math.round(best.getLongitude() * 100) / 100.0)).apply();
        refresh();
    }

    @Override public void onRequestPermissionsResult(int rc, String[] p, int[] r) {
        if (r.length > 0 && r[0] == PackageManager.PERMISSION_GRANTED) askLocation();
    }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }
}

final class Click implements View.OnClickListener {
    private final MainActivity a; private final String what;
    Click(MainActivity a, String what) { this.a = a; this.what = what; }
    public void onClick(View v) { a.onAction(what); }
}
