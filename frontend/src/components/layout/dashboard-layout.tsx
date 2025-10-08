"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { authApi } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import {
    LayoutDashboard,
    Users,
    Target,
    FileText,
    MessageSquare,
    Settings,
    LogOut,
    Menu,
} from "lucide-react";
import { useState } from "react";
import Link from "next/link";

interface DashboardLayoutProps {
    children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
    const router = useRouter();
    const { user, setUser } = useAuthStore();
    const [sidebarOpen, setSidebarOpen] = useState(true);

    const handleLogout = async () => {
        await authApi.logout();
        setUser(null);
        router.push("/login");
    };

    const navigation = [
        { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
        { name: "KOLs", href: "/kols", icon: Users },
        { name: "Campaigns", href: "/campaigns", icon: Target },
        { name: "Briefs", href: "/briefs", icon: FileText },
        { name: "Messages", href: "/messages", icon: MessageSquare },
    ];

    if (user?.role === "admin") {
        navigation.push({ name: "Settings", href: "/settings", icon: Settings });
    }

    return (
        <div className="flex h-screen bg-gray-50">
            {/* Sidebar */}
            <aside
                className={`${sidebarOpen ? "w-64" : "w-20"
                    } bg-white border-r transition-all duration-300 flex flex-col`}
            >
                <div className="p-4 border-b flex items-center justify-between">
                    {sidebarOpen && (
                        <h1 className="text-xl font-bold text-primary">KOL System</h1>
                    )}
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="p-2 hover:bg-gray-100 rounded-md"
                    >
                        <Menu className="h-5 w-5" />
                    </button>
                </div>

                <nav className="flex-1 p-4 space-y-2">
                    {navigation.map((item) => (
                        <Link
                            key={item.name}
                            href={item.href}
                            className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-gray-100 transition-colors"
                        >
                            <item.icon className="h-5 w-5 text-gray-600" />
                            {sidebarOpen && (
                                <span className="text-sm font-medium">{item.name}</span>
                            )}
                        </Link>
                    ))}
                </nav>

                <div className="p-4 border-t">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="h-10 w-10 rounded-full bg-primary text-white flex items-center justify-center font-semibold">
                            {user?.full_name.charAt(0).toUpperCase()}
                        </div>
                        {sidebarOpen && (
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">{user?.full_name}</p>
                                <p className="text-xs text-muted-foreground truncate">
                                    {user?.role}
                                </p>
                            </div>
                        )}
                    </div>
                    <Button
                        variant="outline"
                        size={sidebarOpen ? "default" : "icon"}
                        onClick={handleLogout}
                        className="w-full"
                    >
                        <LogOut className="h-4 w-4" />
                        {sidebarOpen && <span className="ml-2">Logout</span>}
                    </Button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                <div className="container mx-auto p-6">{children}</div>
            </main>
        </div>
    );
}
