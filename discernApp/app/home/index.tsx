import { useState } from 'react';
import { View, StyleSheet, Text } from 'react-native';
import DiscernLogo from '../../components/Logo';
import Intro from '../auth/intro';

export default function HomeScreen() {
    const [showLogo, setShowLogo] = useState(true);

    return (
        <View style={styles.container}>
            {showLogo ? (
                <DiscernLogo onFinish={() => setShowLogo(false)} />
            ) : (
                <Intro />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
    },
});