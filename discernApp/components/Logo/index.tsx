import React, { useEffect, useRef } from 'react';
import {
    Animated,
    Dimensions,
    Image,
    StyleSheet,
    View,
    StatusBar,
} from 'react-native';

const { width, height } = Dimensions.get('window');

type Props = {
    onFinish: () => void;
};

export default function DiscernLogo({ onFinish }: Props) {
    // Animated values for logo position and opacity
    const translateX = useRef(new Animated.Value(-width / 2)).current;
    const translateY = useRef(new Animated.Value(height / 2)).current;
    const opacity = useRef(new Animated.Value(0)).current;

    useEffect(() => {
        // Animate logo into center
        Animated.parallel([
            Animated.timing(translateX, {
                toValue: 0,
                duration: 700,
                useNativeDriver: true,
            }),
            Animated.timing(translateY, {
                toValue: 0,
                duration: 700,
                useNativeDriver: true,
            }),
            Animated.timing(opacity, {
                toValue: 1,
                duration: 400,
                useNativeDriver: true,
            }),
        ]).start(() => {
            // Wait a bit, then signal finished
            setTimeout(() => {
                onFinish?.();
            }, 1200);
        });
    }, []);

    return (
        <View style={styles.container}>
            <StatusBar hidden />
            <Animated.Image
                source={require('../../assets/images/discern-logo.png')}
                style={[
                    styles.logo,
                    {
                        transform: [
                            { translateX },
                            { translateY },
                        ],
                        opacity,
                    },
                ]}
                resizeMode="contain"
            />
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        backgroundColor: '#1f1d1e',
        position: 'absolute',
        width: '100%',
        height: '100%',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 999,
    },
    logo: {
        width: 200,
        height: 200,
    },
});