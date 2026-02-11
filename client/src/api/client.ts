// src/api/client.ts

const config = {
    apiUrl: import.meta.env.VITE_API_BASE_URL as string,
};

if (!config.apiUrl) throw new Error("VITE_API_BASE_URL missing");

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const baseUrl = config.apiUrl.endsWith('/') ? config.apiUrl.slice(0, -1) : config.apiUrl;
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${baseUrl}${cleanEndpoint}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // Bumped to 15s for file uploads

    const isFormData = options.body instanceof FormData;

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            credentials: 'include',
            headers: {
                // ONLY set JSON if it's NOT FormData
                ...(!isFormData && { 'Content-Type': 'application/json' }),
                ...options.headers,
            },
        });

        clearTimeout(timeoutId);
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            let errorMessage = data.detail || "An unexpected error occurred";
            if (Array.isArray(data.detail)) errorMessage = data.detail[0].msg;
            throw new Error(errorMessage);
        }

        return data as T;
    } catch (err: any) {
        if (err.name === 'AbortError') throw new Error("Request timed out.");
        throw err;
    }
}

export const api = {
    get: <T>(endpoint: string) => request<T>(endpoint, { method: 'GET' }),

    post: <T>(endpoint: string, body: any) =>
        request<T>(endpoint, {
            method: 'POST',
            // NEW: Only stringify if it's NOT FormData
            body: body instanceof FormData ? body : JSON.stringify(body)
        }),
};