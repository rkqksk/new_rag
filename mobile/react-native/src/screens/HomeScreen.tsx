import React from 'react';
import {View, Text, StyleSheet, TouchableOpacity, ScrollView} from 'react-native';

const QuickAction = ({icon, label, onPress}: any) => (
  <TouchableOpacity style={styles.actionCard} onPress={onPress}>
    <Text style={styles.actionIcon}>{icon}</Text>
    <Text style={styles.actionLabel}>{label}</Text>
  </TouchableOpacity>
);

export default function HomeScreen({navigation}: any) {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>🚀 RAG Enterprise</Text>
        <Text style={styles.subtitle}>모바일 통합 관리 시스템</Text>
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
  header: {padding: 20, backgroundColor: '#667eea', borderBottomLeftRadius: 20, borderBottomRightRadius: 20},
  title: {fontSize: 24, fontWeight: 'bold', color: 'white'},
  subtitle: {fontSize: 14, color: 'white', marginTop: 4},
  quickActions: {flexDirection: 'row', flexWrap: 'wrap', padding: 16, gap: 12},
  actionCard: {width: '30%', backgroundColor: 'white', borderRadius: 12, padding: 16, alignItems: 'center', shadowColor: '#000', shadowOffset: {width: 0, height: 2}, shadowOpacity: 0.1, shadowRadius: 4, elevation: 2},
  actionIcon: {fontSize: 32, marginBottom: 8},
  actionLabel: {fontSize: 12, textAlign: 'center'},
  card: {backgroundColor: 'white', margin: 16, padding: 16, borderRadius: 12, shadowColor: '#000', shadowOffset: {width: 0, height: 2}, shadowOpacity: 0.1, shadowRadius: 4, elevation: 2},
  cardTitle: {fontSize: 16, fontWeight: 'bold', marginBottom: 8},
  cardText: {fontSize: 14, color: '#666'},
});
