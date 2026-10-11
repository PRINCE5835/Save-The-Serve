"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { UserRole } from "@/lib/types";
import {
  HeartHandshake,
  ShieldAlert,
  Compass,
  LifeBuoy,
  Settings,
  User,
  LogOut,
  ChevronDown,
  Sparkles,
  Truck,
  Building2,
  Gift,
  Menu,
  X,
  CheckCircle2,
} from "lucide-react";

export function Navbar() {
  const { user, role, switchRole, logout, isAuthenticated } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const roleColors: Record<UserRole, { bg: string; text: string; border: string; label: string; icon: any }> = {
    donor: {
      bg: "bg-emerald-50 dark:bg-emerald-950/60",
      text: "text-emerald-700 dark:text-emerald-300",
      border: "border-emerald-200 dark:border-emerald-800",
      label: "Donor Portal",
      icon: Gift,
    },
    ngo: {
      bg: "bg-blue-50 dark:bg-blue-950/60",
      text: "text-blue-700 dark:text-blue-300",
      border: "border-blue-200 dark:border-blue-800",
      label: "NGO Command",
      icon: Building2,
    },
    driver: {
      bg: "bg-amber-50 dark:bg-amber-950/60",
      text: "text-amber-700 dark:text-amber-300",
      border: "border-amber-200 dark:border-amber-800",
      label: "Driver Logistics",
      icon: Truck,
    },
  };

  const currentRoleStyle = roleColors[role] || roleColors.donor;
  const RoleIcon = currentRoleStyle.icon;

  const handleRoleSwitch = (newRole: UserRole) => {
    switchRole(newRole);
    setRoleMenuOpen(false);

    router.push(`/${newRole}`);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/80 backdrop-blur-md dark:border-slate-800/80 dark:bg-slate-900/80">

      <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-700 text-white text-xs py-1 px-4 text-center font-medium tracking-wide flex items-center justify-center gap-2">
        <span className="flex h-2 w-2 rounded-full bg-emerald-200 animate-pulse" />
        <span>S.T.S Automated Watchdog Active: Surplus cooked food with &lt; 2h expiry is auto-escalated to Critical Urgency</span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-500/20 group-hover:scale-105 transition-transform duration-200">
              <HeartHandshake className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-lg tracking-tight text-slate-900 dark:text-white">
                  Save The Serve
                </span>
                <span className="text-[10px] font-black uppercase px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700">
                  S.T.S
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                Geospatial Food &amp; Relief Dispatch
              </p>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            <Link
              href="/"
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                pathname === "/"
                  ? "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800/50"
              }`}
            >
              Overview
            </Link>

            <Link
              href={`/${role}`}
              className={`px-3 py-1.5 text-sm font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                pathname.startsWith(`/${role}`)
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-emerald-700 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/50"
              }`}
            >
              <RoleIcon className="w-4 h-4" />
              <span>{role === "donor" ? "Donor Hub" : role === "ngo" ? "NGO Feed" : "Driver Runs"}</span>
            </Link>

            <Link
              href="/directory"
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
                pathname === "/directory"
                  ? "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800/50"
              }`}
            >
              <Compass className="w-4 h-4" />
              <span>NGO Directory</span>
            </Link>

            <Link
              href="/mobile"
              className={`px-3 py-1.5 text-sm font-semibold rounded-lg transition-colors flex items-center gap-1.5 ${
                pathname === "/mobile"
                  ? "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800/50"
              }`}
            >
              <span>📱 Mobile App</span>
            </Link>

            <Link
              href="/help"
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
                pathname === "/help"
                  ? "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800/50"
              }`}
            >
              <LifeBuoy className="w-4 h-4" />
              <span>Support Desk</span>
            </Link>
          </nav>

          <div className="hidden md:flex items-center gap-3">

            <div className="relative">
              <button
                onClick={() => setRoleMenuOpen(!roleMenuOpen)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold shadow-sm transition-all ${currentRoleStyle.bg} ${currentRoleStyle.text} ${currentRoleStyle.border} hover:opacity-90`}
              >
                <RoleIcon className="w-3.5 h-3.5" />
                <span>Role: {currentRoleStyle.label}</span>
                <ChevronDown className="w-3 h-3 opacity-70" />
              </button>

              {roleMenuOpen && (
                <div
                  className="absolute right-0 mt-2 w-56 rounded-xl bg-white dark:bg-slate-900 shadow-xl border border-slate-200 dark:border-slate-800 py-1.5 z-50 animate-in fade-in slide-in-from-top-2"
                  onMouseLeave={() => setRoleMenuOpen(false)}
                >
                  <div className="px-3 py-1.5 text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                    Switch Active Sub-Portal
                  </div>
                  <button
                    onClick={() => handleRoleSwitch("donor")}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800 ${
                      role === "donor" ? "font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50/50 dark:bg-emerald-950/20" : "text-slate-700 dark:text-slate-300"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <Gift className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Donor Dashboard</span>
                    </span>
                    {role === "donor" && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
                  </button>
                  <button
                    onClick={() => handleRoleSwitch("ngo")}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800 ${
                      role === "ngo" ? "font-bold text-blue-600 dark:text-blue-400 bg-blue-50/50 dark:bg-blue-950/20" : "text-slate-700 dark:text-slate-300"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <Building2 className="w-3.5 h-3.5 text-blue-600" />
                      <span>NGO Rescue Center</span>
                    </span>
                    {role === "ngo" && <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />}
                  </button>
                  <button
                    onClick={() => handleRoleSwitch("driver")}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800 ${
                      role === "driver" ? "font-bold text-amber-600 dark:text-amber-400 bg-amber-50/50 dark:bg-amber-950/20" : "text-slate-700 dark:text-slate-300"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <Truck className="w-3.5 h-3.5 text-amber-600" />
                      <span>Driver Fleet Dispatch</span>
                    </span>
                    {role === "driver" && <CheckCircle2 className="w-3.5 h-3.5 text-amber-600" />}
                  </button>
                </div>
              )}
            </div>

            <Link
              href="/settings"
              className="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg dark:text-slate-400 dark:hover:text-white dark:hover:bg-slate-800 transition-colors"
              title="Settings"
            >
              <Settings className="w-4 h-4" />
            </Link>

            {isAuthenticated && user ? (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 pl-2 pr-1 py-1 rounded-full border border-slate-200 dark:border-slate-800 hover:border-slate-300 bg-white dark:bg-slate-900"
                >
                  <div className="w-7 h-7 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-xs uppercase overflow-hidden">
                    {user.avatarUrl ? (
                      <img src={user.avatarUrl} alt={user.name} className="w-full h-full object-cover" />
                    ) : (
                      user.name.charAt(0)
                    )}
                  </div>
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 max-w-[100px] truncate">
                    {user.name}
                  </span>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                </button>

                {userMenuOpen && (
                  <div
                    className="absolute right-0 mt-2 w-52 rounded-xl bg-white dark:bg-slate-900 shadow-xl border border-slate-200 dark:border-slate-800 py-1.5 z-50 animate-in fade-in slide-in-from-top-2"
                    onMouseLeave={() => setUserMenuOpen(false)}
                  >
                    <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800">
                      <p className="text-xs font-semibold text-slate-900 dark:text-white truncate">{user.name}</p>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">{user.email}</p>
                    </div>
                    <Link
                      href="/settings"
                      onClick={() => setUserMenuOpen(false)}
                      className="w-full text-left px-3 py-2 text-xs flex items-center gap-2 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                    >
                      <Settings className="w-3.5 h-3.5" />
                      <span>Account Settings</span>
                    </Link>
                    <Link
                      href="/help"
                      onClick={() => setUserMenuOpen(false)}
                      className="w-full text-left px-3 py-2 text-xs flex items-center gap-2 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                    >
                      <LifeBuoy className="w-3.5 h-3.5" />
                      <span>Get Help</span>
                    </Link>
                    <button
                      onClick={() => {
                        logout();
                        setUserMenuOpen(false);
                        router.push("/auth");
                      }}
                      className="w-full text-left px-3 py-2 text-xs flex items-center gap-2 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Link
                href="/auth"
                className="px-4 py-2 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm hover:shadow transition-all"
              >
                Sign In / Register
              </Link>
            )}
          </div>

          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 pt-2 pb-4 space-y-2">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
            <span className="text-xs font-semibold text-slate-500">Quick Portal Switch:</span>
            <div className="flex gap-1">
              {(["donor", "ngo", "driver"] as UserRole[]).map((r) => (
                <button
                  key={r}
                  onClick={() => {
                    handleRoleSwitch(r);
                    setMobileMenuOpen(false);
                  }}
                  className={`px-2.5 py-1 text-xs rounded-md font-semibold uppercase ${
                    role === r ? "bg-emerald-600 text-white" : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
          <Link
            href="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 text-sm font-medium rounded-lg text-slate-800 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            Overview
          </Link>
          <Link
            href={`/${role}`}
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 text-sm font-semibold rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300"
          >
            Current Dashboard ({role.toUpperCase()})
          </Link>
          <Link
            href="/directory"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 text-sm font-medium rounded-lg text-slate-800 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            NGO Directory
          </Link>
          <Link
            href="/help"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 text-sm font-medium rounded-lg text-slate-800 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            Help &amp; Support
          </Link>
          <Link
            href="/settings"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 text-sm font-medium rounded-lg text-slate-800 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            Account Settings
          </Link>
          <Link
            href="/auth"
            onClick={() => setMobileMenuOpen(false)}
            className="block w-full text-center px-4 py-2 mt-2 text-xs font-bold rounded-lg bg-emerald-600 text-white"
          >
            Auth Center
          </Link>
        </div>
      )}
    </header>
  );
}
