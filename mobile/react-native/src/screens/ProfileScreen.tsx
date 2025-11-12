import React, {useEffect, useState} from 'react';
import {View, Text, StyleSheet, TouchableOpacity, Image, ScrollView, Switch} from 'react-native';
import {useStore} from '../store/useStore';
import {getUserProfile} from '../services/api';

export default function ProfileScreen() {
  const {user, setUser, theme, setTheme, language, setLanguage} = useStore();
  const [isDark, setIsDark] = useState(theme === 'dark');
  const [isKorean, setIsKorean] = useState(language === 'ko');

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const profile = await getUserProfile();
      setUser(profile);
    } catch (error) {
      // Mock user
      setUser({
        id: '1',
        name: '사용자',
        email: 'user@example.com',
        phone: '010-1234-5678',
        role: '작업자',
      });
    }
  };

  const handleThemeToggle = (value: boolean) => {
    setIsDark(value);
    setTheme(value ? 'dark' : 'light');
  };

  const handleLanguageToggle = (value: boolean) => {
    setIsKorean(value);
    setLanguage(value ? 'ko' : 'en');
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{user?.name?.[0] || 'U'}</Text>
        </View>
        <Text style={styles.name}>{user?.name || '사용자'}</Text>
        <Text style={styles.email}>{user?.email || 'user@example.com'}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>계정 정보</Text>
        <View style={styles.infoCard}>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>이름</Text>
            <Text style={styles.infoValue}>{user?.name || '-'}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>이메일</Text>
            <Text style={styles.infoValue}>{user?.email || '-'}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>전화번호</Text>
            <Text style={styles.infoValue}>{user?.phone || '-'}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>역할</Text>
            <Text style={styles.infoValue}>{user?.role || '-'}</Text>
          </View>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>설정</Text>
        <View style={styles.settingsCard}>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>다크 모드</Text>
            <Switch value={isDark} onValueChange={handleThemeToggle} />
          </View>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>한국어</Text>
            <Switch value={isKorean} onValueChange={handleLanguageToggle} />
          </View>
        </View>
      </View>

      <TouchableOpacity style={styles.logoutButton}>
        <Text style={styles.logoutText}>로그아웃</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#f5f5f5'},
  header: {backgroundColor: '#667eea', padding: 32, alignItems: 'center'},
  avatar: {width: 80, height: 80, borderRadius: 40, backgroundColor: 'rgba(255,255,255,0.3)', justifyContent: 'center', alignItems: 'center', marginBottom: 12},
  avatarText: {fontSize: 32, fontWeight: 'bold', color: '#fff'},
  name: {fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 4},
  email: {fontSize: 16, color: 'rgba(255,255,255,0.9)'},
  section: {padding: 16},
  sectionTitle: {fontSize: 18, fontWeight: '600', marginBottom: 12, color: '#333'},
  infoCard: {backgroundColor: '#fff', borderRadius: 12, padding: 16},
  infoRow: {flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#f5f5f5'},
  infoLabel: {fontSize: 16, color: '#666'},
  infoValue: {fontSize: 16, fontWeight: '600', color: '#333'},
  settingsCard: {backgroundColor: '#fff', borderRadius: 12, padding: 16},
  settingRow: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 12},
  settingLabel: {fontSize: 16, color: '#333'},
  logoutButton: {margin: 16, padding: 16, backgroundColor: '#fff', borderRadius: 12, alignItems: 'center'},
  logoutText: {fontSize: 16, fontWeight: '600', color: '#ff6b6b'},
});
