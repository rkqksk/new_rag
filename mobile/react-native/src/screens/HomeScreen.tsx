import React, {useState, useEffect} from 'react';
import {View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {useStore} from '../store/useStore';

const QuickAction = ({icon, label, onPress}: any) => (
  <TouchableOpacity style={styles.actionCard} onPress={onPress}>
    <Text style={styles.actionIcon}>{icon}</Text>
    <Text style={styles.actionLabel}>{label}</Text>
  </TouchableOpacity>
);

export default function HomeScreen({navigation}: any) {
  const {user, setUser} = useStore();
  const [userName, setUserName] = useState('사용자');

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = await AsyncStorage.getItem('access_token');
    if (!token) {
      navigation.replace('Login');
      return;
    }

    if (user) {
      setUserName(user.name);
    } else {
      // Try to get user from storage
      const userStr = await AsyncStorage.getItem('user');
      if (userStr) {
        const userData = JSON.parse(userStr);
        setUser(userData);
        setUserName(userData.name);
      }
    }
  };

  const handleLogout = () => {
    Alert.alert(
      '로그아웃',
      '로그아웃 하시겠습니까?',
      [
        {text: '취소', style: 'cancel'},
        {
          text: '로그아웃',
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.removeItem('access_token');
            await AsyncStorage.removeItem('refresh_token');
            await AsyncStorage.removeItem('user');
            setUser(null);
            navigation.replace('Login');
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>🚀 RAG Enterprise</Text>
          <Text style={styles.subtitle}>{userName}님, 환영합니다!</Text>
        </View>
        <TouchableOpacity style={styles.profileButton} onPress={() => navigation.navigate('Profile')}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{userName.charAt(0).toUpperCase()}</Text>
          </View>
        </TouchableOpacity>
      </View>

      <View style={styles.quickActions}>
        <QuickAction icon="🔍" label="제품검색" onPress={() => navigation.navigate('Search')} />
        <QuickAction icon="📸" label="이미지검색" onPress={() => navigation.navigate('ImageSearch')} />
        <QuickAction icon="📱" label="QR스캔" onPress={() => navigation.navigate('QRScan')} />
        <QuickAction icon="📋" label="작업지시" onPress={() => navigation.navigate('WorkOrders')} />
        <QuickAction icon="📊" label="대시보드" onPress={() => navigation.navigate('Dashboard')} />
        <QuickAction icon="💬" label="채팅" onPress={() => navigation.navigate('Chat')} />
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>최근 활동</Text>
        <Text style={styles.cardText}>로딩 중...</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>알림</Text>
        <Text style={styles.cardText}>새로운 알림이 없습니다</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#f5f5f5'},
  header: {
    padding: 20,
    backgroundColor: '#667eea',
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {fontSize: 24, fontWeight: 'bold', color: 'white'},
  subtitle: {fontSize: 14, color: 'white', marginTop: 4, opacity: 0.9},
  profileButton: {
    padding: 4,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'white',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#667eea',
  },
  quickActions: {flexDirection: 'row', flexWrap: 'wrap', padding: 16, gap: 12},
  actionCard: {width: '30%', backgroundColor: 'white', borderRadius: 12, padding: 16, alignItems: 'center', shadowColor: '#000', shadowOffset: {width: 0, height: 2}, shadowOpacity: 0.1, shadowRadius: 4, elevation: 2},
  actionIcon: {fontSize: 32, marginBottom: 8},
  actionLabel: {fontSize: 12, textAlign: 'center'},
  card: {backgroundColor: 'white', margin: 16, padding: 16, borderRadius: 12, shadowColor: '#000', shadowOffset: {width: 0, height: 2}, shadowOpacity: 0.1, shadowRadius: 4, elevation: 2},
  cardTitle: {fontSize: 16, fontWeight: 'bold', marginBottom: 8},
  cardText: {fontSize: 14, color: '#666'},
});
