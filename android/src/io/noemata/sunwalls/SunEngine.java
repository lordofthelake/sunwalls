package io.noemata.sunwalls;

import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.service.wallpaper.WallpaperService;
import android.view.SurfaceHolder;

import java.io.InputStream;

final class SunEngine extends WallpaperService.Engine implements SharedPreferences.OnSharedPreferenceChangeListener, Runnable {
        private final SunWallpaperService svc;
        SunEngine(SunWallpaperService svc) { svc.super(); this.svc = svc; }
        private final FrameRunner frame = new FrameRunner(this);
        public void run() { update(false); scheduleCheck(); }
        private final Handler handler = new Handler(Looper.getMainLooper());
        private final Paint paint = new Paint(Paint.FILTER_BITMAP_FLAG | Paint.ANTI_ALIAS_FLAG);
        private Bitmap current, previous;
        private String currentKey = "";
        private long fadeStart = 0;
        static final long FADE_MS = 2500, CHECK_MS = 60_000;
        private float xOffset = 0.5f;
        private boolean visible;
        private int w, h;


        @Override public void onCreate(SurfaceHolder holder) {
            super.onCreate(holder);
            setOffsetNotificationsEnabled(true);
            Prefs.get(svc).registerOnSharedPreferenceChangeListener(this);
        }
        @Override public void onDestroy() {
            Prefs.get(svc).unregisterOnSharedPreferenceChangeListener(this);
            handler.removeCallbacksAndMessages(null);
            super.onDestroy();
        }
        @Override public void onSharedPreferenceChanged(SharedPreferences p, String k) { update(true); }
        @Override public void onVisibilityChanged(boolean v) {
            visible = v;
            handler.removeCallbacks(this);
            if (v) { update(false); scheduleCheck(); }
        }
        @Override public void onSurfaceChanged(SurfaceHolder holder, int format, int width, int height) {
            super.onSurfaceChanged(holder, format, width, height);
            w = width; h = height; update(true);
        }
        @Override public void onSurfaceDestroyed(SurfaceHolder holder) { visible = false; handler.removeCallbacksAndMessages(null); super.onSurfaceDestroyed(holder); }
        @Override public void onOffsetsChanged(float xo, float yo, float xs, float ys, int xp, int yp) {
            xOffset = xo; draw();
        }

        private void scheduleCheck() { if (visible) handler.postDelayed(this, CHECK_MS); }

        private void update(boolean force) {
            String theme = Prefs.theme(svc);
            int idx = Sun.frameFor(System.currentTimeMillis(), Prefs.lat(svc), Prefs.lon(svc));
            String key = Prefs.asset(theme, idx);
            if (!force && key.equals(currentKey)) return;
            Bitmap b = load(key);
            if (b == null) return;
            boolean fade = current != null && !force;
            if (previous != null && previous != current) previous.recycle();
            previous = fade ? current : null;
            if (!fade && current != null) current.recycle();
            current = b; currentKey = key;
            fadeStart = SystemClock.uptimeMillis();
            draw();
        }

        private Bitmap load(String name) {
            try (InputStream in = svc.getAssets().open(name)) {
                BitmapFactory.Options o = new BitmapFactory.Options();
                o.inPreferredConfig = Bitmap.Config.ARGB_8888;
                return BitmapFactory.decodeStream(in, null, o);
            } catch (Exception e) { return null; }
        }

        private void drawBitmap(Canvas c, Bitmap b, int alpha) {
            // scale to fill height, pan horizontally with the launcher's page offset
            float scale = Math.max((float) h / b.getHeight(), (float) w / b.getWidth());
            float bw = b.getWidth() * scale, bh = b.getHeight() * scale;
            float left = -(bw - w) * xOffset, top = -(bh - h) / 2f;
            paint.setAlpha(alpha);
            c.drawBitmap(b, null, new Rect((int) left, (int) top, (int) (left + bw), (int) (top + bh)), paint);
        }

        void draw() {
            if (current == null || w == 0) return;
            SurfaceHolder holder = getSurfaceHolder();
            Canvas c = null;
            boolean again = false;
            try {
                c = holder.lockCanvas();
                if (c == null) return;
                float t = Math.min(1f, (SystemClock.uptimeMillis() - fadeStart) / (float) FADE_MS);
                if (previous != null && t < 1f) {
                    drawBitmap(c, previous, 255);
                    drawBitmap(c, current, (int) (255 * t));
                    again = true;
                } else {
                    if (previous != null) { previous.recycle(); previous = null; }
                    drawBitmap(c, current, 255);
                }
            } finally {
                if (c != null) holder.unlockCanvasAndPost(c);
            }
            handler.removeCallbacks(frame);
            if (again) handler.postDelayed(frame, 33);
        }
}

final class FrameRunner implements Runnable {
    private final SunEngine e; FrameRunner(SunEngine e) { this.e = e; }
    public void run() { e.draw(); }
}
