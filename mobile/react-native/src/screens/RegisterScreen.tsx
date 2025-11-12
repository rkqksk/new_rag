import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {useStore} from '../store/useStore';

type UserRole = 'worker' | 'manager' | 'viewer';

export default function RegisterScreen({navigation}: any) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<UserRole>('worker');
  const [isLoading, setIsLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);
  const {setUser} = useStore();

  const calculatePasswordStrength = (pwd: string): number => {
    let strength = 0;
    if (pwd.length >= 8) strength += 20;
    if (pwd.length >= 12) strength += 20;
    if (/[a-z]/.test(pwd)) strength += 20;
    if (/[A-Z]/.test(pwd)) strength += 20;
    if (/[0-9]/.test(pwd)) strength += 10;
    if (/[^a-zA-Z0-9]/.test(pwd)) strength += 10;
    return strength;
  };

  const handlePasswordChange = (pwd: string) => {
    setPassword(pwd);
    setPasswordStrength(calculatePasswordStrength(pwd));
  };

  const getStrengthColor = () => {
    if (passwordStrength > 70) return '#4ade80';
    if (passwordStrength > 40) return '#ffc107';
    return '#ff6b6b';
  };

  const getStrengthWidth = () => {
    if (passwordStrength > 70) return '100%';
    if (passwordStrength > 40) return '66%';
    if (passwordStrength > 0) return '33%';
    return '0%';
  };

  const validateForm = (): boolean => {
    if (!name.trim()) {
      Alert.alert('오류', '이름을 입력하세요');
      return false;
    }

    if (!email.trim()) {
      Alert.alert('오류', '이메일을 입력하세요');
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      Alert.alert('오류', '유효한 이메일 주소를 입력하세요');
      return false;
    }

    if (password.length < 8) {
      Alert.alert('오류', '비밀번호는 최소 8자 이상이어야 합니다');
      return false;
    }

    if (password !== confirmPassword) {
      Alert.alert('오류', '비밀번호가 일치하지 않습니다');
      return false;
    }

    return true;
  };

  const handleRegister = async () => {
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8001/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          password,
          phone: phone.trim() || null,
          role,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        Alert.alert(
          '회원가입 완료',
          '회원가입이 완료되었습니다. 로그인 페이지로 이동합니다.',
          [
            {
              text: '확인',
              onPress: () => navigation.navigate('Login'),
            },
          ]
        );
      } else {
        Alert.alert('회원가입 실패', data.detail || '회원가입에 실패했습니다');
      }
    } catch (error) {
      console.error('Register error:', error);
      Alert.alert('오류', '서버 연결에 실패했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.logoContainer}>
          <Text style={styles.logoIcon}>🚀</Text>
          <Text style={styles.logoText}>RAG Mobile</Text>
          <Text style={styles.logoSubtext}>새로운 계정 만들기</Text>
        </View>

        <View style={styles.formContainer}>
          <Text style={styles.title}>회원가입</Text>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>이름 *</Text>
            <TextInput
              style={styles.input}
              placeholder="이름을 입력하세요"
              value={name}
              onChangeText={setName}
              autoCapitalize="words"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>이메일 *</Text>
            <TextInput
              style={styles.input}
              placeholder="이메일을 입력하세요"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>전화번호</Text>
            <TextInput
              style={styles.input}
              placeholder="010-1234-5678"
              value={phone}
              onChangeText={setPhone}
              keyboardType="phone-pad"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>비밀번호 *</Text>
            <TextInput
              style={styles.input}
              placeholder="비밀번호를 입력하세요"
              value={password}
              onChangeText={handlePasswordChange}
              secureTextEntry
              autoCapitalize="none"
            />
            <View style={styles.strengthBar}>
              <View
                style={[
                  styles.strengthFill,
                  {
                    width: getStrengthWidth(),
                    backgroundColor: getStrengthColor(),
                  },
                ]}
              />
            </View>
            <Text style={styles.hint}>최소 8자 이상 입력하세요</Text>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>비밀번호 확인 *</Text>
            <TextInput
              style={styles.input}
              placeholder="비밀번호를 다시 입력하세요"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry
              autoCapitalize="none"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>역할</Text>
            <View style={styles.roleContainer}>
              <TouchableOpacity
                style={[styles.roleButton, role === 'worker' && styles.roleButtonActive]}
                onPress={() => setRole('worker')}>
                <Text style={[styles.roleText, role === 'worker' && styles.roleTextActive]}>
                  작업자
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.roleButton, role === 'manager' && styles.roleButtonActive]}
                onPress={() => setRole('manager')}>
                <Text style={[styles.roleText, role === 'manager' && styles.roleTextActive]}>
                  관리자
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.roleButton, role === 'viewer' && styles.roleButtonActive]}
                onPress={() => setRole('viewer')}>
                <Text style={[styles.roleText, role === 'viewer' && styles.roleTextActive]}>
                  조회자
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          <TouchableOpacity
            style={[styles.registerButton, isLoading && styles.registerButtonDisabled]}
            onPress={handleRegister}
            disabled={isLoading}>
            <Text style={styles.registerButtonText}>
              {isLoading ? '가입 중...' : '가입하기'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.loginButton}
            onPress={() => navigation.navigate('Login')}>
            <Text style={styles.loginButtonText}>
              이미 계정이 있으신가요? <Text style={styles.loginButtonTextBold}>로그인</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#667eea',
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logoIcon: {
    fontSize: 56,
    marginBottom: 12,
  },
  logoText: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
  },
  logoSubtext: {
    fontSize: 15,
    color: 'rgba(255,255,255,0.8)',
  },
  formContainer: {
    backgroundColor: 'white',
    borderRadius: 24,
    padding: 24,
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  input: {
    borderWidth: 2,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    color: '#333',
  },
  strengthBar: {
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
    marginTop: 8,
    overflow: 'hidden',
  },
  strengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  hint: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  roleContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  roleButton: {
    flex: 1,
    padding: 12,
    borderWidth: 2,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    alignItems: 'center',
  },
  roleButtonActive: {
    borderColor: '#667eea',
    backgroundColor: '#f8f9ff',
  },
  roleText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  roleTextActive: {
    color: '#667eea',
  },
  registerButton: {
    backgroundColor: '#667eea',
    padding: 18,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  registerButtonDisabled: {
    opacity: 0.6,
  },
  registerButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  loginButton: {
    marginTop: 16,
    padding: 12,
    alignItems: 'center',
  },
  loginButtonText: {
    fontSize: 15,
    color: '#666',
  },
  loginButtonTextBold: {
    fontWeight: 'bold',
    color: '#667eea',
  },
});
