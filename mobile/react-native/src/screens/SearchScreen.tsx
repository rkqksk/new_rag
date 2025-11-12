import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  FlatList,
  Image,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import {useStore} from '../store/useStore';
import {searchProducts} from '../services/api';

export default function SearchScreen({navigation}: any) {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const {searchResults, setSearchResults, recentSearches, addRecentSearch} =
    useStore();

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const data = await searchProducts(searchQuery, 20);
      setSearchResults(data.results || []);
      addRecentSearch(searchQuery);
    } catch (error) {
      console.error('Search failed:', error);
      Alert.alert('검색 실패', '검색 중 오류가 발생했습니다');
    } finally {
      setIsSearching(false);
    }
  };

  const handleRecentSearchPress = (searchQuery: string) => {
    setQuery(searchQuery);
    handleSearch(searchQuery);
  };

  const renderSearchResult = ({item}: any) => (
    <TouchableOpacity style={styles.resultCard}>
      <Image
        source={{uri: item.image_url || 'https://via.placeholder.com/100'}}
        style={styles.resultImage}
      />
      <View style={styles.resultInfo}>
        <Text style={styles.resultName}>{item.name}</Text>
        <Text style={styles.resultCategory}>{item.category}</Text>
        <View style={styles.resultFooter}>
          <Text style={styles.resultPrice}>₩{item.price?.toLocaleString()}</Text>
          <View
            style={[
              styles.stockBadge,
              {backgroundColor: item.in_stock ? '#d1f4e0' : '#f8d7da'},
            ]}>
            <Text
              style={[
                styles.stockText,
                {color: item.in_stock ? '#0f5132' : '#721c24'},
              ]}>
              {item.in_stock ? '재고 있음' : '품절'}
            </Text>
          </View>
        </View>
        <Text style={styles.resultScore}>
          유사도: {(item.score * 100).toFixed(0)}%
        </Text>
      </View>
    </TouchableOpacity>
  );

  const renderRecentSearch = ({item}: {item: string}) => (
    <TouchableOpacity
      style={styles.recentItem}
      onPress={() => handleRecentSearchPress(item)}>
      <Text style={styles.recentIcon}>🕐</Text>
      <Text style={styles.recentText}>{item}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchBar}>
        <TextInput
          style={styles.searchInput}
          placeholder="제품 검색..."
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={() => handleSearch(query)}
          returnKeyType="search"
        />
        <TouchableOpacity
          style={styles.searchButton}
          onPress={() => handleSearch(query)}>
          <Text style={styles.searchButtonText}>검색</Text>
        </TouchableOpacity>
      </View>

      {/* Recent Searches */}
      {!isSearching && searchResults.length === 0 && recentSearches.length > 0 && (
        <View style={styles.recentSection}>
          <Text style={styles.sectionTitle}>최근 검색</Text>
          <FlatList
            data={recentSearches}
            renderItem={renderRecentSearch}
            keyExtractor={(item, index) => `recent-${index}`}
            horizontal
            showsHorizontalScrollIndicator={false}
          />
        </View>
      )}

      {/* Loading */}
      {isSearching && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#667eea" />
          <Text style={styles.loadingText}>검색 중...</Text>
        </View>
      )}

      {/* Search Results */}
      {!isSearching && searchResults.length > 0 && (
        <View style={styles.resultsContainer}>
          <Text style={styles.resultsCount}>
            {searchResults.length}개의 결과
          </Text>
          <FlatList
            data={searchResults}
            renderItem={renderSearchResult}
            keyExtractor={item => item.id}
            showsVerticalScrollIndicator={false}
          />
        </View>
      )}

      {/* Empty State */}
      {!isSearching && searchResults.length === 0 && query && (
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>🔍</Text>
          <Text style={styles.emptyText}>검색 결과가 없습니다</Text>
          <Text style={styles.emptyHint}>다른 키워드로 검색해보세요</Text>
        </View>
      )}

      {/* Quick Actions */}
      {!isSearching && searchResults.length === 0 && !query && (
        <View style={styles.quickActions}>
          <Text style={styles.sectionTitle}>빠른 검색</Text>
          <View style={styles.quickGrid}>
            <TouchableOpacity
              style={styles.quickCard}
              onPress={() => navigation.navigate('ImageSearch')}>
              <Text style={styles.quickIcon}>📸</Text>
              <Text style={styles.quickLabel}>이미지 검색</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.quickCard}
              onPress={() => navigation.navigate('QRScan')}>
              <Text style={styles.quickIcon}>📱</Text>
              <Text style={styles.quickLabel}>QR 스캔</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  searchBar: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    gap: 8,
  },
  searchInput: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    fontSize: 16,
  },
  searchButton: {
    backgroundColor: '#667eea',
    paddingHorizontal: 20,
    justifyContent: 'center',
    borderRadius: 8,
  },
  searchButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  recentSection: {
    padding: 16,
    backgroundColor: '#fff',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
    color: '#333',
  },
  recentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
  },
  recentIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  recentText: {
    fontSize: 14,
    color: '#333',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#999',
  },
  resultsContainer: {
    flex: 1,
    padding: 16,
  },
  resultsCount: {
    fontSize: 14,
    color: '#999',
    marginBottom: 12,
  },
  resultCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  resultImage: {
    width: 80,
    height: 80,
    borderRadius: 8,
    backgroundColor: '#f5f5f5',
  },
  resultInfo: {
    flex: 1,
    marginLeft: 12,
  },
  resultName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  resultCategory: {
    fontSize: 14,
    color: '#999',
    marginBottom: 8,
  },
  resultFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  resultPrice: {
    fontSize: 16,
    fontWeight: '700',
    color: '#667eea',
  },
  stockBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  stockText: {
    fontSize: 12,
    fontWeight: '600',
  },
  resultScore: {
    fontSize: 12,
    color: '#999',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  emptyHint: {
    fontSize: 14,
    color: '#999',
  },
  quickActions: {
    flex: 1,
    padding: 16,
  },
  quickGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  quickCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  quickIcon: {
    fontSize: 40,
    marginBottom: 8,
  },
  quickLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
});
