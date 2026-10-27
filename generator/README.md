# Sunwalls generator

Generates the four calm sci-fi dynamic wallpapers (Ringfall, Tidewater, Meridian, Canopy).
Each theme has 16 frames across the day. The script packs them as sun-tagged macOS `.heic` files
and as an Android live-wallpaper app.

## One-time setup

```bash
cd sunwalls/generator
python3 -m venv .venv
.venv/bin/pip install numpy pillow scipy
```

For the Mac wallpapers you also need Xcode Command Line Tools, which provide `swiftc`
(`xcode-select --install`).

For the Android app you need the Android SDK in `~/Library/Android/sdk`, with build-tools 33.0.1 and
platform android-33, plus a JDK. If your SDK is somewhere else, set `ANDROID_HOME` to its path.
`build.py android` builds the app in `../android`. Frames are written to `android/assets/`, which is not
committed.

## Usage

```bash
.venv/bin/python build.py preview                 # all themes at 7:00, quarter resolution → out/preview_*.png
.venv/bin/python build.py preview Meridian 19.5   # one theme at 19:30
.venv/bin/python build.py frame Canopy 22         # one full 5K frame
.venv/bin/python build.py mac                     # 64 frames → out/mac/*.heic  (≈ a few minutes on Apple Silicon)
.venv/bin/python build.py android                 # portrait frames → out/android/Sunwalls.apk
.venv/bin/python build.py all --themes Ringfall   # both, only one theme
```

Options:

- `--jobs N` sets the number of parallel render processes.
- `--lat 48.1` sets the latitude used for the sun tags in the `.heic` files.

To install the results:

- **Mac:** take `out/mac/*.heic`. Then open System
  Settings → Wallpaper → Add Photo, and choose "Dynamic". Location Services must be on so macOS knows where the sun is.
- **Android:** copy `out/android/Sunwalls.apk` to the phone and open it. It is signed with the key in
  `~/.android/sunwalls.keystore`, which `build.sh` creates on first build. Builds signed with the same key
  install as updates over each other; builds from different machines don't, so uninstall first. Keep that file
  private and don't share it.

## How it works

| File | Role |
|---|---|
| `build.py` | Entry point: rendering, sun tags, packing |
| `scenes/themes3.py` | The four scenes: layers, ships, settlements, sea, forest |
| `scenes/themes2.py` | Colour palettes for night / dawn / day / sunset, and the 16 frame times (`HOURS`) |
| `scenes/kit.py` | Flat building parts: domes, towers, dishes, cabins, greenhouses, turbines, hangar… |
| `scenes/dyn.py`, `scenes/gen.py` | Drawing basics: sky, sun path, stars, glows, supersampled vector shapes |
| `pack_heic.swift` | Writes the multi-frame HEIC with Apple's `apple_desktop:solar` metadata |

- **Time of day.** Palettes are keyframed at night, pre-dawn, dawn, morning, day, sunset, dusk and night,
  and blended smoothly in between. The sun and moon follow arcs from the frame's hour, and the stars rotate.
- **Frames and sun tags.** The 16 frames are drawn for the hours in `HOURS`. Each one is tagged with the sun
  position for that hour at the equinox, so macOS (and the Android app) shows whichever frame matches the
  real sun. That makes summer days long and winter days short and dim.
- **Resolution.** Frames are 5120×2880 (Mac) and 1800×2400 portrait (Android, with parallax panning).

### Common tweaks

- **Colours:** edit the `RF`, `TW`, `MD` and `CN` palettes in `scenes/themes2.py`. Each has `dawn`, `day`,
  `sunset` and `night` entries.
- **Ship size:** `SHIP=1.3 .venv/bin/python build.py …`, or change `PX(46)` in `ships_up`.
- **Ship routes:** the `specs` lists in each scene function.
- **Settlements:** the `town`, `build`, `lh` and `cab` functions in `themes3.py`. Each calls `Kit` parts with
  normalized x positions and sizes in screen-height units. In Meridian, `SITES` sets each ridge's search
  range and perspective scale.
- **Haze and depth:** the `hazes=[…]` lists per scene (0 = crisp, higher = fades into the sky).
- **Frame times:** `HOURS` in `themes2.py`. The `.heic` sun tags follow automatically. For Android, paste the
  output of `build.py suntable` into the `FRAMES` table in the app's `Sun.java` (`android/src/io/noemata/sunwalls/Sun.java`).
