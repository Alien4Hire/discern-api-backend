// stores/auth.ts
// Adds a dev-only login method and fixes the google endpoint path

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { apiFetch } from "../lib/api";
import { setAuthToken, clearAuthToken } from "../lib/authToken";

// Defines the user type
type User = {
    id?: string;
    email: string;
    first_name?: string;
    last_name?: string;
    role: "admin" | "trial" | "subscriber" | "unsubscribed";
};

// Defines the auth store shape
type AuthState = {
    token: string | null;
    user: User | null;
    loading: boolean;
    error: string | null;

    loginWithGoogle: (idToken: string) => Promise<void>;
    loginWithPassword: (email: string, password: string) => Promise<void>;
    logout: () => void;
    fetchMe: () => Promise<void>;
    loginDev: (email: string) => Promise<void>;
};

// Determines if we are in dev
const IS_DEV = __DEV__ || process.env.EXPO_PUBLIC_ENV === "development";

// Creates the store
export const authStore = create<AuthState>()(
    // Persists the store
    persist(
        (set, get) => ({
            token: null,
            user: null,
            loading: false,
            error: null,

            // Implements Google login using your API
            loginWithGoogle: async (idToken: string) => {
                set({ loading: true, error: null });
                try {
                    // Calls the correct endpoint name
                    const res = await apiFetch<{ access_token: string; user?: User; profile?: any }>(
                        "/auth/google/login",
                        { method: "POST", body: { id_token: idToken } }
                    );
                    // Sets the token globally
                    setAuthToken(res.access_token);
                    // Chooses user shape depending on backend response
                    const user = res.user ?? {
                        email: res.profile?.email,
                        first_name: res.profile?.first_name,
                        last_name: res.profile?.last_name,
                        role: (res as any).role ?? "unsubscribed",
                    };
                    // Updates store
                    set({ token: res.access_token, user, loading: false });
                } catch (e: any) {
                    // Stores error
                    set({ error: e.message || "Google login failed", loading: false });
                    // Re-throws for UI handling
                    throw e;
                }
            },

            // Implements password login
            loginWithPassword: async (email: string, password: string) => {
                // Sets loading true
                set({ loading: true, error: null });
                try {
                    // Builds form body
                    const form = new URLSearchParams();
                    // Adds username
                    form.append("username", email);
                    // Adds password
                    form.append("password", password);

                    // Requests token
                    const tokenRes = await apiFetch<{ access_token: string; token_type: string }>(
                        "/auth/login",
                        {
                            method: "POST",
                            headers: { "Content-Type": "application/x-www-form-urlencoded" },
                            body: form.toString(),
                        }
                    );

                    // Persists token
                    setAuthToken(tokenRes.access_token);
                    // Stores token
                    set({ token: tokenRes.access_token });

                    // Fetches user info
                    const me = await apiFetch<User>("/auth/get-user-data", { method: "GET", auth: true });
                    // Stores user
                    set({ user: me, loading: false });
                } catch (e: any) {
                    // Stores error
                    set({ error: e.message || "Login failed", loading: false });
                    // Re-throws for UI handling
                    throw e;
                }
            },

            // Implements dev login
            loginDev: async (email: string) => {
                // Sets loading true
                set({ loading: true, error: null });
                try {
                    // Guards to only call in dev
                    if (!IS_DEV) throw new Error("Dev login not allowed in this build");

                    // Calls the dev auth endpoint
                    const res = await apiFetch<{ access_token: string; role: string; profile: any }>(
                        "/auth/dev/login",
                        {
                            method: "POST",
                            body: { email },
                        }
                    );

                    // # Sets token for subsequent requests
                    setAuthToken(res.access_token);
                    // # Builds a user from the dev payload
                    const user: User = {
                        email: res.profile?.email,
                        first_name: res.profile?.first_name,
                        last_name: res.profile?.last_name,
                        role: (res.role as User["role"]) ?? "unsubscribed",
                    };
                    // # Updates store
                    set({ token: res.access_token, user, loading: false });
                } catch (e: any) {
                    // # Stores error
                    set({ error: e.message || "Dev login failed", loading: false });
                    // # Re - throws for UI handling
                    throw e;
                }
            },

            // # Implements logout
            logout: () => {
                // # Clears auth token
                clearAuthToken();
                // # Resets store state
                set({ token: null, user: null, error: null });
            },

            // # Implements fetchMe
            fetchMe: async () => {
                try {
                    // # Requests / me
                    const me = await apiFetch<User>("/auth/get-user-data", { method: "GET", auth: true });
                    // # Stores user
                    set({ user: me });
                } catch {
                    // # Clears token on failure
                    clearAuthToken();
                    // # Resets auth - related state
                    set({ token: null, user: null });
                }
            },
        }),
        {
            // # Names the persisted key
            name: "discern-auth",
            // # Uses AsyncStorage for persistence
            storage: createJSONStorage(() => AsyncStorage),
            // # Persists only token and user
            partialize: (s) => ({ token: s.token, user: s.user }),
            // # Hydrates token into auth module on rehydrate
            onRehydrateStorage: () => (state) => {
                // # Sets the module token if present
                if (state?.token) setAuthToken(state.token);
            },
        }
    )
);
