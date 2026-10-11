"use client";

import React, { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { UserRole } from "@/lib/types";
import {
  Gift,
  Building2,
  Truck,
  Lock,
  Mail,
  User,
  Phone,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  Eye,
  EyeOff,
  CheckCircle2,
} from "lucide-react";

function AuthContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialMode = searchParams.get("mode") === "signup" ? "signup" : "signin";
  const initialRole = (searchParams.get("role") as UserRole) || "donor";

  const { login, signup, switchRole } = useAuth();

  const [mode, setMode] = useState<"signin" | "signup">(initialMode);
  const [selectedRole, setSelectedRole] = useState<UserRole>(initialRole);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [successNotice, setSuccessNotice] = useState("");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [vehicleType, setVehicleType] = useState("");

  const handleQuickDemo = (role: UserRole) => {
    setSelectedRole(role);
    switchRole(role);
    setSuccessNotice(`Signed in as demo ${role.toUpperCase()}! Redirecting...`);
    setTimeout(() => {
      router.push(`/${role}`);
    }, 600);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (mode === "signin") {
        await login(email || `${selectedRole}@example.com`, selectedRole, password);
      } else {
        await signup({
          name: name || `${selectedRole.toUpperCase()} User`,
          email: email || `${selectedRole}@example.com`,
          role: selectedRole,
          phone: phone || "+1 (555) 345-6789",
          organizationName: selectedRole === "ngo" ? organizationName || "Metropolitan Food Aid" : undefined,
          vehicleType: selectedRole === "driver" ? vehicleType || "Refrigerated Cargo Van" : undefined,
        });
      }

      setSuccessNotice(`Authentication successful! Entering ${selectedRole.toUpperCase()} portal...`);
      setTimeout(() => {
        router.push(`/${selectedRole}`);
      }, 700);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const roleDetails = {
    donor: {
      title: "Surplus Food & Goods Donor",
      description: "Hotels, caterers, corporations, or individuals donating meals, clothing, blankets, and earmarked funds.",
      icon: Gift,
      color: "emerald",
      badge: "Zero-Waste Impact",
    },
    ngo: {
      title: "Frontline NGO & Shelter",
      description: "Charity kitchens, shelters, and relief orgs claiming incoming surplus within custom radius.",
      icon: Building2,
      color: "blue",
      badge: "Verified Intake",
    },
    driver: {
      title: "Rescue Courier & Driver",
      description: "Volunteer drivers and delivery fleets executing pickup & drop-off with 6-digit OTP verification.",
      icon: Truck,
      color: "amber",
      badge: "Geo-Dispatched",
    },
  };

  const activeRoleInfo = roleDetails[selectedRole];
  const RoleIcon = activeRoleInfo.icon;

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 sm:p-6 lg:p-8 relative overflow-hidden bg-gradient-to-b from-slate-50 via-slate-100 to-slate-200 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">

      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-emerald-500/10 dark:bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-xl z-10">

        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 mb-3 shadow-sm">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Unified Role-Gated Access</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">
            {mode === "signin" ? "Welcome back to Save The Serve" : "Join the Rescue Network"}
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1 max-w-md mx-auto">
            Select your role to access your personalized command center and geospatial feed.
          </p>
        </div>

        <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md rounded-2xl border border-slate-200/90 dark:border-slate-800 p-4 mb-6 shadow-sm">
          <div className="flex items-center justify-between text-xs font-bold text-slate-500 dark:text-slate-400 mb-2">
            <span>Instant Demo Sign-In (Skip Typing):</span>
            <span className="text-[11px] text-emerald-600 font-medium">1-Click Role Access</span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleQuickDemo("donor")}
              className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 hover:bg-emerald-100 dark:hover:bg-emerald-900 transition-all shadow-sm"
            >
              <Gift className="w-3.5 h-3.5" />
              <span>Demo Donor</span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickDemo("ngo")}
              className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-blue-50 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900 transition-all shadow-sm"
            >
              <Building2 className="w-3.5 h-3.5" />
              <span>Demo NGO</span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickDemo("driver")}
              className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-amber-50 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800 hover:bg-amber-100 dark:hover:bg-amber-900 transition-all shadow-sm"
            >
              <Truck className="w-3.5 h-3.5" />
              <span>Demo Driver</span>
            </button>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl overflow-hidden">

          <div className="p-3 bg-slate-100/70 dark:bg-slate-950/50 border-b border-slate-200 dark:border-slate-800">
            <div className="grid grid-cols-3 gap-2">
              {(["donor", "ngo", "driver"] as UserRole[]).map((r) => {
                const isSelected = selectedRole === r;
                const info = roleDetails[r];
                const Icon = info.icon;
                return (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setSelectedRole(r)}
                    className={`flex flex-col items-center justify-center py-2.5 px-2 rounded-xl text-xs font-bold transition-all relative ${
                      isSelected
                        ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-md border border-slate-200/80 dark:border-slate-700"
                        : "text-slate-500 dark:text-slate-400 hover:text-slate-800 hover:bg-white/40 dark:hover:bg-slate-800/40"
                    }`}
                  >
                    <Icon
                      className={`w-4 h-4 mb-1 ${
                        isSelected
                          ? r === "donor"
                            ? "text-emerald-600"
                            : r === "ngo"
                            ? "text-blue-600"
                            : "text-amber-600"
                          : "text-slate-400"
                      }`}
                    />
                    <span className="capitalize">{r}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex border-b border-slate-200 dark:border-slate-800 px-6 pt-4">
            <button
              type="button"
              onClick={() => setMode("signin")}
              className={`pb-3 text-xs sm:text-sm font-bold border-b-2 mr-6 transition-colors ${
                mode === "signin"
                  ? "border-emerald-600 text-emerald-600 dark:text-emerald-400"
                  : "border-transparent text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
              }`}
            >
              Sign In to Account
            </button>
            <button
              type="button"
              onClick={() => setMode("signup")}
              className={`pb-3 text-xs sm:text-sm font-bold border-b-2 transition-colors ${
                mode === "signup"
                  ? "border-emerald-600 text-emerald-600 dark:text-emerald-400"
                  : "border-transparent text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
              }`}
            >
              Create New Account
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-4">

            <div className="flex items-start gap-3 p-3 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-xs">
              <div
                className={`p-2 rounded-xl ${
                  selectedRole === "donor"
                    ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                    : selectedRole === "ngo"
                    ? "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300"
                    : "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
                }`}
              >
                <RoleIcon className="w-5 h-5" />
              </div>
              <div>
                <div className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>{activeRoleInfo.title}</span>
                  <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                    {activeRoleInfo.badge}
                  </span>
                </div>
                <p className="text-slate-500 dark:text-slate-400 text-[11px] mt-0.5">
                  {activeRoleInfo.description}
                </p>
              </div>
            </div>

            {successNotice && (
              <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/80 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{successNotice}</span>
              </div>
            )}

            {mode === "signup" && (
              <>
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Full Name / Contact Person
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="text"
                      required
                      placeholder={selectedRole === "ngo" ? "Rev. Marcus Vance" : "Sarah Jenkins"}
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>

                {selectedRole === "ngo" && (
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Registered NGO / Charity Name &amp; EIN
                    </label>
                    <div className="relative">
                      <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                      <input
                        type="text"
                        required
                        placeholder="Hope Harvest Relief Center (EIN-84-93821)"
                        value={organizationName}
                        onChange={(e) => setOrganizationName(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                )}

                {selectedRole === "driver" && (
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Vehicle Type &amp; Transport Capability
                    </label>
                    <div className="relative">
                      <Truck className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                      <input
                        type="text"
                        required
                        placeholder="e.g. Refrigerated Van, Cargo SUV, Scooter"
                        value={vehicleType}
                        onChange={(e) => setVehicleType(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Phone Number (for SMS OTP Handshakes)
                  </label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="tel"
                      required
                      placeholder="+1 (555) 234-8901"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  placeholder={
                    selectedRole === "donor"
                      ? "sarah.jenkins@grandhotel.com"
                      : selectedRole === "ngo"
                      ? "marcus@hopeharvest.org"
                      : "alex.driver@sts-couriers.net"
                  }
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
                  Password
                </label>
                {mode === "signin" && (
                  <span className="text-[11px] text-emerald-600 hover:underline cursor-pointer">
                    Forgot password?
                  </span>
                )}
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-10 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold text-white shadow-md flex items-center justify-center gap-2 transition-all ${
                selectedRole === "donor"
                  ? "bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/20"
                  : selectedRole === "ngo"
                  ? "bg-blue-600 hover:bg-blue-700 shadow-blue-500/20"
                  : "bg-amber-600 hover:bg-amber-700 shadow-amber-500/20"
              }`}
            >
              <span>{loading ? "Authenticating..." : mode === "signin" ? `Sign In as ${selectedRole.toUpperCase()}` : `Create ${selectedRole.toUpperCase()} Account`}</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <div className="pt-2 text-center flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>TLS 1.3 Encrypted &bull; 6-Digit Verification Handshake Ready</span>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function AuthPage() {
  return (
    <React.Suspense
      fallback={
        <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center text-xs font-bold text-slate-500">
          Loading S.T.S authentication portal...
        </div>
      }
    >
      <AuthContent />
    </React.Suspense>
  );
}
