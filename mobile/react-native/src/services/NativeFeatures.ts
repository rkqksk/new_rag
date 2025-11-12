/**
 * React Native Native Features
 * Camera, Location, Biometrics, Notifications
 * Version: v8.4.0
 */

import {Platform, PermissionsAndroid, Alert} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Geolocation from '@react-native-community/geolocation';
import {launchCamera, launchImageLibrary} from 'react-native-image-picker';
import messaging from '@react-native-firebase/messaging';
import ReactNativeBiometrics from 'react-native-biometrics';
import PushNotification from 'react-native-push-notification';

// =====================================================
// Camera Service
// =====================================================

export interface CameraOptions {
  mediaType?: 'photo' | 'video' | 'mixed';
  quality?: number; // 0-1
  maxWidth?: number;
  maxHeight?: number;
  includeBase64?: boolean;
}

export class CameraService {
  /**
   * Request camera permission
   */
  static async requestPermission(): Promise<boolean> {
    if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.CAMERA,
        {
          title: 'Camera Permission',
          message: 'App needs camera access',
          buttonPositive: 'OK',
        }
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    }
    return true; // iOS requests permission automatically
  }

  /**
   * Take photo with camera
   */
  static async takePhoto(options: CameraOptions = {}) {
    const hasPermission = await this.requestPermission();
    if (!hasPermission) {
      Alert.alert('Error', 'Camera permission denied');
      return null;
    }

    return new Promise((resolve, reject) => {
      launchCamera(
        {
          mediaType: options.mediaType || 'photo',
          quality: options.quality || 0.8,
          maxWidth: options.maxWidth || 1920,
          maxHeight: options.maxHeight || 1080,
          includeBase64: options.includeBase64 || false,
        },
        (response) => {
          if (response.didCancel) {
            resolve(null);
          } else if (response.errorCode) {
            reject(new Error(response.errorMessage));
          } else if (response.assets && response.assets[0]) {
            resolve(response.assets[0]);
          } else {
            reject(new Error('Unknown error'));
          }
        }
      );
    });
  }

  /**
   * Pick image from gallery
   */
  static async pickImage(options: CameraOptions = {}) {
    return new Promise((resolve, reject) => {
      launchImageLibrary(
        {
          mediaType: options.mediaType || 'photo',
          quality: options.quality || 0.8,
          maxWidth: options.maxWidth || 1920,
          maxHeight: options.maxHeight || 1080,
          includeBase64: options.includeBase64 || false,
          selectionLimit: 1,
        },
        (response) => {
          if (response.didCancel) {
            resolve(null);
          } else if (response.errorCode) {
            reject(new Error(response.errorMessage));
          } else if (response.assets && response.assets[0]) {
            resolve(response.assets[0]);
          } else {
            reject(new Error('Unknown error'));
          }
        }
      );
    });
  }

  /**
   * Capture and upload image
   */
  static async captureAndUpload(apiUrl: string, options: CameraOptions = {}) {
    try {
      const image = await this.takePhoto(options);
      if (!image) return null;

      // Create form data
      const formData = new FormData();
      formData.append('image', {
        uri: image.uri,
        type: image.type || 'image/jpeg',
        name: image.fileName || 'photo.jpg',
      } as any);

      // Upload
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.ok) {
        return await response.json();
      } else {
        throw new Error(`Upload failed: ${response.status}`);
      }
    } catch (error) {
      console.error('Capture and upload error:', error);
      throw error;
    }
  }
}

// =====================================================
// Location Service
// =====================================================

export interface LocationCoords {
  latitude: number;
  longitude: number;
  altitude?: number;
  accuracy?: number;
  heading?: number;
  speed?: number;
}

export class LocationService {
  /**
   * Request location permission
   */
  static async requestPermission(): Promise<boolean> {
    if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
        {
          title: 'Location Permission',
          message: 'App needs location access',
          buttonPositive: 'OK',
        }
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    }
    return true;
  }

  /**
   * Get current location
   */
  static async getCurrentLocation(): Promise<LocationCoords> {
    const hasPermission = await this.requestPermission();
    if (!hasPermission) {
      throw new Error('Location permission denied');
    }

    return new Promise((resolve, reject) => {
      Geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            altitude: position.coords.altitude || undefined,
            accuracy: position.coords.accuracy,
            heading: position.coords.heading || undefined,
            speed: position.coords.speed || undefined,
          });
        },
        (error) => reject(error),
        {
          enableHighAccuracy: true,
          timeout: 15000,
          maximumAge: 10000,
        }
      );
    });
  }

  /**
   * Watch location changes
   */
  static watchLocation(
    onLocationChange: (coords: LocationCoords) => void,
    onError?: (error: any) => void
  ): number {
    return Geolocation.watchPosition(
      (position) => {
        onLocationChange({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          altitude: position.coords.altitude || undefined,
          accuracy: position.coords.accuracy,
          heading: position.coords.heading || undefined,
          speed: position.coords.speed || undefined,
        });
      },
      (error) => {
        if (onError) onError(error);
      },
      {
        enableHighAccuracy: true,
        distanceFilter: 10, // Update every 10 meters
      }
    );
  }

  /**
   * Stop watching location
   */
  static clearWatch(watchId: number) {
    Geolocation.clearWatch(watchId);
  }

  /**
   * Calculate distance between two points (Haversine formula)
   */
  static getDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ): number {
    const R = 6371; // Earth radius in km
    const dLat = this.toRad(lat2 - lat1);
    const dLon = this.toRad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.toRad(lat1)) *
        Math.cos(this.toRad(lat2)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distance in km
  }

  private static toRad(degrees: number): number {
    return (degrees * Math.PI) / 180;
  }
}

// =====================================================
// Biometrics Service
// =====================================================

export class BiometricsService {
  private static rnBiometrics = new ReactNativeBiometrics();

  /**
   * Check if biometrics is available
   */
  static async isAvailable(): Promise<{available: boolean; biometryType?: string}> {
    try {
      const {available, biometryType} = await this.rnBiometrics.isSensorAvailable();
      return {available, biometryType};
    } catch (error) {
      console.error('Biometrics check error:', error);
      return {available: false};
    }
  }

  /**
   * Authenticate with biometrics
   */
  static async authenticate(promptMessage: string = 'Verify your identity'): Promise<boolean> {
    try {
      const {available} = await this.isAvailable();
      if (!available) {
        Alert.alert('Error', 'Biometric authentication not available');
        return false;
      }

      const {success} = await this.rnBiometrics.simplePrompt({
        promptMessage,
        cancelButtonText: 'Cancel',
      });

      return success;
    } catch (error) {
      console.error('Biometrics auth error:', error);
      return false;
    }
  }

  /**
   * Create biometric keys
   */
  static async createKeys(): Promise<{publicKey: string} | null> {
    try {
      const {publicKey} = await this.rnBiometrics.createKeys();
      return {publicKey};
    } catch (error) {
      console.error('Create keys error:', error);
      return null;
    }
  }

  /**
   * Delete biometric keys
   */
  static async deleteKeys(): Promise<boolean> {
    try {
      const {keysDeleted} = await this.rnBiometrics.deleteKeys();
      return keysDeleted;
    } catch (error) {
      console.error('Delete keys error:', error);
      return false;
    }
  }
}

// =====================================================
// Push Notification Service
// =====================================================

export class PushNotificationService {
  /**
   * Initialize push notifications
   */
  static async initialize() {
    // Configure local notifications
    PushNotification.configure({
      onRegister: (token) => {
        console.log('FCM Token:', token);
      },
      onNotification: (notification) => {
        console.log('Notification received:', notification);
        notification.finish('UIBackgroundFetchResultNoData');
      },
      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },
      popInitialNotification: true,
      requestPermissions: true,
    });

    // Request Firebase Cloud Messaging permission (iOS)
    if (Platform.OS === 'ios') {
      const authStatus = await messaging().requestPermission();
      const enabled =
        authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
        authStatus === messaging.AuthorizationStatus.PROVISIONAL;

      if (!enabled) {
        console.log('Push notification permission denied');
      }
    }

    // Get FCM token
    const token = await messaging().getToken();
    await AsyncStorage.setItem('fcm_token', token);

    return token;
  }

  /**
   * Show local notification
   */
  static showLocalNotification(title: string, message: string, data?: any) {
    PushNotification.localNotification({
      title,
      message,
      userInfo: data,
      playSound: true,
      soundName: 'default',
      vibrate: true,
    });
  }

  /**
   * Schedule notification
   */
  static scheduleNotification(
    title: string,
    message: string,
    date: Date,
    data?: any
  ) {
    PushNotification.localNotificationSchedule({
      title,
      message,
      date,
      userInfo: data,
      playSound: true,
      soundName: 'default',
    });
  }

  /**
   * Cancel all notifications
   */
  static cancelAllNotifications() {
    PushNotification.cancelAllLocalNotifications();
  }

  /**
   * Get badge count (iOS)
   */
  static async getBadgeCount(): Promise<number> {
    if (Platform.OS === 'ios') {
      return new Promise((resolve) => {
        PushNotification.getApplicationIconBadgeNumber((count) => {
          resolve(count);
        });
      });
    }
    return 0;
  }

  /**
   * Set badge count (iOS)
   */
  static setBadgeCount(count: number) {
    if (Platform.OS === 'ios') {
      PushNotification.setApplicationIconBadgeNumber(count);
    }
  }

  /**
   * Listen to foreground messages
   */
  static onForegroundMessage(callback: (message: any) => void) {
    return messaging().onMessage(async (remoteMessage) => {
      console.log('Foreground message:', remoteMessage);
      callback(remoteMessage);
    });
  }

  /**
   * Listen to background messages
   */
  static setBackgroundMessageHandler(handler: (message: any) => Promise<void>) {
    messaging().setBackgroundMessageHandler(handler);
  }
}

// Export all services
export default {
  Camera: CameraService,
  Location: LocationService,
  Biometrics: BiometricsService,
  PushNotification: PushNotificationService,
};
