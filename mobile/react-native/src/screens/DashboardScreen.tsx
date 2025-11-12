import React, {useEffect, useState} from 'react';
import {View, Text, StyleSheet, ScrollView, ActivityIndicator} from 'react-native';
import {getDashboardStats} from '../services/api';
import {useStore} from '../store/useStore';

export default function DashboardScreen() {
  const {dashboardStats, setDashboardStats} = useStore();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setIsLoading(true);
    try {
      const stats = await getDashboardStats();
      setDashboardStats(stats);
    } catch (error) {
      // Mock data
      setDashboardStats({
        totalWorkOrders: 42,
        completedWorkOrders: 28,
        inProgressWorkOrders: 10,
        delayedWorkOrders: 4,
        totalProducts: 1523,
        recentSearches: 156,
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#667eea" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>📊 대시보드</Text>

      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{dashboardStats?.totalWorkOrders || 0}</Text>
          <Text style={styles.statLabel}>작업지시</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, {color: '#4ade80'}]}>{dashboardStats?.completedWorkOrders || 0}</Text>
          <Text style={styles.statLabel}>완료</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, {color: '#ffc107'}]}>{dashboardStats?.inProgressWorkOrders || 0}</Text>
          <Text style={styles.statLabel}>진행중</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, {color: '#ff6b6b'}]}>{dashboardStats?.delayedWorkOrders || 0}</Text>
          <Text style={styles.statLabel}>지연</Text>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>제품 정보</Text>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>총 제품 수</Text>
          <Text style={styles.infoValue}>{dashboardStats?.totalProducts.toLocaleString() || 0}</Text>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>검색 통계</Text>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>최근 검색</Text>
          <Text style={styles.infoValue}>{dashboardStats?.recentSearches || 0}회</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#f5f5f5'},
  loadingContainer: {flex: 1, justifyContent: 'center', alignItems: 'center'},
  title: {fontSize: 24, fontWeight: 'bold', padding: 20, color: '#333'},
  statsGrid: {flexDirection: 'row', flexWrap: 'wrap', padding: 12, gap: 12},
  statCard: {width: '47%', backgroundColor: '#fff', padding: 20, borderRadius: 12, alignItems: 'center'},
  statValue: {fontSize: 32, fontWeight: '700', color: '#667eea', marginBottom: 4},
  statLabel: {fontSize: 14, color: '#666'},
  card: {backgroundColor: '#fff', margin: 12, padding: 16, borderRadius: 12},
  cardTitle: {fontSize: 18, fontWeight: '600', marginBottom: 12},
  infoRow: {flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8},
  infoLabel: {fontSize: 16, color: '#666'},
  infoValue: {fontSize: 16, fontWeight: '600', color: '#333'},
});
