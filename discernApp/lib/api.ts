import Constants from "expo-constants";
import { getAuthToken } from "./authToken";

type ApiOptions = {
    method?: string;
    headers?: Record<string, string>;
    body?: any;
    auth?: boolean;           // if true, attach bearer automatically
};

const API_BASE =
    (Constants.expoConfig?.extra as any)?.API_BASE_URL ?? "http://localhost:8000";

export async function apiFetch<T = any>(path: string, opts: ApiOptions = {}): Promise<T> {
    const url = `${API_BASE}${path}`;
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(opts.headers || {}),
    };

    if (opts.auth) {
        const token = getAuthToken();
        if (token) headers.Authorization = `Bearer ${token}`;
    }

    const res = await fetch(url, {
        method: opts.method ?? "POST",
        headers,
        body: typeof opts.body === "string" ? opts.body : opts.body ? JSON.stringify(opts.body) : undefined,
    });

    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `HTTP ${res.status}`);
    }

    const ct = res.headers.get("content-type") || "";
    return ct.includes("application/json") ? (await res.json()) : ((await res.text()) as any);
}
