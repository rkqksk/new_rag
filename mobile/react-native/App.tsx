/**
 * RAG Enterprise Mobile App - React Native
 * v7.4.0
 */

import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createStackNavigator} from '@react-navigation/stack';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

// Screens
import HomeScreen from './src/screens/HomeScreen';
import SearchScreen from './src/screens/SearchScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import ImageSearchScreen from './src/screens/ImageSearchScreen';
import QRScanScreen from './src/screens/QRScanScreen';
import WorkOrdersScreen from './src/screens/WorkOrdersScreen';
import ChatScreen from './src/screens/ChatScreen';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// Home Stack
function HomeStack() {
  return (
    <Stack.Navigator screenOptions={{headerShown: true}}>
      <Stack.Screen 
        name="HomeMain" 
        component={HomeScreen}
        options={{title: 'RAG Enterprise'}}
      />
      <Stack.Screen name="ImageSearch" component={ImageSearchScreen} options={{title: '이미지 검색'}} />
      <Stack.Screen name="QRScan" component={QRScanScreen} options={{title: 'QR 스캔'}} />
      <Stack.Screen name="WorkOrders" component={WorkOrdersScreen} options={{title: '작업지시'}} />
      <Stack.Screen name="Chat" component={ChatScreen} options={{title: '채팅'}} />
    </Stack.Navigator>
  );
}

// Main Tab Navigator
function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        tabBarIcon: ({focused, color, size}) => {
          let iconName = 'home';
          if (route.name === 'Home') iconName = 'home';
          else if (route.name === 'Search') iconName = 'magnify';
          else if (route.name === 'Dashboard') iconName = 'view-dashboard';
          else if (route.name === 'Profile') iconName = 'account';
          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#667eea',
        tabBarInactiveTintColor: 'gray',
        headerShown: false,
      })}>
      <Tab.Screen name="Home" component={HomeStack} options={{title: '홈'}} />
      <Tab.Screen name="Search" component={SearchScreen} options={{title: '검색'}} />
      <Tab.Screen name="Dashboard" component={DashboardScreen} options={{title: '대시보드'}} />
      <Tab.Screen name="Profile" component={ProfileScreen} options={{title: '내정보'}} />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <TabNavigator />
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
