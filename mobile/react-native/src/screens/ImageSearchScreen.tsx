import React, {useState} from 'react';
import {View, Text, StyleSheet, TouchableOpacity, Image, ActivityIndicator, Alert} from 'react-native';
import {launchCamera, launchImageLibrary} from 'react-native-image-picker';
import {imageSearch} from '../services/api';
import {useStore} from '../store/useStore';

export default function ImageSearchScreen({navigation}: any) {
  const [imageUri, setImageUri] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const {setSearchResults} = useStore();

  const handleCamera = async () => {
    const result = await launchCamera({mediaType: 'photo', quality: 0.8});
    if (result.assets && result.assets[0].uri) {
      performImageSearch(result.assets[0].uri);
    }
  };

  const handleGallery = async () => {
    const result = await launchImageLibrary({mediaType: 'photo', quality: 0.8});
    if (result.assets && result.assets[0].uri) {
      performImageSearch(result.assets[0].uri);
    }
  };

  const performImageSearch = async (uri: string) => {
    setImageUri(uri);
    setIsSearching(true);
    try {
      const data = await imageSearch(uri);
      setSearchResults(data.results || []);
      navigation.navigate('Search');
    } catch (error) {
      Alert.alert('검색 실패', '이미지 검색 중 오류가 발생했습니다');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>이미지로 제품 검색</Text>
      <Text style={styles.subtitle}>사진을 찍거나 갤러리에서 선택하세요</Text>

      {imageUri ? (
        <Image source={{uri: imageUri}} style={styles.previewImage} />
      ) : (
        <View style={styles.placeholder}>
          <Text style={styles.placeholderIcon}>📸</Text>
        </View>
      )}

      {isSearching ? (
        <ActivityIndicator size="large" color="#667eea" style={styles.loading} />
      ) : (
        <View style={styles.buttonContainer}>
          <TouchableOpacity style={styles.button} onPress={handleCamera}>
            <Text style={styles.buttonText}>📷 카메라</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.button} onPress={handleGallery}>
            <Text style={styles.buttonText}>🖼️ 갤러리</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, padding: 20, backgroundColor: '#f5f5f5', alignItems: 'center'},
  title: {fontSize: 24, fontWeight: 'bold', marginBottom: 8, color: '#333'},
  subtitle: {fontSize: 16, color: '#666', marginBottom: 30},
  placeholder: {width: 300, height: 300, backgroundColor: '#e0e0e0', borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginBottom: 30},
  placeholderIcon: {fontSize: 80},
  previewImage: {width: 300, height: 300, borderRadius: 12, marginBottom: 30},
  loading: {marginTop: 20},
  buttonContainer: {flexDirection: 'row', gap: 12},
  button: {flex: 1, backgroundColor: '#667eea', padding: 16, borderRadius: 8, alignItems: 'center'},
  buttonText: {color: '#fff', fontSize: 16, fontWeight: '600'},
});
