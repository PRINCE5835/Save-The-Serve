"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useApp } from "@/context/AppContext";
import {
  HeartHandshake,
  Gift,
  Building2,
  Truck,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Leaf,
  Users,
  Compass,
  Clock,
  QrCode,
  Flame,
  ChevronRight,
  MapPin,
  CheckCircle2,
} from "lucide-react";

export default function HomePage() {
  const { role } = useAuth();
  const { esgStats, donations, ngos } = useApp();

  return (
    <div className="flex flex-col min-h-screen">

      <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-900 text-white">

        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/15 rounded-full blur-[140px] pointer-events-none" />
        <div className="absolute top-1/3 left-1/4 w-[350px] h-[350px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center space-y-6">

          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-inner">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Save The Serve (S.T.S) &bull; Automated Perishable Watchdog Online</span>
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white max-w-4xl mx-auto leading-tight">
            Zero-Waste Surplus Rescue. <br />
            <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
              Dispatched at PostGIS Speed.
            </span>
          </h1>

          <p className="text-sm sm:text-base lg:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Connecting commercial food surplus, clothing, and essential medical supplies to nearby verified shelters with dynamic urgency escalation and secure 6-digit OTP handshakes.
          </p>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/auth"
              className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs sm:text-sm shadow-xl shadow-emerald-500/20 hover:scale-[1.02] transition-all flex items-center justify-center gap-2"
            >
              <span>Get Started &bull; Unified Auth</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              href={`/${role}`}
              className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs sm:text-sm border border-white/20 transition-all flex items-center justify-center gap-2"
            >
              <span>Enter Active {role.toUpperCase()} Portal</span>
              <ChevronRight className="w-4 h-4 text-emerald-400" />
            </Link>

            <Link
              href="/directory"
              className="w-full sm:w-auto px-6 py-3.5 rounded-2xl bg-transparent hover:bg-white/5 text-slate-300 hover:text-white font-bold text-xs sm:text-sm transition-all flex items-center justify-center gap-2"
            >
              <Compass className="w-4 h-4" />
              <span>Explore NGO Directory</span>
            </Link>
          </div>

          <div className="pt-12 max-w-5xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 text-left">
              <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                <Leaf className="w-3.5 h-3.5" />
                <span>CO₂ Prevented</span>
              </span>
              <div className="text-2xl font-black font-mono mt-1 text-white">
                {esgStats.co2KgPrevented.toLocaleString()} kg
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">Scope 3 diverted</p>
            </div>

            <div className="p-4 rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 text-left">
              <span className="text-xs font-semibold text-teal-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Meals Rescued</span>
              </span>
              <div className="text-2xl font-black font-mono mt-1 text-white">
                {esgStats.mealsSaved.toLocaleString()}
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">Hot nutritious meals</p>
            </div>

            <div className="p-4 rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 text-left">
              <span className="text-xs font-semibold text-cyan-400 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5" />
                <span>Active Shelters</span>
              </span>
              <div className="text-2xl font-black font-mono mt-1 text-white">
                {ngos.length} Verified
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">Within urban radius</p>
            </div>

            <div className="p-4 rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 text-left">
              <span className="text-xs font-semibold text-amber-400 flex items-center gap-1.5">
                <Truck className="w-3.5 h-3.5" />
                <span>Fleet Couriers</span>
              </span>
              <div className="text-2xl font-black font-mono mt-1 text-white">
                {esgStats.activeDrivers} Ready
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">Average dispatch: 14 mins</p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 sm:py-24 bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <span className="text-xs font-black uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
              Role-Gated Ecosystem
            </span>
            <h2 className="text-2xl sm:text-4xl font-black text-slate-900 dark:text-white tracking-tight">
              Three Dedicated Command Centers
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              Select your role to access tailored dashboards, workflows, and automated coordination tools.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

            <div className="bg-white dark:bg-slate-950 rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-emerald-500/50 transition-all flex flex-col justify-between group">
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-300 flex items-center justify-center font-bold group-hover:scale-110 transition-transform">
                  <Gift className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-black text-slate-900 dark:text-white">
                    Donor Dashboard
                  </h3>
                  <span className="text-[11px] font-bold text-emerald-600 uppercase tracking-wider">
                    Surplus Providers &amp; Sponsors
                  </span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Multi-step donation wizard supporting Cooked Food, Clothes, Blankets, Medical items, and Earmarked Monetary sponsorship with live ESG impact reports.
                </p>
                <ul className="space-y-2 text-xs font-medium text-slate-700 dark:text-slate-300 pt-2">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Perishable expiry watchdog timer</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Scope 3 carbon reduction metrics</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Unique 6-digit pickup OTP verification</span>
                  </li>
                </ul>
              </div>

              <div className="pt-6">
                <Link
                  href="/donor"
                  className="w-full py-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 hover:bg-emerald-600 hover:text-white text-emerald-700 dark:text-emerald-300 font-bold text-xs flex items-center justify-center gap-1.5 transition-all"
                >
                  <span>Launch Donor Hub</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-950 rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-blue-500/50 transition-all flex flex-col justify-between group">
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-950/80 text-blue-600 dark:text-blue-300 flex items-center justify-center font-bold group-hover:scale-110 transition-transform">
                  <Building2 className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-black text-slate-900 dark:text-white">
                    NGO Command Center
                  </h3>
                  <span className="text-[11px] font-bold text-blue-600 uppercase tracking-wider">
                    Shelters &amp; Community Kitchens
                  </span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Real-time incoming rescue radar feed with distance calculations, 1-click claim with 15-minute reservation hold, and earmarked supply wishlists.
                </p>
                <ul className="space-y-2 text-xs font-medium text-slate-700 dark:text-slate-300 pt-2">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span>Real-time proximity feed</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span>15-Minute claim reservation lock</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span>Operating capacity toggle (Active / Paused)</span>
                  </li>
                </ul>
              </div>

              <div className="pt-6">
                <Link
                  href="/ngo"
                  className="w-full py-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/50 hover:bg-blue-600 hover:text-white text-blue-700 dark:text-blue-300 font-bold text-xs flex items-center justify-center gap-1.5 transition-all"
                >
                  <span>Launch NGO Command</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-950 rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-amber-500/50 transition-all flex flex-col justify-between group">
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-950/80 text-amber-600 dark:text-amber-300 flex items-center justify-center font-bold group-hover:scale-110 transition-transform">
                  <Truck className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-black text-slate-900 dark:text-white">
                    Driver Fleet Dispatch
                  </h3>
                  <span className="text-[11px] font-bold text-amber-600 uppercase tracking-wider">
                    Volunteer Logistics &amp; Couriers
                  </span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Interactive mission cards with visual route maps, estimated drive times, and cryptographic 6-digit OTP dual-handshake verification + photo proof.
                </p>
                <ul className="space-y-2 text-xs font-medium text-slate-700 dark:text-slate-300 pt-2">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                    <span>Visual Donor &rarr; NGO route progression</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                    <span>Donor 6-digit `pickup_otp` verification</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                    <span>NGO `dropoff_otp` + proof photo upload</span>
                  </li>
                </ul>
              </div>

              <div className="pt-6">
                <Link
                  href="/driver"
                  className="w-full py-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/50 hover:bg-amber-600 hover:text-white text-amber-700 dark:text-amber-300 font-bold text-xs flex items-center justify-center gap-1.5 transition-all"
                >
                  <span>Launch Driver Fleet</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 sm:py-24 bg-white dark:bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <span className="text-xs font-black uppercase tracking-wider text-emerald-600">
              End-to-End Handshake Architecture
            </span>
            <h2 className="text-2xl sm:text-4xl font-black text-slate-900 dark:text-white tracking-tight">
              From Kitchen Dock to Shelter Table
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3">
              <div className="w-8 h-8 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-black text-xs">
                01
              </div>
              <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                Surplus Registered
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Donor enters meal trays or goods with preparation and expiry timestamps. Secret `pickup_otp` is generated.
              </p>
            </div>

            <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3">
              <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black text-xs">
                02
              </div>
              <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                PostGIS Matching
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Matching engine runs ST_DWithin radius search. Food with &lt; 2h expiry is escalated to Critical Urgency automatically.
              </p>
            </div>

            <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3">
              <div className="w-8 h-8 rounded-xl bg-amber-600 text-white flex items-center justify-center font-black text-xs">
                03
              </div>
              <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                OTP Pickup Handshake
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Courier claims task and travels to donor. Donor provides 6-digit OTP to verify courier identity before handover.
              </p>
            </div>

            <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3">
              <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-black text-xs">
                04
              </div>
              <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                Dropoff &amp; Proof Log
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Shelter verifies dropoff OTP + photo capture. Community nourished, zero waste achieved, and ESG credits minted.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-700 py-16 text-white text-center">
        <div className="max-w-4xl mx-auto px-4 space-y-6">
          <h2 className="text-2xl sm:text-4xl font-black tracking-tight">
            Ready to Save The Serve in your City?
          </h2>
          <p className="text-xs sm:text-sm text-emerald-100 max-w-xl mx-auto leading-relaxed">
            Whether you are a commercial kitchen with hot catering trays, a registered shelter needing supplies, or a volunteer driver with a vehicle—join our network.
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <Link
              href="/auth"
              className="px-8 py-3.5 rounded-2xl bg-slate-950 hover:bg-slate-900 text-white font-extrabold text-xs shadow-xl transition-all"
            >
              Sign Up or Enter Unified Portal
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
