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
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.Switch;
import android.widget.TextView;

import java.io.InputStream;
import java.util.Locale;

public class MainActivity extends Activity {
    private ImageView preview;
    private TextView info, hint;
    private LinearLayout panel, manualRow;
    private Switch autoSwitch;
    private EditText latField, lonField;
    private Button setBtn;
    private final Button[] themeButtons = new Button[Prefs.THEMES.length];

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);
        getWindow().setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_PAN);

        FrameLayout root = new FrameLayout(this);
        preview = new ImageView(this);
        preview.setScaleType(ImageView.ScaleType.CENTER_CROP);
        preview.setOnClickListener(v -> togglePanel());
        root.addView(preview, new FrameLayout.LayoutParams(-1, -1));

        panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(20);
        panel.setPadding(pad, pad, pad, pad);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(0xAA0B1028); bg.setCornerRadius(dp(24));
        panel.setBackground(bg);

        LinearLayout head = new LinearLayout(this);
        head.setOrientation(LinearLayout.HORIZONTAL);
        head.setGravity(Gravity.CENTER_VERTICAL);
        TextView title = new TextView(this);
        title.setText("Sunwalls"); title.setTextColor(Color.WHITE); title.setTextSize(22); title.setTypeface(Typeface.DEFAULT_BOLD);
        head.addView(title, new LinearLayout.LayoutParams(0, -2, 1));
        TextView hide = new TextView(this);
        hide.setText("Hide"); hide.setTextColor(0xCCFFFFFF); hide.setTextSize(14); hide.setPadding(dp(12), dp(8), 0, dp(8));
        hide.setOnClickListener(v -> togglePanel());
        head.addView(hide);
        panel.addView(head);

        info = new TextView(this);
        info.setTextColor(0xCCFFFFFF); info.setTextSize(13); info.setPadding(0, dp(4), 0, dp(14));
        panel.addView(info);

        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        for (int i = 0; i < Prefs.THEMES.length; i++) {
            String t = Prefs.THEMES[i];
            Button btn = pill(Prefs.NAMES[i]); btn.setTextSize(12);
            btn.setOnClickListener(v -> { Prefs.get(this).edit().putString("theme", t).apply(); refresh(); });
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, dp(48), 1); lp.setMargins(dp(3), 0, dp(3), 0);
            row.addView(btn, lp);
            themeButtons[i] = btn;
        }
        panel.addView(row);

        LinearLayout locRow = new LinearLayout(this);
        locRow.setOrientation(LinearLayout.HORIZONTAL);
        locRow.setGravity(Gravity.CENTER_VERTICAL);
        locRow.setPadding(dp(4), dp(12), dp(4), 0);
        TextView locLabel = new TextView(this);
        locLabel.setText("Use my location"); locLabel.setTextColor(Color.WHITE); locLabel.setTextSize(15);
        locRow.addView(locLabel, new LinearLayout.LayoutParams(0, -2, 1));
        autoSwitch = new Switch(this);
        autoSwitch.setOnClickListener(v -> onAutoToggled(autoSwitch.isChecked()));
        locRow.addView(autoSwitch);
        panel.addView(locRow);

        manualRow = new LinearLayout(this);
        manualRow.setOrientation(LinearLayout.HORIZONTAL);
        latField = coordField("Latitude");
        lonField = coordField("Longitude");
        LinearLayout.LayoutParams flp = new LinearLayout.LayoutParams(0, dp(48), 1); flp.setMargins(dp(3), dp(6), dp(3), 0);
        manualRow.addView(latField, flp);
        manualRow.addView(lonField, flp);
        panel.addView(manualRow);

        setBtn = pill("Set as wallpaper");
        setBtn.setOnClickListener(v -> applyWallpaper());
        ((GradientDrawable) setBtn.getBackground()).setColor(0xFFF2C6A0);
        setBtn.setTextColor(0xFF1B1F3A);
        LinearLayout.LayoutParams llp = new LinearLayout.LayoutParams(-1, -2); llp.topMargin = dp(12);
        panel.addView(setBtn, llp);

        FrameLayout.LayoutParams plp = new FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM);
        plp.setMargins(dp(16), 0, dp(16), dp(40));
        root.addView(panel, plp);

        hint = new TextView(this);
        hint.setText("Tap to show controls"); hint.setTextColor(0xAAFFFFFF); hint.setTextSize(12);
        hint.setVisibility(View.GONE);
        FrameLayout.LayoutParams hlp = new FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
        hlp.bottomMargin = dp(48);
        root.addView(hint, hlp);

        setContentView(root);
        refresh();
    }

    @Override protected void onResume() {
        super.onResume();
        if (Prefs.autoLocation(this) && hasLocationPermission()) updateFromDevice();
        refresh();
    }

    @Override protected void onPause() { commitManual(); super.onPause(); }

    private void togglePanel() {
        boolean show = panel.getVisibility() != View.VISIBLE;
        if (!show) commitManual();
        panel.setVisibility(show ? View.VISIBLE : View.GONE);
        hint.setVisibility(show ? View.GONE : View.VISIBLE);
    }

    private Button pill(String text) {
        Button b = new Button(this);
        b.setText(text); b.setAllCaps(false); b.setTextColor(Color.WHITE); b.setTextSize(13);
        b.setSingleLine(true); b.setEllipsize(android.text.TextUtils.TruncateAt.END); b.setPadding(dp(4), 0, dp(4), 0); b.setMinWidth(0); b.setMinimumWidth(0);
        GradientDrawable d = new GradientDrawable(); d.setCornerRadius(dp(18)); d.setColor(0x33FFFFFF);
        b.setBackground(d); b.setStateListAnimator(null);
        return b;
    }

    private EditText coordField(String hintText) {
        EditText e = new EditText(this);
        e.setHint(hintText); e.setHintTextColor(0x88FFFFFF); e.setTextColor(Color.WHITE); e.setTextSize(14);
        e.setSingleLine(true); e.setGravity(Gravity.CENTER); e.setPadding(dp(8), 0, dp(8), 0);
        e.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL | InputType.TYPE_NUMBER_FLAG_SIGNED);
        e.setImeOptions(EditorInfo.IME_ACTION_DONE);
        GradientDrawable d = new GradientDrawable(); d.setCornerRadius(dp(18)); d.setColor(0x33FFFFFF);
        e.setBackground(d);
        e.setOnEditorActionListener((v, action, ev) -> { commitManual(); v.clearFocus(); return false; });
        e.setOnFocusChangeListener((v, focus) -> { if (!focus) commitManual(); });
        return e;
    }

    /** Saves the manually typed coordinates, ignoring invalid input. */
    private void commitManual() {
        if (Prefs.autoLocation(this) || latField == null) return;
        try {
            double lat = Double.parseDouble(latField.getText().toString().trim());
            double lon = Double.parseDouble(lonField.getText().toString().trim());
            if (lat < -90 || lat > 90 || lon < -180 || lon > 180) throw new NumberFormatException();
            if (lat != Prefs.lat(this) || lon != Prefs.lon(this)) { Prefs.setLocation(this, lat, lon); refresh(); }
        } catch (NumberFormatException ignored) {}
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
        boolean auto = Prefs.autoLocation(this);
        autoSwitch.setChecked(auto);
        manualRow.setVisibility(auto ? View.GONE : View.VISIBLE);
        if (!latField.hasFocus() && !lonField.hasFocus()) {
            latField.setText(String.format(Locale.US, "%.2f", lat));
            lonField.setText(String.format(Locale.US, "%.2f", lon));
        }
        setBtn.setText(isActive() ? "Wallpaper active" : "Set as wallpaper");
    }

    private boolean isActive() {
        android.app.WallpaperInfo wi = WallpaperManager.getInstance(this).getWallpaperInfo();
        return wi != null && wi.getPackageName().equals(getPackageName());
    }

    /** Android only lets apps switch to a live wallpaper through the system picker. */
    private void applyWallpaper() {
        if (isActive()) { moveTaskToBack(true); return; }
        Intent in = new Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER);
        in.putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT, new ComponentName(this, SunWallpaperService.class));
        startActivity(in);
    }

    private void onAutoToggled(boolean on) {
        if (!on) { Prefs.get(this).edit().putBoolean("auto", false).apply(); refresh(); return; }
        if (!hasLocationPermission()) {
            requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION}, 1);
            autoSwitch.setChecked(false);
            return;
        }
        Prefs.get(this).edit().putBoolean("auto", true).apply();
        updateFromDevice();
        refresh();
    }

    private boolean hasLocationPermission() {
        return checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void updateFromDevice() {
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
        Prefs.setLocation(this, Math.round(best.getLatitude() * 100) / 100.0, Math.round(best.getLongitude() * 100) / 100.0);
    }

    @Override public void onRequestPermissionsResult(int rc, String[] p, int[] r) {
        if (r.length > 0 && r[0] == PackageManager.PERMISSION_GRANTED) onAutoToggled(true);
    }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }
}
