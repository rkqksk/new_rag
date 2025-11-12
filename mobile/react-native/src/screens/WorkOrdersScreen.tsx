import React, {useEffect, useState} from 'react';
import {View, Text, StyleSheet, FlatList, TouchableOpacity, ActivityIndicator} from 'react-native';
import {getWorkOrders, WorkOrder} from '../services/api';
import {useStore} from '../store/useStore';

export default function WorkOrdersScreen() {
  const {workOrders, setWorkOrders} = useStore();
  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadWorkOrders();
  }, []);

  const loadWorkOrders = async () => {
    setIsLoading(true);
    try {
      const orders = await getWorkOrders();
      setWorkOrders(orders);
    } catch (error) {
      console.error('Failed to load work orders:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredOrders = filter === 'all' ? workOrders : workOrders.filter(wo => wo.status === filter);

  const renderWorkOrder = ({item}: {item: WorkOrder}) => (
    <View style={styles.woCard}>
      <View style={styles.woHeader}>
        <Text style={styles.woNumber}>{item.wo_number}</Text>
        <View style={[styles.statusBadge, {backgroundColor: getStatusColor(item.status)}]}>
          <Text style={styles.statusText}>{getStatusText(item.status)}</Text>
        </View>
      </View>
      <Text style={styles.woProduct}>{item.product_name}</Text>
      <View style={styles.woDetails}>
        <Text style={styles.woDetailText}>계획: {item.quantity_planned.toLocaleString()}</Text>
        <Text style={styles.woDetailText}>완료: {item.quantity_completed.toLocaleString()}</Text>
      </View>
      <View style={styles.progressBar}>
        <View style={[styles.progressFill, {width: `${item.progress_percent}%`}]} />
      </View>
      <Text style={styles.progressText}>{item.progress_percent.toFixed(1)}%</Text>
    </View>
  );

  const getStatusColor = (status: string) => {
    return {planned: '#e3f2fd', inprogress: '#fff3cd', completed: '#d1f4e0', delayed: '#f8d7da'}[status] || '#f5f5f5';
  };

  const getStatusText = (status: string) => {
    return {planned: '예정', inprogress: '진행중', completed: '완료', delayed: '지연'}[status] || status;
  };

  return (
    <View style={styles.container}>
      <View style={styles.filterBar}>
        {['all', 'planned', 'inprogress', 'completed', 'delayed'].map(f => (
          <TouchableOpacity key={f} style={[styles.filterBtn, filter === f && styles.filterActive]} onPress={() => setFilter(f)}>
            <Text style={[styles.filterText, filter === f && styles.filterTextActive]}>
              {f === 'all' ? '전체' : getStatusText(f)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      {isLoading ? (
        <ActivityIndicator size="large" color="#667eea" style={styles.loading} />
      ) : (
        <FlatList data={filteredOrders} renderItem={renderWorkOrder} keyExtractor={item => item.wo_id} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#f5f5f5'},
  filterBar: {flexDirection: 'row', padding: 12, backgroundColor: '#fff', gap: 8},
  filterBtn: {paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: '#f5f5f5'},
  filterActive: {backgroundColor: '#667eea'},
  filterText: {fontSize: 14, color: '#666'},
  filterTextActive: {color: '#fff', fontWeight: '600'},
  loading: {marginTop: 40},
  woCard: {backgroundColor: '#fff', margin: 12, padding: 16, borderRadius: 12},
  woHeader: {flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8},
  woNumber: {fontSize: 16, fontWeight: '700'},
  statusBadge: {paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12},
  statusText: {fontSize: 12, fontWeight: '600'},
  woProduct: {fontSize: 14, color: '#666', marginBottom: 12},
  woDetails: {flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12},
  woDetailText: {fontSize: 13, color: '#333'},
  progressBar: {height: 8, backgroundColor: '#e0e0e0', borderRadius: 4, marginBottom: 4},
  progressFill: {height: '100%', backgroundColor: '#667eea', borderRadius: 4'},
  progressText: {fontSize: 12, color: '#999', textAlign: 'right'},
});
