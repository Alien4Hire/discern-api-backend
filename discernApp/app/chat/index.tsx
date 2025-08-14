// app/chat/index.tsx
import React, { useCallback, useEffect, useState } from 'react';
import {
    ImageBackground,
    Platform,
    StyleSheet,
    View,
    KeyboardAvoidingView,
} from 'react-native';
import {
    GiftedChat,
    Bubble,
    InputToolbar,
    Composer,
    Send,
    IMessage,
} from 'react-native-gifted-chat';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function Chat() {
    const insets = useSafeAreaInsets();
    // pad the bottom by the device inset; add a little breathing room
    const bottomPad = Math.max(insets.bottom, 12);

    const [messages, setMessages] = useState<IMessage[]>([]);
    const [isTyping, setIsTyping] = useState(false);

    useEffect(() => {
        setMessages([
            {
                _id: 'seed-1',
                text: 'God is our refuge and strength, a very present help in trouble. (Ps 46:1)',
                createdAt: new Date(),
                user: { _id: 'discern', name: 'Discern AI' },
            },
        ]);
    }, []);

    const onSend = useCallback(async (newMsgs: IMessage[] = []) => {
        setMessages(prev => GiftedChat.append(prev, newMsgs));
        setIsTyping(true);
        const question = newMsgs[0]?.text ?? '';
        setTimeout(() => {
            setMessages(prev =>
                GiftedChat.append(prev, [
                    {
                        _id: String(Date.now()),
                        text: `Here’s a verse for “${question}” — “Trust in the LORD with all your heart…” (Prov 3:5)`,
                        createdAt: new Date(),
                        user: { _id: 'discern', name: 'Discern AI' },
                    },
                ])
            );
            setIsTyping(false);
        }, 900);
    }, []);

    return (
        <ImageBackground
            source={require('../../assets/images/chat-bg.png')}
            style={styles.bg}
            resizeMode="cover"
        >
            <View style={styles.overlay} />

            <KeyboardAvoidingView
                style={{ flex: 1 }}
                behavior={Platform.OS === 'ios' ? 'padding' : undefined}
                // If you show a header titled "Chat", add ~56 for its height.
                keyboardVerticalOffset={Platform.select({ ios: insets.top + 56, android: 0 })}
            >
                <GiftedChat
                    messages={messages}
                    onSend={onSend}
                    user={{ _id: 'me' }}
                    isTyping={isTyping}
                    placeholder="Write any question here"
                    alignTop
                    alwaysShowSend
                    bottomOffset={bottomPad}               // << keeps input above nav bar

                    renderBubble={(props) => (
                        <Bubble
                            {...props}
                            wrapperStyle={{
                                left: { backgroundColor: '#2a2a2c', borderRadius: 18, padding: 2 },
                                right: { backgroundColor: '#3b82f6', borderRadius: 18, padding: 2 },
                            }}
                            textStyle={{
                                left: { color: '#fff', fontSize: 16 },
                                right: { color: '#fff', fontSize: 16 },
                            }}
                        />
                    )}

                    renderInputToolbar={(props) => (
                        <InputToolbar
                            {...props}
                            containerStyle={[
                                styles.inputContainer,
                                { paddingBottom: bottomPad },     // << extra bottom padding
                            ]}
                            primaryStyle={{ alignItems: 'center' }}
                        />
                    )}

                    renderComposer={(props) => (
                        <Composer
                            {...props}
                            textInputStyle={styles.composer}
                            placeholderTextColor="#9CA3AF"
                        />
                    )}

                    renderSend={(props) => (
                        <Send {...props} containerStyle={{ justifyContent: 'center', paddingHorizontal: 6 }} />
                    )}

                    messagesContainerStyle={styles.messagesContainer}
                />
            </KeyboardAvoidingView>
        </ImageBackground>
    );
}

const styles = StyleSheet.create({
    bg: { flex: 1, backgroundColor: '#0f0f10' },
    overlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(8,8,10,0.25)' },
    messagesContainer: { paddingTop: 8, paddingHorizontal: 8 },
    inputContainer: { backgroundColor: 'transparent', borderTopWidth: 0, paddingHorizontal: 8, paddingTop: 8 },
    composer: {
        backgroundColor: '#1e1e20',
        color: '#fff',
        borderRadius: 22,
        paddingHorizontal: 14,
        paddingTop: 10,
        paddingBottom: 10,
        fontSize: 16,
    },
});
