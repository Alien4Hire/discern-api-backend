// app/chat/_layout.tsx
import { Stack } from 'expo-router';
import React from 'react';

export default function ChatLayout() {
    return (
        <Stack
            screenOptions={{
                headerShown: true,
                headerTitle: 'Chat',
                headerTintColor: '#fff',
                headerStyle: { backgroundColor: '#151516' }, // dark bar
                headerTitleStyle: { fontWeight: '600' },
            }}
        />
    );
}
