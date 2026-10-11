"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import {
  Settings,
  User,
  Bell,
  Lock,
  MapPin,
  CheckCircle2,
  ShieldCheck,
  Building2,
  Truck,
  Sparkles,
} from "lucide-react";

export default function SettingsPage() {
  const { user, updateProfile } = useAuth();

  const [name, setName] = useState(user?.name || "");
  const [phone, setPhone] = useState(user?.phone || "+1 (555) 234-8901");
  const [address, setAddress] = useState(user?.address || "Downtown Kitchen Dock, SF");
  const [orgName, setOrgName] = useState(user?.organizationName || "");
  const [vehicle, setVehicle] = useState(user?.vehicleType || "");

  const [urgentSurplusAlerts, setUrgentSurplusAlerts] = useState(true);
  const [deliveryUpdates, setDeliveryUpdates] = useState(true);
  const [esgMilestones, setEsgMilestones] = useState(true);
  const [alertRadiusKm, setAlertRadiusKm] = useState(25);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [saveBanner, setSaveBanner] = useState<string | null>(null);

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile({
      name,
      phone,
      address,
      organizationName: orgName || undefined,
      vehicleType: vehicle || undefined,
    });
    setSaveBanner("Profile and contact details saved successfully!");
  };

  const handleSavePassword = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      alert("New passwords do not match.");
      return;
    }
    setSaveBanner("Password updated successfully.");
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 mb-2">
          <Settings className="w-3.5 h-3.5" />
          <span>Account &bull; Preferences</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">
          Account Settings &amp; Notifications
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Manage your role credentials, 6-digit handshake verification phone number, and surplus alert preferences.
        </p>
      </div>

      {saveBanner && (
        <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/80 border border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200 text-xs sm:text-sm font-bold flex items-center justify-between gap-3 animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{saveBanner}</span>
          </div>
          <button onClick={() => setSaveBanner(null)} className="text-emerald-700 font-bold">
            Dismiss
          </button>
        </div>
      )}

      <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 space-y-6">
        <div className="flex items-center gap-2 pb-4 border-b border-slate-100 dark:border-slate-800">
          <User className="w-5 h-5 text-emerald-600" />
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            Profile Details &amp; Operational Info
          </h2>
        </div>

        <form onSubmit={handleSaveProfile} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                Full Name / Contact Name
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                SMS Handshake Phone Number
              </label>
              <input
                type="tel"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
              Primary Physical Address / Dock Location
            </label>
            <input
              type="text"
              required
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          {user?.role === "ngo" && (
            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                Registered NGO Name
              </label>
              <input
                type="text"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
              />
            </div>
          )}

          {user?.role === "driver" && (
            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                Vehicle Type &amp; Cargo Specs
              </label>
              <input
                type="text"
                value={vehicle}
                onChange={(e) => setVehicle(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
              />
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold shadow hover:opacity-90 transition-all"
            >
              Save Profile Changes
            </button>
          </div>
        </form>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 space-y-6">
        <div className="flex items-center gap-2 pb-4 border-b border-slate-100 dark:border-slate-800">
          <Bell className="w-5 h-5 text-indigo-600" />
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            Push Notifications &amp; Proximity Alerts
          </h2>
        </div>

        <div className="space-y-4 text-xs">
          <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
            <div>
              <div className="font-bold text-slate-900 dark:text-white">
                Urgent Perishable Surplus Escalations (&lt; 2h Expiry)
              </div>
              <p className="text-slate-500 dark:text-slate-400 text-[11px]">
                Instant high-priority notification when hot cooked food has under 2 hours remaining in your area.
              </p>
            </div>
            <input
              type="checkbox"
              checked={urgentSurplusAlerts}
              onChange={(e) => setUrgentSurplusAlerts(e.target.checked)}
              className="accent-indigo-600 rounded w-4 h-4"
            />
          </div>

          <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
            <div>
              <div className="font-bold text-slate-900 dark:text-white">
                Delivery Dispatch &amp; Handshake Updates
              </div>
              <p className="text-slate-500 dark:text-slate-400 text-[11px]">
                Receive alerts when your donation is claimed, picked up, or delivered with 6-digit OTP verification.
              </p>
            </div>
            <input
              type="checkbox"
              checked={deliveryUpdates}
              onChange={(e) => setDeliveryUpdates(e.target.checked)}
              className="accent-indigo-600 rounded w-4 h-4"
            />
          </div>

          <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
            <div>
              <div className="font-bold text-slate-900 dark:text-white">
                Monthly ESG Impact Milestones &amp; Certificates
              </div>
              <p className="text-slate-500 dark:text-slate-400 text-[11px]">
                Summary of total meals rescued, CO₂ emissions prevented, and Scope 3 reports.
              </p>
            </div>
            <input
              type="checkbox"
              checked={esgMilestones}
              onChange={(e) => setEsgMilestones(e.target.checked)}
              className="accent-indigo-600 rounded w-4 h-4"
            />
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="flex items-center justify-between font-bold">
              <span>Geospatial Alert Radius:</span>
              <span className="font-mono text-indigo-600 dark:text-indigo-400">{alertRadiusKm} km</span>
            </div>
            <input
              type="range"
              min={5}
              max={50}
              value={alertRadiusKm}
              onChange={(e) => setAlertRadiusKm(Number(e.target.value))}
              className="w-full accent-indigo-600 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
            />
            <p className="text-[11px] text-slate-400">
              Only notify me about surplus events and rescue missions within this distance.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 space-y-6">
        <div className="flex items-center gap-2 pb-4 border-b border-slate-100 dark:border-slate-800">
          <Lock className="w-5 h-5 text-rose-600" />
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            Security &amp; Password Update
          </h2>
        </div>

        <form onSubmit={handleSavePassword} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
              Current Password
            </label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                New Password
              </label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                Confirm New Password
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
              />
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold shadow-md transition-all"
            >
              Update Password
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
