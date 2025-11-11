# Mobile Deployment Guide - v7.4.0

## 목차
1. [개요](#개요)
2. [PWA 배포](#pwa-배포)
3. [React Native 배포](#react-native-배포)
4. [API 설정](#api-설정)
5. [푸시 알림 설정](#푸시-알림-설정)

---

## 개요

RAG Enterprise 모바일 솔루션은 두 가지 버전으로 제공됩니다:

1. **PWA (Progressive Web App)** - 웹 기반 모바일 앱
   - 설치 가능
   - 오프라인 지원
   - 푸시 알림
   - 크로스 플랫폼

2. **React Native App** - 네이티브 모바일 앱
   - iOS + Android
   - 네이티브 성능
   - 카메라, 파일 접근
   - 고급 푸시 알림

---

## PWA 배포

### 1. 빌드

```bash
cd mobile/pwa

# Static 파일 준비
cp index.html public/
cp service-worker.js public/
cp manifest.json public/
```

### 2. 웹 서버 설정

**Nginx 설정:**

```nginx
server {
    listen 443 ssl http2;
    server_name mobile.example.com;

    # SSL 인증서
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    root /var/www/rag-mobile/pwa/public;
    index index.html;

    # Service Worker
    location /service-worker.js {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Service-Worker-Allowed "/";
    }

    # Manifest
    location /manifest.json {
        add_header Content-Type application/manifest+json;
    }

    # API Proxy
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 3. HTTPS 필수

PWA는 HTTPS에서만 작동합니다:

```bash
# Let's Encrypt 인증서 발급
sudo certbot --nginx -d mobile.example.com
```

### 4. 테스트

```bash
# Lighthouse로 PWA 점수 확인
npx lighthouse https://mobile.example.com --view

# Service Worker 확인
# Chrome DevTools > Application > Service Workers
```

---

## React Native 배포

### 1. 환경 설정

```bash
cd mobile/react-native

# 패키지 설치
npm install

# iOS (macOS only)
cd ios && pod install && cd ..

# Android SDK 확인
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

### 2. iOS 빌드

```bash
# 개발 빌드
npm run ios

# Release 빌드
cd ios
xcodebuild -workspace RAGEnterpriseMobile.xcworkspace \
  -scheme RAGEnterpriseMobile \
  -configuration Release \
  -archivePath $PWD/build/RAGEnterpriseMobile.xcarchive \
  archive

# IPA 생성
xcodebuild -exportArchive \
  -archivePath $PWD/build/RAGEnterpriseMobile.xcarchive \
  -exportPath $PWD/build \
  -exportOptionsPlist ExportOptions.plist

# App Store Connect에 업로드
xcrun altool --upload-app \
  --type ios \
  --file build/RAGEnterpriseMobile.ipa \
  --username "your@email.com" \
  --password "app-specific-password"
```

### 3. Android 빌드

```bash
# 개발 빌드
npm run android

# Release APK 생성
cd android
./gradlew assembleRelease

# APK 위치
# android/app/build/outputs/apk/release/app-release.apk

# AAB (Google Play) 생성
./gradlew bundleRelease

# AAB 위치
# android/app/build/outputs/bundle/release/app-release.aab

# 서명
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
  -keystore my-release-key.keystore \
  app-release.aab alias_name

# zipalign
zipalign -v -p 4 app-release.aab app-release-aligned.aab
```

### 4. 앱 스토어 제출

**iOS (App Store):**
1. Xcode로 Archive
2. Organizer에서 Upload to App Store
3. App Store Connect에서 메타데이터 입력
4. 심사 제출

**Android (Google Play):**
1. Google Play Console 접속
2. AAB 파일 업로드
3. 스토어 등록정보 작성
4. 심사 제출

---

## API 설정

### 1. API 엔드포인트 구성

**프로덕션 설정:**

```typescript
// config.ts
const API_CONFIG = {
  baseURL: 'https://api.example.com',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'X-Mobile-Version': '7.4.0',
  },
};
```

### 2. 오프라인 지원

```typescript
// api/client.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

async function fetchWithCache(url: string) {
  try {
    const response = await fetch(url);
    const data = await response.json();

    // 캐시에 저장
    await AsyncStorage.setItem(url, JSON.stringify(data));

    return data;
  } catch (error) {
    // 오프라인: 캐시에서 가져오기
    const cached = await AsyncStorage.getItem(url);
    if (cached) {
      return JSON.parse(cached);
    }
    throw error;
  }
}
```

---

## 푸시 알림 설정

### 1. Firebase Cloud Messaging (Android + iOS)

```bash
# Firebase CLI 설치
npm install -g firebase-tools

# Firebase 프로젝트 초기화
firebase init

# google-services.json (Android)
# 다운로드 후 android/app/google-services.json에 복사

# GoogleService-Info.plist (iOS)
# 다운로드 후 ios/GoogleService-Info.plist에 복사
```

### 2. iOS APNs 설정

1. Apple Developer 계정 로그인
2. Certificates, Identifiers & Profiles
3. Keys → Create new key
4. APNs 활성화
5. .p8 파일 다운로드
6. Firebase Console에 업로드

### 3. 푸시 알림 코드

```typescript
// App.tsx
import PushNotification from 'react-native-push-notification';
import messaging from '@react-native-firebase/messaging';

// 권한 요청
async function requestUserPermission() {
  const authStatus = await messaging().requestPermission();
  const enabled =
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;

  if (enabled) {
    console.log('Authorization status:', authStatus);
  }
}

// 토큰 가져오기
async function getToken() {
  const token = await messaging().getToken();
  console.log('FCM Token:', token);

  // 서버에 토큰 전송
  await fetch('https://api.example.com/mobile-api/notifications/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      device_id: DeviceInfo.getUniqueId(),
      platform: Platform.OS,
      push_token: token,
      user_id: currentUserId,
    }),
  });
}

// 포그라운드 메시지 처리
messaging().onMessage(async remoteMessage => {
  console.log('Foreground notification:', remoteMessage);

  PushNotification.localNotification({
    title: remoteMessage.notification?.title,
    message: remoteMessage.notification?.body || '',
  });
});

// 백그라운드 메시지 처리
messaging().setBackgroundMessageHandler(async remoteMessage => {
  console.log('Background notification:', remoteMessage);
});
```

---

## 테스트

### 1. PWA 테스트

```bash
# 로컬 테스트
python -m http.server 8080 -d mobile/pwa/public

# 실제 디바이스 테스트 (HTTPS 필요)
ngrok http 8080
# 생성된 HTTPS URL을 모바일에서 접속
```

### 2. React Native 테스트

```bash
# iOS 시뮬레이터
npm run ios

# Android 에뮬레이터
npm run android

# 실제 디바이스
# iOS: Xcode에서 디바이스 선택 후 Run
# Android: USB 연결 후 npm run android
```

---

## 모니터링

### 1. 크래시 리포팅

**Sentry 설정:**

```bash
npm install @sentry/react-native

# iOS
cd ios && pod install

# Sentry 초기화
npx @sentry/wizard -i reactNative -p ios android
```

```typescript
// App.tsx
import * as Sentry from '@sentry/react-native';

Sentry.init({
  dsn: 'your-sentry-dsn',
  environment: 'production',
});
```

### 2. 분석

**Firebase Analytics:**

```typescript
import analytics from '@react-native-firebase/analytics';

// 화면 전환 추적
await analytics().logScreenView({
  screen_name: 'Home',
  screen_class: 'HomeScreen',
});

// 이벤트 추적
await analytics().logEvent('search', {
  search_term: 'PET 용기',
  category: '플라스틱',
});
```

---

## 성능 최적화

### 1. 이미지 최적화

```typescript
import FastImage from 'react-native-fast-image';

<FastImage
  source={{
    uri: 'https://example.com/image.jpg',
    priority: FastImage.priority.high,
    cache: FastImage.cacheControl.immutable,
  }}
  style={{width: 200, height: 200}}
/>
```

### 2. 코드 스플리팅

```typescript
// Lazy loading
const SearchScreen = React.lazy(() => import('./screens/SearchScreen'));
```

---

## 보안

### 1. API 키 보호

```bash
# .env 파일 사용
API_KEY=your-secret-api-key

# react-native-config
npm install react-native-config
```

```typescript
import Config from 'react-native-config';

const apiKey = Config.API_KEY;
```

### 2. 인증서 피닝

```typescript
// iOS: Info.plist
// Android: network_security_config.xml
```

---

## 문제 해결

### PWA

**문제:** Service Worker가 등록되지 않음
**해결:** HTTPS 확인, 브라우저 캐시 삭제

**문제:** 설치 버튼이 표시되지 않음
**해결:** manifest.json 검증, HTTPS 확인

### React Native

**문제:** Build 실패 (iOS)
**해결:** `pod install` 재실행, Xcode 캐시 삭제

**문제:** Build 실패 (Android)
**해결:** `./gradlew clean`, Android Studio에서 Invalidate Caches

---

## 지원

- 문서: `mobile/README.md`
- 이슈: GitHub Issues
- 이메일: support@example.com

**Version**: v7.4.0
**Last Updated**: 2025-01-11
