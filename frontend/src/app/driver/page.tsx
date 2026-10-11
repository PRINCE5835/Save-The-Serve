"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useApp } from "@/context/AppContext";
import { DeliveryMission } from "@/lib/types";
import {
  Truck,
  MapPin,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Navigation,
  ArrowRight,
  Upload,
  AlertCircle,
  Phone,
  Flame,
  Camera,
  Compass,
  Award,
} from "lucide-react";

export default function DriverDashboard() {
  const { user } = useAuth();
  const {
    deliveries,
    claimDeliveryMission,
    verifyPickupOTP,
    verifyDropoffOTP,
  } = useApp();

  const [activeDeliveryId, setActiveDeliveryId] = useState<string | null>(
    deliveries.find((d) => d.status === "claimed" || d.status === "picked_up")?.id || null
  );

  const [enteredPickupOtp, setEnteredPickupOtp] = useState("");
  const [enteredDropoffOtp, setEnteredDropoffOtp] = useState("");
  const [proofImageName, setProofImageName] = useState("");
  const [actionAlert, setActionAlert] = useState<{ type: "success" | "error"; text: string } | null>(
    null
  );

  const activeMission = deliveries.find((d) => d.id === activeDeliveryId);

  const handleClaim = (mission: DeliveryMission) => {
    claimDeliveryMission(
      mission.id,
      user?.id || "usr_driver_1",
      user?.name || "Alex Rivera"
    );
    setActiveDeliveryId(mission.id);
    setActionAlert({
      type: "success",
      text: `Mission "${mission.donation_title}" accepted! Route locked in. Proceed to Donor pickup location.`,
    });
  };

  const handleVerifyPickup = (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeDeliveryId) return;

    const res = verifyPickupOTP(activeDeliveryId, enteredPickupOtp);
    if (res.success) {
      setActionAlert({ type: "success", text: res.message });
      setEnteredPickupOtp("");
    } else {
      setActionAlert({ type: "error", text: res.message });
    }
  };

  const handleVerifyDropoff = (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeDeliveryId) return;

    const proofUrl = proofImageName
      ? `https://images.unsplash.com/photo-1593113598332-cd288d649433?w=400`
      : undefined;

    const res = verifyDropoffOTP(activeDeliveryId, enteredDropoffOtp, proofUrl);
    if (res.success) {
      setActionAlert({
        type: "success",
        text: "Delivery completed successfully! Handoff logged and driver credits updated.",
      });
      setEnteredDropoffOtp("");
      setProofImageName("");
    } else {
      setActionAlert({ type: "error", text: res.message });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

      <div className="rounded-3xl bg-gradient-to-r from-amber-950 via-slate-900 to-amber-900 text-white p-6 sm:p-8 shadow-xl border border-amber-800/40 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-400/30">
              <Truck className="w-3.5 h-3.5" />
              <span>Courier Fleet Command &bull; Real-Time Geo Dispatch</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
              Welcome, {user?.name || "Alex Rivera (Courier #408)"}
            </h1>
            <p className="text-xs sm:text-sm text-amber-200/80 max-w-xl">
              Execute critical surplus pickups and shelter deliveries with verified 6-digit OTP handshakes and proof photo capture.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/10 shrink-0 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500 text-slate-950 flex items-center justify-center font-black">
              <Navigation className="w-6 h-6" />
            </div>
            <div className="space-y-0.5 text-xs">
              <div className="font-bold text-white">Vehicle: {user?.vehicleType || "Refrigerated Cargo Van"}</div>
              <div className="text-amber-200">License: {user?.vehicleNumber || "STS-VAN-408"}</div>
              <div className="text-[11px] text-emerald-400 font-bold flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block" />
                <span>GPS Live Tracking Enabled</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {actionAlert && (
        <div
          className={`p-4 rounded-2xl border shadow-sm flex items-start justify-between gap-3 animate-in fade-in ${
            actionAlert.type === "success"
              ? "bg-emerald-50 dark:bg-emerald-950/80 border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200"
              : "bg-rose-50 dark:bg-rose-950/80 border-rose-300 dark:border-rose-800 text-rose-900 dark:text-rose-200"
          }`}
        >
          <div className="flex items-start gap-3">
            {actionAlert.type === "success" ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            )}
            <p className="text-xs sm:text-sm font-bold">{actionAlert.text}</p>
          </div>
          <button
            onClick={() => setActionAlert(null)}
            className="text-xs font-bold hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-lg p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Compass className="w-5 h-5 text-amber-600" />
                <h2 className="text-base sm:text-lg font-black text-slate-900 dark:text-white">
                  Active Delivery Mission Workflow
                </h2>
              </div>
              {activeMission && (
                <span
                  className={`text-[10px] font-black uppercase px-2.5 py-1 rounded-full ${
                    activeMission.status === "delivered"
                      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                      : activeMission.status === "picked_up"
                      ? "bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300"
                      : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                  }`}
                >
                  {activeMission.status}
                </span>
              )}
            </div>

            {activeMission ? (
              <div className="space-y-6 pt-5">

                <div>
                  <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                    {activeMission.donation_title}
                  </h3>
                  <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                    <span>Distance: <strong>{activeMission.distance_km} km</strong></span>
                    <span>&bull;</span>
                    <span>Est. Travel: <strong>{activeMission.est_minutes} mins</strong></span>
                    <span>&bull;</span>
                    <span className="capitalize font-semibold text-amber-600">{activeMission.category.replace("_", " ")}</span>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-900 text-white relative overflow-hidden space-y-4">
                  <div className="text-[11px] font-bold text-amber-400 flex items-center gap-1.5 uppercase tracking-wider">
                    <Navigation className="w-3.5 h-3.5" />
                    <span>Visual Route Timeline (PostGIS ST_Distance)</span>
                  </div>

                  <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-700">

                    <div className="relative">
                      <div
                        className={`absolute -left-6 top-1 w-4 h-4 rounded-full border-2 border-slate-900 flex items-center justify-center ${
                          activeMission.status !== "available"
                            ? "bg-emerald-500"
                            : "bg-amber-500"
                        }`}
                      />
                      <div className="space-y-0.5">
                        <span className="text-[10px] font-bold text-slate-400 uppercase">
                          Point A: Donor Pickup
                        </span>
                        <div className="text-xs font-bold">{activeMission.donor_name}</div>
                        <p className="text-[11px] text-slate-400">{activeMission.donor_address}</p>
                        <div className="flex items-center gap-1 text-[11px] text-emerald-400">
                          <Phone className="w-3 h-3" />
                          <span>{activeMission.donor_phone}</span>
                        </div>
                      </div>
                    </div>

                    <div className="relative">
                      <div
                        className={`absolute -left-6 top-1 w-4 h-4 rounded-full border-2 border-slate-900 flex items-center justify-center ${
                          activeMission.status === "delivered"
                            ? "bg-emerald-500"
                            : "bg-slate-600"
                        }`}
                      />
                      <div className="space-y-0.5">
                        <span className="text-[10px] font-bold text-slate-400 uppercase">
                          Point B: NGO Shelter Intake
                        </span>
                        <div className="text-xs font-bold">{activeMission.ngo_name}</div>
                        <p className="text-[11px] text-slate-400">{activeMission.ngo_address}</p>
                        <div className="flex items-center gap-1 text-[11px] text-emerald-400">
                          <Phone className="w-3 h-3" />
                          <span>{activeMission.ngo_phone}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {activeMission.status === "claimed" && (

                  <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-300 dark:border-amber-900/50 space-y-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-amber-900 dark:text-amber-200">
                      <ShieldCheck className="w-4 h-4 text-amber-600" />
                      <span>Stage 1: Verify Donor Pickup Handshake</span>
                    </div>
                    <p className="text-xs text-amber-800 dark:text-amber-300">
                      Ask the donor for their 6-digit `pickup_otp` before loading items into your vehicle.
                    </p>

                    <form onSubmit={handleVerifyPickup} className="space-y-3">
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1">
                          Enter 6-Digit Donor OTP (Demo Code: <span className="font-mono text-emerald-600">{activeMission.pickup_otp}</span>)
                        </label>
                        <input
                          type="text"
                          maxLength={6}
                          required
                          value={enteredPickupOtp}
                          onChange={(e) => setEnteredPickupOtp(e.target.value)}
                          placeholder="e.g. 482910"
                          className="w-full text-center text-lg font-mono font-bold tracking-widest py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                        />
                      </div>
                      <button
                        type="submit"
                        className="w-full py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs shadow-md"
                      >
                        Verify Pickup &amp; Start Transit
                      </button>
                    </form>
                  </div>
                )}

                {activeMission.status === "picked_up" && (

                  <div className="p-4 rounded-2xl bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-300 dark:border-indigo-900/50 space-y-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-indigo-900 dark:text-indigo-200">
                      <Camera className="w-4 h-4 text-indigo-600" />
                      <span>Stage 2: Verify NGO Drop-Off &amp; Handoff Photo Proof</span>
                    </div>
                    <p className="text-xs text-indigo-800 dark:text-indigo-300">
                      Obtain the NGO intake officer's 6-digit `dropoff_otp` and upload an image of the received goods at the shelter.
                    </p>

                    <form onSubmit={handleVerifyDropoff} className="space-y-3">
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1">
                          Enter 6-Digit NGO Dropoff OTP (Demo Code: <span className="font-mono text-indigo-600">{activeMission.dropoff_otp}</span>)
                        </label>
                        <input
                          type="text"
                          maxLength={6}
                          required
                          value={enteredDropoffOtp}
                          onChange={(e) => setEnteredDropoffOtp(e.target.value)}
                          placeholder="e.g. 739102"
                          className="w-full text-center text-lg font-mono font-bold tracking-widest py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                        />
                      </div>

                      {/* Photo Proof Upload Simulation */}
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1">
                          Delivery Confirmation Proof Photo
                        </label>
                        <div className="flex items-center gap-2">
                          <label className="cursor-pointer px-3 py-2 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-900 flex items-center gap-1.5">
                            <Upload className="w-3.5 h-3.5 text-indigo-600" />
                            <span>{proofImageName || "Attach Handoff Photo"}</span>
                            <input
                              type="file"
                              accept="image/*"
                              className="hidden"
                              onChange={(e) => {
                                if (e.target.files?.[0]) {
                                  setProofImageName(e.target.files[0].name);
                                }
                              }}
                            />
                          </label>
                          {proofImageName && (
                            <span className="text-[11px] text-emerald-600 font-bold flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Ready</span>
                            </span>
                          )}
                        </div>
                      </div>

                      <button
                        type="submit"
                        className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md"
                      >
                        Complete Delivery &amp; Log Handoff
                      </button>
                    </form>
                  </div>
                )}

                {activeMission.status === "delivered" && (
                  <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 text-xs space-y-2 text-center">
                    <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                    <h4 className="font-extrabold text-sm text-emerald-900 dark:text-emerald-200">
                      Mission Completed Successfully!
                    </h4>
                    <p className="text-emerald-700 dark:text-emerald-400 text-xs">
                      Both 6-digit OTP codes and proof image verified. +50 Volunteer ESG Impact Points awarded to your driver profile.
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-16 text-slate-400 text-xs space-y-2">
                <Navigation className="w-8 h-8 mx-auto text-slate-300" />
                <p>No active delivery mission claimed.</p>
                <p className="text-[11px]">Select a mission from the available runs on the right to start.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Available Delivery Runs List */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Truck className="w-4 h-4 text-amber-600" />
                <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                  Available Delivery Runs
                </h3>
              </div>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                {deliveries.filter((d) => d.status === "available").length} Open
              </span>
            </div>

            <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
              {deliveries.map((m) => {
                const isSelected = activeDeliveryId === m.id;
                const isCritical = m.urgency === "critical";

                return (
                  <div
                    key={m.id}
                    className={`p-4 rounded-2xl border transition-all space-y-3 ${
                      isSelected
                        ? "border-amber-500 bg-amber-50/30 dark:bg-amber-950/20"
                        : "border-slate-200 dark:border-slate-800 hover:border-slate-300 bg-slate-50/50 dark:bg-slate-800/30"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <span
                          className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${
                            isCritical
                              ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                              : "bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-300"
                          }`}
                        >
                          {m.urgency} Urgency
                        </span>
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white line-clamp-1">
                          {m.donation_title}
                        </h4>
                      </div>
                      <span className="text-xs font-mono font-bold text-slate-700 dark:text-slate-300">
                        {m.distance_km} km
                      </span>
                    </div>

                    <div className="space-y-1 text-[11px] text-slate-600 dark:text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        <span className="line-clamp-1">From: {m.donor_address}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                        <span className="line-clamp-1">To: {m.ngo_name}</span>
                      </div>
                    </div>

                    <div className="pt-1 flex items-center justify-between">
                      <span className="text-[11px] text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>~{m.est_minutes} mins</span>
                      </span>

                      {m.status === "available" ? (
                        <button
                          type="button"
                          onClick={() => handleClaim(m)}
                          className="px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs shadow-sm flex items-center gap-1.5"
                        >
                          <span>Claim Task</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setActiveDeliveryId(m.id)}
                          className="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-bold text-slate-700 dark:text-slate-300"
                        >
                          View Mission
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
