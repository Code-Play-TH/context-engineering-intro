import { create } from "zustand";
import { User } from "@/lib/auth";

interface AuthState {
    user: User | null;
    setUser: (user: User | null) => void;
    isAuthenticated: boolean;
    setIsAuthenticated: (isAuthenticated: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    isAuthenticated: false,
    setUser: (user) => set({ user, isAuthenticated: !!user }),
    setIsAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
}));
