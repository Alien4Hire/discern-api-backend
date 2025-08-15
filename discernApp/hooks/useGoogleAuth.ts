import * as WebBrowser from "expo-web-browser";
import * as Google from "expo-auth-session/providers/google";
import Constants from "expo-constants";
import { useEffect } from "react";

WebBrowser.maybeCompleteAuthSession();

export function useGoogleIdTokenAuth(onIdToken: (idToken: string) => void) {
    const extra = Constants.expoConfig?.extra ?? {};
    const config = {
        clientId: extra.GOOGLE_WEB_CLIENT_ID,
        iosClientId: extra.GOOGLE_IOS_CLIENT_ID,
        androidClientId: extra.GOOGLE_ANDROID_CLIENT_ID,
        scopes: ["openid", "email", "profile"],
    };

    // Prefer dedicated hook that returns idToken when available
    // Fallback to generic useAuthRequest if your SDK doesn’t have useIdTokenAuthRequest
    const [request, response, promptAsync] = Google.useIdTokenAuthRequest
        ? Google.useIdTokenAuthRequest(config as any)
        : Google.useAuthRequest({
            ...config,
            responseType: "id_token",
            extraParams: { prompt: "select_account" },
        } as any);

    useEffect(() => {
        if (!response) return;
        if (response.type === "success") {
            const idToken =
                // from useIdTokenAuthRequest
                (response.authentication as any)?.idToken ||
                // from useAuthRequest + responseType=id_token
                (response.params as any)?.id_token;

            if (idToken) onIdToken(idToken);
        }
    }, [response]);

    return { request, promptAsync };
}
