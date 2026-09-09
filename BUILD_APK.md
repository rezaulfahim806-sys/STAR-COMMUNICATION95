# STAR COMMUNICATION — APK Build Guide

This is the prepared Android Studio project for the STAR COMMUNICATION app.

## Build a debug APK

1. Install **Android Studio** on Windows/macOS/Linux.
2. Open this folder:
   `STAR_COMMUNICATION_Android`
3. Let Android Studio download/sync:
   - Android Gradle Plugin 8.5.2
   - Gradle 8.7
   - Android SDK Platform 35
   - Android SDK Build-Tools
4. Select **Build → Build APK(s)**.
5. APK location:
   `app/build/outputs/apk/debug/app-debug.apk`
6. Copy that APK to the Android phone and install it.

## Recommended SDK settings

- compileSdk: 35
- targetSdk: 35
- minSdk: 23
- applicationId: `com.starcommunication.isp`
- versionName: `1.0`

## Backend

The app already has Internet permission and can call the backend API configured from the app's server/API settings. Keep bKash API credentials on the backend, not inside the APK.

## bKash

The configured customer payment number is **01897-099850**. Transactions are not auto-paid; they remain pending until the admin manually confirms payment. Production bKash API/webhook can be added later.
