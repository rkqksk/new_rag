import React from 'react'
import { NavigationContainer } from '@react-navigation/native'
import { AuthProvider } from '@rag/core/auth'
import { AppNavigator } from './src/navigation/AppNavigator'

export default function App() {
  return (
    <NavigationContainer>
      <AuthProvider>
        <AppNavigator />
      </AuthProvider>
    </NavigationContainer>
  )
}
