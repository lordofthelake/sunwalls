#!/bin/bash
# Builds Sunwalls.apk with the plain Android SDK tools (no Gradle / Android Studio needed).
set -euo pipefail
cd "$(dirname "$0")"
SDK="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
BT="$SDK/build-tools/33.0.1"
JAR="$SDK/platforms/android-33/android.jar"
export JAVA_HOME="$(/usr/libexec/java_home)"
rm -rf build && mkdir -p build/gen build/classes build/dex
"$BT/aapt2" compile --dir res -o build/res.zip
"$BT/aapt2" link -o build/unsigned.apk -I "$JAR" --manifest AndroidManifest.xml -A assets \
  --java build/gen build/res.zip --min-sdk-version 26 --target-sdk-version 33 -0 jpg
"$JAVA_HOME/bin/javac" --release 8 -nowarn -XDstringConcat=inline -Xlint:-options -classpath "$JAR" -d build/classes \
  $(find src build/gen -name '*.java')
"$BT/d8" --release --lib "$JAR" --min-api 26 --output build/dex $(find build/classes -name '*.class')
(cd build/dex && zip -q ../unsigned.apk classes.dex)
"$BT/zipalign" -f -p 4 build/unsigned.apk build/aligned.apk
KS="$HOME/.android/sunwalls.keystore"
[ -f "$KS" ] || "$JAVA_HOME/bin/keytool" -genkeypair -keystore "$KS" -storepass sunwalls -keypass sunwalls \
  -alias sunwalls -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Sunwalls" >/dev/null 2>&1
"$BT/apksigner" sign --ks "$KS" --ks-pass pass:sunwalls --key-pass pass:sunwalls --out Sunwalls.apk build/aligned.apk
"$BT/apksigner" verify Sunwalls.apk && ls -l Sunwalls.apk
