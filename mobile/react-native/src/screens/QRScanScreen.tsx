import React, {useState} from 'react';
import {View, Text, StyleSheet, TouchableOpacity, Alert} from 'react-native';
import QRCodeScanner from 'react-native-qrcode-scanner';
import {scanQRCode} from '../services/api';

export default function QRScanScreen({navigation}: any) {
  const [scanned, setScanned] = useState(false);

  const onSuccess = async (e: any) => {
    if (scanned) return;
    setScanned(true);

    try {
      const result = await scanQRCode(e.data);
      Alert.alert('QR 코드 인식', `데이터: ${e.data}\n\n제품: ${result.product?.name || '알 수 없음'}`,
        [{text: '확인', onPress: () => setScanned(false)}]
      );
    } catch (error) {
      Alert.alert('QR 코드 인식', `데이터: ${e.data}`, [{text: '확인', onPress: () => setScanned(false)}]);
    }
  };

  return (
    <View style={styles.container}>
      <QRCodeScanner
        onRead={onSuccess}
        reactivate={!scanned}
        reactivateTimeout={3000}
        topContent={<Text style={styles.title}>QR 코드를 스캔하세요</Text>}
        bottomContent={
          <TouchableOpacity style={styles.button} onPress={() => navigation.goBack()}>
            <Text style={styles.buttonText}>뒤로 가기</Text>
          </TouchableOpacity>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#000'},
  title: {fontSize: 18, color: '#fff', fontWeight: '600', marginBottom: 20},
  button: {backgroundColor: '#667eea', padding: 16, borderRadius: 8, marginTop: 20},
  buttonText: {color: '#fff', fontSize: 16, fontWeight: '600', textAlign: 'center'},
});
