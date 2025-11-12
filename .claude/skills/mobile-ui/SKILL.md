# Mobile UI Skill

## Overview
Specialist in React Native UI development with platform-specific optimizations and native features.

## Trigger Words
- react native
- mobile ui
- native components
- expo
- mobile app
- ios android

## Capabilities

### React Native Components
- Core components (View, Text, ScrollView, FlatList)
- Navigation (React Navigation, Native Stack)
- Platform-specific code
- Custom native modules
- Gesture handling

### Platform Detection
```typescript
import { Platform, Dimensions } from 'react-native'

const isIOS = Platform.OS === 'ios'
const isAndroid = Platform.OS === 'android'
const { width, height } = Dimensions.get('window')

// Platform-specific styling
const styles = StyleSheet.create({
  container: {
    ...Platform.select({
      ios: { paddingTop: 20 },
      android: { paddingTop: 0 }
    })
  }
})
```

### Native Features

#### Biometric Authentication
```typescript
import * as LocalAuthentication from 'expo-local-authentication'

const authenticate = async () => {
  const hasHardware = await LocalAuthentication.hasHardwareAsync()
  const supportedTypes = await LocalAuthentication.supportedAuthenticationTypesAsync()

  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Authenticate to access your account',
    fallbackLabel: 'Use passcode'
  })

  return result.success
}
```

#### Camera Integration
```typescript
import { Camera } from 'expo-camera'

const CameraScreen = () => {
  const [hasPermission, setHasPermission] = useState(null)
  const [type, setType] = useState(Camera.Constants.Type.back)

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync()
      setHasPermission(status === 'granted')
    })()
  }, [])
}
```

### Performance Optimization

#### List Optimization
```typescript
// Optimized FlatList
<FlatList
  data={data}
  renderItem={renderItem}
  keyExtractor={(item) => item.id}
  initialNumToRender={10}
  maxToRenderPerBatch={10}
  windowSize={10}
  removeClippedSubviews={true}
  getItemLayout={(data, index) => ({
    length: ITEM_HEIGHT,
    offset: ITEM_HEIGHT * index,
    index
  })}
/>
```

#### Memory Management
```typescript
// Image optimization
import FastImage from 'react-native-fast-image'

<FastImage
  source={{ uri: imageUrl, priority: FastImage.priority.normal }}
  style={styles.image}
  resizeMode={FastImage.resizeMode.cover}
/>
```

### Navigation Patterns

#### Stack Navigation
```typescript
import { createNativeStackNavigator } from '@react-navigation/native-stack'

const Stack = createNativeStackNavigator()

function AppNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="Home" component={HomeScreen} />
      <Stack.Screen name="Details" component={DetailsScreen} />
    </Stack.Navigator>
  )
}
```

#### Tab Navigation
```typescript
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs'

const Tab = createBottomTabNavigator()

function TabNavigator() {
  return (
    <Tab.Navigator>
      <Tab.Screen name="Feed" component={FeedScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  )
}
```

### Styling Best Practices

```typescript
// Responsive design
import { useWindowDimensions } from 'react-native'

const ResponsiveComponent = () => {
  const { width, height, scale, fontScale } = useWindowDimensions()

  return (
    <View style={[styles.container, { width: width * 0.9 }]}>
      <Text style={{ fontSize: 16 * fontScale }}>
        Responsive Text
      </Text>
    </View>
  )
}
```

### Gesture Handling

```typescript
import { GestureHandlerRootView, PanGestureHandler } from 'react-native-gesture-handler'
import Animated, {
  useAnimatedGestureHandler,
  useAnimatedStyle,
  useSharedValue,
  withSpring
} from 'react-native-reanimated'

const SwipeableCard = () => {
  const translateX = useSharedValue(0)

  const gestureHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      translateX.value = event.translationX
    },
    onEnd: () => {
      translateX.value = withSpring(0)
    }
  })

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }]
  }))
}
```

## Expo SDK Features

### Push Notifications
```typescript
import * as Notifications from 'expo-notifications'

const registerForPushNotifications = async () => {
  const { status } = await Notifications.requestPermissionsAsync()
  if (status !== 'granted') return

  const token = await Notifications.getExpoPushTokenAsync()
  return token.data
}
```

### Background Tasks
```typescript
import * as BackgroundFetch from 'expo-background-fetch'
import * as TaskManager from 'expo-task-manager'

TaskManager.defineTask(BACKGROUND_FETCH_TASK, async () => {
  // Background work
  return BackgroundFetch.BackgroundFetchResult.NewData
})
```

## Testing

### Component Testing
```typescript
import { render, fireEvent } from '@testing-library/react-native'

test('button press', () => {
  const onPress = jest.fn()
  const { getByText } = render(<Button onPress={onPress} title="Press me" />)

  fireEvent.press(getByText('Press me'))
  expect(onPress).toHaveBeenCalled()
})
```

### E2E Testing with Detox
```javascript
describe('App E2E', () => {
  beforeAll(async () => {
    await device.launchApp()
  })

  it('should show welcome screen', async () => {
    await expect(element(by.id('welcome'))).toBeVisible()
  })
})
```

## Build & Deployment

### EAS Build
```bash
# Development build
eas build --platform ios --profile development

# Production build
eas build --platform all --profile production

# Submit to stores
eas submit --platform ios
eas submit --platform android
```

## Common Issues & Solutions

1. **Metro bundler issues**: Clear cache with `npx react-native start --reset-cache`
2. **iOS build failures**: Clean build folder `cd ios && pod install`
3. **Android build issues**: `cd android && ./gradlew clean`
4. **Performance**: Use Flipper for profiling

## Related Skills
- native-features
- platform-bridge
- component-library
- mobile-agent