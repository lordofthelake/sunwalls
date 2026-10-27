#!/usr/bin/env python3
"""Sunwalls generator — renders the four dynamic sci-fi wallpapers and packages them.

  python3 build.py preview [Theme] [hour]   quick low-res look at one moment (default: all themes at 7:00)
  python3 build.py frame Theme hour          one full-resolution 5K frame
  python3 build.py mac                       render 16 frames x 4 themes and pack sun-tagged .heic files (macOS only)
  python3 build.py android                   render portrait frames and rebuild Sunwalls.apk (needs the Android SDK)
  python3 build.py all                       mac + android
  python3 build.py suntable                  print the frame sun table for the Android app's Sun.java

Options: --themes Ringfall,Meridian   only some themes
         --jobs N                     parallel render processes (default: CPU count - 1)
         --lat 52.5                   latitude used for the sun tags in the .heic files
See README.md for details.
"""
import argparse, base64, glob, math, os, plistlib, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SCENES = os.path.join(ROOT, 'scenes')
OUT = os.path.join(ROOT, 'out')
THEMES = ['Ringfall', 'Tidewater', 'Meridian', 'Canopy']
sys.path.insert(0, SCENES)


def py(code, env=None):
    subprocess.run([sys.executable, '-c', code], cwd=SCENES, check=True, env={**os.environ, **(env or {})})


def render_all(outdir, themes, jobs, portrait=False):
    os.makedirs(outdir, exist_ok=True)
    env = {'OUT': outdir, 'NP': str(jobs)}
    if portrait: env['PORTRAIT'] = '1'
    print(f'Rendering {16 * len(themes)} {"portrait" if portrait else "5K"} frames into {outdir} ...', flush=True)
    subprocess.run([sys.executable, 'themes3.py', *themes], cwd=SCENES, check=True, env={**os.environ, **env})


def frame_hours():
    from ast import literal_eval
    src = open(os.path.join(SCENES, 'themes2.py')).read()
    line = next(l for l in src.splitlines() if l.startswith('HOURS='))
    return literal_eval(line.split('=', 1)[1])


def solar_tag(lat_deg):
    """Apple 'solar' metadata: sun altitude/azimuth each frame was drawn for (equinox, local solar time;
    frames show sunrise 6:30, noon 12:30, sunset 18:30). macOS shows the frame nearest the real sun."""
    hours = frame_hours(); lat = math.radians(lat_deg); si = []
    for i, h in enumerate(hours):
        H = math.radians((h - 12.5) * 15)
        alt = math.degrees(math.asin(math.cos(lat) * math.cos(H)))
        az = (math.degrees(math.atan2(math.sin(H), math.cos(H) * math.sin(lat))) + 180) % 360
        si.append({'a': round(alt, 2), 'z': round(az, 2), 'i': i})
    light, dark = hours.index(12.5), hours.index(22)
    plist = {'si': si, 'ap': {'l': light, 'd': dark}}
    return base64.b64encode(plistlib.dumps(plist, fmt=plistlib.FMT_BINARY)).decode(), light, dark


def build_mac(themes, jobs, lat):
    if sys.platform != 'darwin': sys.exit('The .heic packing step needs macOS (it uses Apple ImageIO).')
    frames = os.path.join(OUT, 'frames'); macdir = os.path.join(OUT, 'mac'); os.makedirs(macdir, exist_ok=True)
    render_all(frames, themes, jobs)
    packer = os.path.join(OUT, 'pack_heic')
    subprocess.run(['swiftc', '-O', os.path.join(ROOT, 'pack_heic.swift'), '-o', packer], check=True)
    tag, light, dark = solar_tag(lat)
    for t in themes:
        files = [os.path.join(frames, f'{t}_{i:02d}.png') for i in range(16)]
        subprocess.run([packer, os.path.join(macdir, f'{t}.heic'), tag, str(light), str(dark), *files], check=True)
    print(f'Done: {macdir}')


def build_android(themes, jobs):
    from PIL import Image
    sdk = os.environ.get('ANDROID_HOME', os.path.expanduser('~/Library/Android/sdk'))
    if not os.path.isdir(sdk): sys.exit(f'Android SDK not found at {sdk} (set ANDROID_HOME).')
    appdir = os.path.join(ROOT, '..', 'android')   # app source lives next to the generator
    port = os.path.join(OUT, 'portrait'); render_all(port, themes, jobs, portrait=True)
    assets = os.path.join(appdir, 'assets'); shutil.rmtree(assets, ignore_errors=True); os.makedirs(assets)
    for f in sorted(glob.glob(os.path.join(port, '*.png'))):
        name = os.path.basename(f)[:-4].lower() + '.jpg'
        Image.open(f).convert('RGB').save(os.path.join(assets, name), quality=88, optimize=True)
    subprocess.run(['./build.sh'], cwd=appdir, check=True, env={**os.environ})
    os.makedirs(os.path.join(OUT, 'android'), exist_ok=True)
    shutil.copy(os.path.join(appdir, 'Sunwalls.apk'), os.path.join(OUT, 'android', 'Sunwalls.apk'))
    print(f'Done: {os.path.join(OUT, "android", "Sunwalls.apk")}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['preview', 'frame', 'mac', 'android', 'all', 'suntable'])
    ap.add_argument('args', nargs='*')
    ap.add_argument('--themes', default=','.join(THEMES))
    ap.add_argument('--jobs', type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument('--lat', type=float, default=52.5)
    a = ap.parse_args()
    themes = [t for t in a.themes.split(',') if t]
    os.makedirs(OUT, exist_ok=True)
    if a.cmd in ('preview', 'frame'):
        sel = [a.args[0]] if a.args else themes
        hour = float(a.args[1]) if len(a.args) > 1 else 7.0
        flag = "'--preview'" if a.cmd == 'preview' else "'x'"
        for t in sel:
            out = os.path.join(OUT, f'{a.cmd}_{t}_{hour:g}.png')
            py(f"import sys; sys.argv=['x',{flag}]\nimport themes3 as T\nfrom gen import save\nsave(T.THEMES['{t}']({hour}), r'{out}')")
            print(out)
    if a.cmd == 'suntable':   # Java table for the Android app's Sun.FRAMES
        si = plistlib.loads(base64.b64decode(solar_tag(a.lat)[0]))['si']
        print(',\n'.join('{%s, %s}' % (e['a'], e['z']) for e in si))
    if a.cmd in ('mac', 'all'): build_mac(themes, a.jobs, a.lat)
    if a.cmd in ('android', 'all'): build_android(themes, a.jobs)


if __name__ == '__main__':
    main()
