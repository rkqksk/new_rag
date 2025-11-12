import React, {useState} from 'react';
import {View, Text, StyleSheet, TextInput, TouchableOpacity, FlatList, KeyboardAvoidingView, Platform} from 'react-native';
import {useStore} from '../store/useStore';
import {sendChatMessage} from '../services/api';

export default function ChatScreen() {
  const {messages, addMessage} = useStore();
  const [inputText, setInputText] = useState('');
  const [isSending, setIsSending] = useState(false);

  const handleSend = async () => {
    if (!inputText.trim() || isSending) return;

    const userMessage = {id: Date.now().toString(), text: inputText, sender: 'user' as const, timestamp: new Date()};
    addMessage(userMessage);
    setInputText('');
    setIsSending(true);

    try {
      const response = await sendChatMessage(inputText);
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        text: response.message || '답변을 받지 못했습니다',
        sender: 'assistant' as const,
        timestamp: new Date(),
      };
      addMessage(assistantMessage);
    } catch (error) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        text: '메시지 전송에 실패했습니다',
        sender: 'assistant' as const,
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      setIsSending(false);
    }
  };

  const renderMessage = ({item}: any) => (
    <View style={[styles.messageBubble, item.sender === 'user' ? styles.userBubble : styles.assistantBubble]}>
      <Text style={[styles.messageText, item.sender === 'user' ? styles.userText : styles.assistantText]}>
        {item.text}
      </Text>
    </View>
  );

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <FlatList data={messages} renderItem={renderMessage} keyExtractor={item => item.id} inverted style={styles.messageList} />
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder="메시지를 입력하세요..."
          value={inputText}
          onChangeText={setInputText}
          onSubmitEditing={handleSend}
          returnKeyType="send"
        />
        <TouchableOpacity style={styles.sendButton} onPress={handleSend} disabled={isSending}>
          <Text style={styles.sendButtonText}>전송</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#f5f5f5'},
  messageList: {flex: 1, padding: 16},
  messageBubble: {maxWidth: '80%', padding: 12, borderRadius: 12, marginBottom: 12},
  userBubble: {alignSelf: 'flex-end', backgroundColor: '#667eea'},
  assistantBubble: {alignSelf: 'flex-start', backgroundColor: '#fff'},
  messageText: {fontSize: 16},
  userText: {color: '#fff'},
  assistantText: {color: '#333'},
  inputContainer: {flexDirection: 'row', padding: 12, backgroundColor: '#fff', gap: 8},
  input: {flex: 1, backgroundColor: '#f5f5f5', paddingHorizontal: 16, paddingVertical: 12, borderRadius: 24, fontSize: 16},
  sendButton: {backgroundColor: '#667eea', paddingHorizontal: 24, justifyContent: 'center', borderRadius: 24},
  sendButtonText: {color: '#fff', fontWeight: '600', fontSize: 16},
});
