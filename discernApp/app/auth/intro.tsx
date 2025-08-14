import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image, Linking } from "react-native";
import { router } from "expo-router";
import GoogleSignInButton from "../../components/Button/GoogleSignInButton";

export default function Intro() {
    const handleGoogleSignIn = () => {
        console.log("Google Sign-In pressed");
        // TODO: implement real sign-in logic
    };
    const handleContinue = () => {
        // go to chat (tabs or a dedicated chat stack)
        router.replace("/chat");
    };

    return (
        <View style={styles.container}>
            <View style={styles.logoContainer}>
                <Image source={require("../../assets/images/discern-logo.png")} style={styles.logo} resizeMode="contain" />
            </View>

            <Text style={styles.heading}>
                Ask anything.{"\n"}
                Let the Bible speak.
            </Text>

            <Text style={styles.subheading}>AI built this to reflect God, not replace Him.</Text>

            <View style={styles.valueBox}>
                <Text style={styles.valuePoint}>✓ Backed by pastors & scholars</Text>
                <Text style={styles.valuePoint}>✓ Answers cite real Bible verses</Text>
                <Text style={styles.valuePoint}>✓ Built for all denominations</Text>
            </View>

            <View style={{ height: 40 }} />

            <TouchableOpacity style={styles.secondaryButton} onPress={handleContinue}>
                <Text style={styles.secondaryText}>Continue without an account</Text>
            </TouchableOpacity>

            <GoogleSignInButton onPress={handleGoogleSignIn} />

            <Text style={styles.privacy}>
                We respect your privacy…{" "}
                <Text style={styles.link} onPress={() => Linking.openURL("https://yourdomain.com/privacy")}>
                    Privacy Policy
                </Text>{" "}
                and{" "}
                <Text style={styles.link} onPress={() => Linking.openURL("https://yourdomain.com/terms")}>
                    Terms of Use
                </Text>
                .
            </Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: "#1f1d1e", alignItems: "center", justifyContent: "center", paddingHorizontal: 24 },
    logoContainer: { alignSelf: "flex-start", marginTop: 40 },
    logo: { width: 200, height: 200 },
    heading: { color: "white", fontSize: 40, textAlign: "left", fontWeight: "bold", marginBottom: 10 },
    subheading: { color: "#CCC", fontSize: 16, textAlign: "center" },
    secondaryButton: { marginBottom: 16 },
    secondaryText: { color: "white", fontSize: 16 },
    privacy: { color: "#888", fontSize: 12, textAlign: "center", marginTop: 40, lineHeight: 18 },
    link: { textDecorationLine: "underline", color: "#aaa" },
    valueBox: {
        backgroundColor: "#2a2829",
        borderRadius: 12,
        paddingVertical: 16,
        paddingHorizontal: 60,
        width: "100%",
        marginVertical: 40,
        borderColor: "#444",
        borderWidth: 1,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.2,
        shadowRadius: 4,
        elevation: 3,
    },
    valuePoint: { color: "#EEE", fontSize: 16, fontWeight: "500", paddingVertical: 4 },
});
