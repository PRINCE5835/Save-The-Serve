"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { UserProfile, UserRole } from "@/lib/types";
import { initialUsers } from "@/lib/mock-data";

interface AuthContextType {
  user: UserProfile | null;
  role: UserRole;
  isAuthenticated: boolean;
  login: (email: string, role: UserRole, password?: string) => Promise<boolean>;
  signup: (data: {
    name: string;
    email: string;
    role: UserRole;
    phone?: string;
    organizationName?: string;
    vehicleType?: string;
  }) => Promise<boolean>;
  logout: () => void;
  switchRole: (newRole: UserRole) => void;
  updateProfile: (data: Partial<UserProfile>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(initialUsers[0]);
  const [role, setRole] = useState<UserRole>("donor");

  useEffect(() => {
    try {
      const savedUser = localStorage.getItem("sts_auth_user");
      if (savedUser) {
        const parsed = JSON.parse(savedUser) as UserProfile;
        setUser(parsed);
        setRole(parsed.role);
      } else {
        localStorage.setItem("sts_auth_user", JSON.stringify(initialUsers[0]));
      }
    } catch (err) {
      console.warn("Storage error:", err);
    }
  }, []);

  const login = async (email: string, selectedRole: UserRole): Promise<boolean> => {
    const existing = initialUsers.find((u) => u.role === selectedRole);
    const userToSet: UserProfile = existing
      ? { ...existing, email }
      : {
          id: `usr_${Date.now()}`,
          name: email.split("@")[0].replace(".", " "),
          email,
          role: selectedRole,
          verified: true,
          phone: "+1 (555) 000-1234",
          address: "Mission District, San Francisco",
          organizationName: selectedRole === "ngo" ? "Registered NGO Partner" : undefined,
          vehicleType: selectedRole === "driver" ? "Standard Van" : undefined,
        };

    setUser(userToSet);
    setRole(selectedRole);
    try {
      localStorage.setItem("sts_auth_user", JSON.stringify(userToSet));
    } catch {}
    return true;
  };

  const signup = async (data: {
    name: string;
    email: string;
    role: UserRole;
    phone?: string;
    organizationName?: string;
    vehicleType?: string;
  }): Promise<boolean> => {
    const newUser: UserProfile = {
      id: `usr_${Date.now()}`,
      name: data.name,
      email: data.email,
      role: data.role,
      phone: data.phone || "+1 (555) 444-5555",
      address: "Downtown Hub, SF",
      organizationName: data.organizationName,
      vehicleType: data.vehicleType,
      verified: true,
      avatarUrl: `https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80`,
    };

    setUser(newUser);
    setRole(data.role);
    try {
      localStorage.setItem("sts_auth_user", JSON.stringify(newUser));
    } catch {}
    return true;
  };

  const logout = () => {
    setUser(null);
    try {
      localStorage.removeItem("sts_auth_user");
    } catch {}
  };

  const switchRole = (newRole: UserRole) => {
    const foundDemo = initialUsers.find((u) => u.role === newRole) || {
      id: `usr_${newRole}_${Date.now()}`,
      name: `Active ${newRole.toUpperCase()} User`,
      email: `${newRole}@sts-platform.org`,
      role: newRole,
      verified: true,
    };
    setUser(foundDemo);
    setRole(newRole);
    try {
      localStorage.setItem("sts_auth_user", JSON.stringify(foundDemo));
    } catch {}
  };

  const updateProfile = (data: Partial<UserProfile>) => {
    if (!user) return;
    const updated = { ...user, ...data };
    setUser(updated);
    try {
      localStorage.setItem("sts_auth_user", JSON.stringify(updated));
    } catch {}
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user ? user.role : role,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
        switchRole,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
