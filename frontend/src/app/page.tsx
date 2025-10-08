"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/auth";

export default function Home() {
    const router = useRouter();

    useEffect(() => {
        if (authApi.isAuthenticated()) {
            router.push("/dashboard");
        } else {
            router.push("/login");
        }
    }, [router]);

    return (
        <div className="flex min-h-screen items-center justify-center">
            <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                <p className="mt-4 text-muted-foreground">Loading...</p>
            </div>
        </div>
    );
}
