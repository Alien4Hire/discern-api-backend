let _token: string | null = null;

export const setAuthToken = (t: string | null) => { _token = t; };
export const getAuthToken = () => _token;
export const clearAuthToken = () => { _token = null; };
