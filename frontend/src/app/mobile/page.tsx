"use client";

import React, { useState, useEffect } from "react";
import {
  Smartphone,
  Gift,
  Building2,
  Truck,
  Camera,
  MapPin,
  Phone,
  Navigation,
  QrCode,
  DollarSign,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ShieldCheck,
  Flame,
  ChevronRight,
  Layers,
  HeartHandshake,
  Wifi,
  Battery,
  Share2,
} from "lucide-react";

type MobileRole = "donor" | "ngo" | "driver";

export default function MobileAppEmulatorPage() {
  const [role, setRole] = useState<MobileRole>("donor");
  const [currentTab, setCurrentTab] = useState<string>("rapid_donate");
  const [showOtpModal, setShowOtpModal] = useState<boolean>(false);
  const [showSplash, setShowSplash] = useState<boolean>(false);
  const [deviceModel, setDeviceModel] = useState<"iphone" | "pixel">("iphone");

  const [cameraSnapped, setCameraSnapped] = useState<boolean>(false);
  const [donationCategory, setDonationCategory] = useState<string>("cooked_food");
  const [donorDonationSuccess, setDonorDonationSuccess] = useState<string | null>(null);

  const [unitCount, setUnitCount] = useState<number>(50);
  const [unitCost, setUnitCost] = useState<number>(15);
  const [payNotice, setPayNotice] = useState<string | null>(null);

  const [claimedTimers, setClaimedTimers] = useState<Record<string, number>>({});
  const [ngoClaimAlert, setNgoClaimAlert] = useState<string | null>(null);
  const [ngoCapacityActive, setNgoCapacityActive] = useState<boolean>(true);

  const [enteredPickupOtp, setEnteredPickupOtp] = useState<string>("");
  const [enteredDropoffOtp, setEnteredDropoffOtp] = useState<string>("");
  const [otpVerifyResult, setOtpVerifyResult] = useState<string | null>(null);
  const [driverMissionStatus, setDriverMissionStatus] = useState<"claimed" | "picked_up" | "delivered">("claimed");
  const [maneuverStep, setManeuverStep] = useState<number>(0);

  const [currentTime, setCurrentTime] = useState<string>("9:41");

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(
        `${now.getHours()}:${now.getMinutes() < 10 ? "0" : ""}${now.getMinutes()}`
      );
    };
    updateClock();
    const timer = setInterval(updateClock, 30000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setClaimedTimers((prev) => {
        const next: Record<string, number> = {};
        for (const [id, sec] of Object.entries(prev)) {
          if (sec > 1) next[id] = sec - 1;
        }
        return next;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleRoleChange = (newRole: MobileRole) => {
    setRole(newRole);
    if (newRole === "donor") setCurrentTab("rapid_donate");
    if (newRole === "ngo") setCurrentTab("alerts_feed");
    if (newRole === "driver") setCurrentTab("route_nav");
  };

  const maneuvers = [
    { text: "In 350m, turn right onto 7th St", dist: "350 m" },
    { text: "Continue straight on Folsom St for 1.2 km", dist: "1.2 km" },
    { text: "Turn left onto Riverfront Blvd at signal", dist: "600 m" },
    { text: "Arriving at NGO Intake Dock B on the right", dist: "50 m" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 mb-2">
            <Smartphone className="w-3.5 h-3.5" />
            <span>Cross-Platform React Native &bull; Live Mobile Simulator</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">
            Save The Serve (S.T.S) Mobile Application
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1 max-w-2xl">
            Experience the cross-platform mobile app in real time. The bottom navigation bar, camera modules, and workflows automatically adapt based on your active role.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-white dark:bg-slate-900 p-2 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm shrink-0">
          <span className="text-xs font-bold text-slate-500 pl-2">Role:</span>
          <button
            onClick={() => handleRoleChange("donor")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              role === "donor"
                ? "bg-emerald-600 text-white shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <Gift className="w-3.5 h-3.5" />
            <span>Donor</span>
          </button>
          <button
            onClick={() => handleRoleChange("ngo")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              role === "ngo"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>NGO</span>
          </button>
          <button
            onClick={() => handleRoleChange("driver")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              role === "driver"
                ? "bg-amber-600 text-white shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <Truck className="w-3.5 h-3.5" />
            <span>Driver</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

        <div className="lg:col-span-6 flex justify-center">
          <div className="w-[390px] h-[810px] rounded-[52px] bg-slate-950 p-4 border-[6px] border-slate-800 shadow-2xl relative overflow-hidden flex flex-col justify-between select-none">

            <div className="absolute top-3 left-1/2 -translate-x-1/2 w-28 h-6 bg-black rounded-full z-50 flex items-center justify-center">
              <div className="w-2.5 h-2.5 rounded-full bg-slate-900 border border-slate-800" />
            </div>

            <div className="pt-2 px-6 flex items-center justify-between text-white text-[12px] font-bold z-40">
              <span>{currentTime}</span>
              <div className="flex items-center gap-1.5 opacity-90">
                <Wifi className="w-3.5 h-3.5" />
                <span className="text-[10px]">5G</span>
                <Battery className="w-4 h-4" />
              </div>
            </div>

            <div className="px-4 py-2 border-b border-slate-800/80 flex items-center justify-between z-30">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-black text-xs">
                  ♥
                </div>
                <div>
                  <span className="text-xs font-extrabold text-white">S.T.S Mobile</span>
                  <div className="flex items-center gap-1 text-[9px] text-emerald-400 font-semibold">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                    <span>Watchdog Active</span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleRoleChange(role === "donor" ? "ngo" : role === "ngo" ? "driver" : "donor")}
                className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase border ${
                  role === "donor"
                    ? "bg-emerald-950/80 text-emerald-300 border-emerald-700"
                    : role === "ngo"
                    ? "bg-blue-950/80 text-blue-300 border-blue-700"
                    : "bg-amber-950/80 text-amber-300 border-amber-700"
                }`}
              >
                {role} ⇄
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 text-white text-xs">

              {role === "donor" && currentTab === "rapid_donate" && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-sm text-white">Rapid Surplus Donation</span>
                    <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded-full border border-emerald-800">
                      Step 1 of 2
                    </span>
                  </div>

                  <div className="bg-slate-900 rounded-2xl p-3 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-[11px] font-bold text-slate-300">
                      <span>Live Camera Viewfinder</span>
                      <span className="text-[9px] text-emerald-400">AI Safety Check</span>
                    </div>

                    {cameraSnapped ? (
                      <div className="relative rounded-xl overflow-hidden h-36 bg-slate-800">
                        <img
                          src="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&q=80"
                          alt="Surplus Food Preview"
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute bottom-2 left-2 bg-slate-950/80 px-2 py-1 rounded text-[9px] font-mono text-emerald-400">
                          {currentTime} &bull; 37.7749, -122.4194 &bull; FOOD-SAFE
                        </div>
                        <button
                          onClick={() => setCameraSnapped(false)}
                          className="absolute top-2 right-2 bg-black/70 px-2 py-0.5 rounded text-[10px] font-bold text-white"
                        >
                          Retake
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setCameraSnapped(true)}
                        className="w-full h-32 rounded-xl border border-dashed border-slate-700 bg-slate-950/50 flex flex-col items-center justify-center gap-1 hover:border-emerald-500 transition-colors"
                      >
                        <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                          <Camera className="w-5 h-5" />
                        </div>
                        <span className="font-bold text-xs text-slate-200">Snap Photo of Surplus</span>
                        <span className="text-[10px] text-slate-500">Tap to simulate mobile camera shutter</span>
                      </button>
                    )}
                  </div>

                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Surplus Category</span>
                    <div className="flex gap-1.5 overflow-x-auto pb-1">
                      {["cooked_food", "clothes", "blankets", "medical"].map((c) => (
                        <button
                          key={c}
                          onClick={() => setDonationCategory(c)}
                          className={`px-2.5 py-1 rounded-lg text-[10px] font-bold capitalize shrink-0 ${
                            donationCategory === c
                              ? "bg-emerald-600 text-white"
                              : "bg-slate-900 text-slate-400 border border-slate-800"
                          }`}
                        >
                          {c.replace("_", " ")}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="bg-amber-950/30 p-2.5 rounded-xl border border-amber-900/50 space-y-1.5">
                    <div className="flex items-center gap-1.5 text-amber-400 text-[11px] font-bold">
                      <Flame className="w-3.5 h-3.5" />
                      <span>Perishable Expiry Watchdog (1.5h Remaining)</span>
                    </div>
                    <p className="text-[10px] text-amber-200/80">
                      Surplus under 2 hours will automatically escalate to Critical Urgency and double the courier search radius.
                    </p>
                  </div>

                  <button
                    onClick={() => {
                      setDonorDonationSuccess("Surplus registered! Secret Pickup OTP: 482910");
                      setTimeout(() => setCurrentTab("history"), 900);
                    }}
                    className="w-full py-3 rounded-xl bg-emerald-600 text-white font-extrabold text-xs shadow-md shadow-emerald-600/30 active:scale-95 transition-all"
                  >
                    Publish Surplus &amp; Alert Radius
                  </button>

                  {donorDonationSuccess && (
                    <div className="p-2 rounded-lg bg-emerald-950 border border-emerald-700 text-emerald-300 text-[10px] font-bold flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                      <span>{donorDonationSuccess}</span>
                    </div>
                  )}
                </div>
              )}

              {role === "donor" && currentTab === "sponsorship" && (
                <div className="space-y-3">
                  <span className="font-extrabold text-sm text-white">Monetary Sponsorship Calculator</span>
                  <div className="bg-slate-900 p-3 rounded-2xl border border-slate-800 space-y-3">
                    <div>
                      <span className="text-[10px] font-bold text-slate-400">Target Shelter:</span>
                      <div className="p-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs font-bold mt-1">
                        Hope Harvest Food Bank &amp; Shelter
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <span className="text-[10px] font-bold text-slate-400">Units ($15/ea):</span>
                        <input
                          type="number"
                          value={unitCount}
                          onChange={(e) => setUnitCount(Number(e.target.value))}
                          className="w-full p-2 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono font-bold text-xs mt-1"
                        />
                      </div>
                      <div>
                        <span className="text-[10px] font-bold text-slate-400">Total Grant:</span>
                        <div className="p-2 rounded-xl bg-slate-950 border border-slate-800 text-emerald-400 font-mono font-black text-xs mt-1">
                          ${unitCount * unitCost}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2 pt-1">
                      <button
                        onClick={() => setPayNotice(` Pay of $${unitCount * unitCost} confirmed! Receipt logged.`)}
                        className="w-full py-2.5 rounded-xl bg-black border border-slate-700 font-bold text-xs text-white"
                      >
                         Pay ${unitCount * unitCost}
                      </button>
                      <button
                        onClick={() => setPayNotice(`Google Pay of $${unitCount * unitCost} confirmed!`)}
                        className="w-full py-2.5 rounded-xl bg-slate-800 font-bold text-xs text-white"
                      >
                        GPay ${unitCount * unitCost}
                      </button>
                    </div>

                    {payNotice && (
                      <div className="p-2 rounded-lg bg-emerald-950 border border-emerald-700 text-emerald-300 text-[10px] font-bold">
                        {payNotice}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {role === "donor" && currentTab === "history" && (
                <div className="space-y-3">
                  <span className="font-extrabold text-sm text-white">Active Donations &amp; OTPs</span>
                  <div className="space-y-2">
                    <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-black uppercase text-emerald-400">Cooked Food</span>
                        <span className="text-[9px] font-bold bg-amber-950 text-amber-300 px-2 py-0.5 rounded">Claimed</span>
                      </div>
                      <div className="font-bold text-xs text-white">85 Chef-Prepared Catering Trays</div>

                      <div className="p-2 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                        <span className="text-[10px] text-slate-400 font-semibold">Pickup Handshake OTP:</span>
                        <span className="text-sm font-mono font-black text-emerald-400 tracking-wider">482910</span>
                      </div>
                    </div>

                    <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-black uppercase text-blue-400">Clothes</span>
                        <span className="text-[9px] font-bold bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded">Open</span>
                      </div>
                      <div className="font-bold text-xs text-white">60 Heavy Winter Jackets &amp; Hoodies</div>
                      <div className="p-2 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                        <span className="text-[10px] text-slate-400 font-semibold">Pickup Handshake OTP:</span>
                        <span className="text-sm font-mono font-black text-emerald-400 tracking-wider">392019</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {role === "ngo" && currentTab === "alerts_feed" && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-sm text-white">Real-Time Rescue Radar</span>
                    <button
                      onClick={() => setNgoCapacityActive(!ngoCapacityActive)}
                      className={`text-[9px] font-black px-2 py-0.5 rounded-full ${
                        ngoCapacityActive ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-rose-950 text-rose-400 border border-rose-800"
                      }`}
                    >
                      {ngoCapacityActive ? "INTAKE OPEN" : "INTAKE FULL"}
                    </button>
                  </div>

                  {ngoClaimAlert && (
                    <div className="p-2 rounded-lg bg-blue-950 border border-blue-700 text-blue-200 text-[10px] font-bold">
                      {ngoClaimAlert}
                    </div>
                  )}

                  <div className="p-3 rounded-2xl bg-rose-950/40 border border-rose-600 space-y-2 animate-pulse">
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] font-black uppercase bg-rose-600 text-white px-2 py-0.5 rounded">
                        CRITICAL: &lt; 2H EXPIRY
                      </span>
                      <span className="text-[10px] font-bold text-slate-300">2.4 km away</span>
                    </div>
                    <div className="font-bold text-xs text-white">85 Catering Trays (Rice &amp; Curry)</div>
                    <div className="text-[10px] text-slate-400">Grand Central Hospitality &bull; Dock B</div>

                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[10px] text-rose-400 font-mono font-bold">Expires in 1h 12m</span>
                      {claimedTimers["don_101"] ? (
                        <span className="text-[10px] font-mono font-bold text-amber-400 bg-slate-950 px-2 py-1 rounded">
                          Hold Lock: 14:48
                        </span>
                      ) : (
                        <button
                          onClick={() => {
                            setClaimedTimers({ ...claimedTimers, don_101: 900 });
                            setNgoClaimAlert("1-Click Claim locked for 15 minutes! Courier dispatched.");
                          }}
                          className="px-3 py-1.5 rounded-xl bg-rose-600 font-bold text-[10px] text-white"
                        >
                          1-Click Claim
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] font-bold text-blue-400">CLOTHES</span>
                      <span className="text-[10px] font-bold text-slate-400">3.8 km away</span>
                    </div>
                    <div className="font-bold text-xs text-white">60 Winter Coats &amp; Hoodies</div>
                    <button
                      onClick={() => setNgoClaimAlert("Claimed 60 coats for shelter distribution!")}
                      className="w-full py-1.5 rounded-xl bg-blue-600 font-bold text-[10px] text-white"
                    >
                      Claim Donation
                    </button>
                  </div>
                </div>
              )}

              {role === "ngo" && currentTab === "direct_call" && (
                <div className="space-y-3">
                  <span className="font-extrabold text-sm text-white">Direct Donor Voice Desk</span>
                  <div className="space-y-2">
                    <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
                      <div className="font-bold text-xs text-white">Grand Central Hospitality Kitchen</div>
                      <p className="text-[10px] text-slate-400">Buzzer #4 for basement dock barrier.</p>
                      <a
                        href="tel:+15552348901"
                        className="w-full py-2 rounded-xl bg-blue-600 flex items-center justify-center gap-1.5 font-bold text-[11px] text-white"
                      >
                        <Phone className="w-3 h-3" />
                        <span>1-Tap Call: +1 (555) 234-8901</span>
                      </a>
                    </div>
                  </div>
                </div>
              )}

              {role === "ngo" && currentTab === "tracking" && (
                <div className="space-y-3">
                  <span className="font-extrabold text-sm text-white">Inbound Courier Telemetry</span>
                  <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-white">Alex Rivera (Courier #408)</span>
                      <span className="text-[9px] font-bold bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded">En Route</span>
                    </div>
                    <div className="text-[10px] text-slate-400">Toyota ProAce &bull; Refrigerated Cargo Van</div>
                    <div className="p-2 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-[10px]">
                      <span className="text-slate-400">Estimated Arrival:</span>
                      <span className="font-mono font-bold text-amber-400">9 mins (2.4 km)</span>
                    </div>
                  </div>
                </div>
              )}

              {role === "driver" && currentTab === "route_nav" && (
                <div className="space-y-3">

                  <div className="p-3 rounded-2xl bg-emerald-800 text-white space-y-1">
                    <div className="flex items-center justify-between text-[10px] font-black opacity-80 uppercase">
                      <span>Next Maneuver ({maneuvers[maneuverStep].dist})</span>
                      <button
                        onClick={() => setManeuverStep((maneuverStep + 1) % maneuvers.length)}
                        className="bg-black/30 px-2 py-0.5 rounded text-[9px]"
                      >
                        Next Step
                      </button>
                    </div>
                    <div className="font-black text-sm flex items-center gap-1.5">
                      <Navigation className="w-4 h-4 text-emerald-300" />
                      <span>{maneuvers[maneuverStep].text}</span>
                    </div>
                  </div>

                  <div className="h-44 rounded-2xl bg-slate-900 border border-slate-800 relative overflow-hidden flex flex-col justify-between p-3">
                    <div className="flex justify-between items-start z-10">
                      <span className="text-[9px] font-mono bg-black/70 px-2 py-0.5 rounded text-emerald-400">
                        GPS SPEED: 38 KM/H
                      </span>
                      <span className="text-[9px] font-mono bg-black/70 px-2 py-0.5 rounded text-amber-400">
                        ETA: 9 MINS
                      </span>
                    </div>

                    <div className="absolute inset-0 flex items-center justify-center opacity-40">
                      <div className="w-48 h-20 border-2 border-emerald-500 rounded-3xl border-dashed" />
                    </div>

                    <div className="flex justify-between items-end z-10">
                      <div className="bg-black/80 px-2 py-1 rounded text-[9px]">
                        <span className="text-emerald-400 font-bold">A:</span> Grand Central
                      </div>
                      <div className="bg-black/80 px-2 py-1 rounded text-[9px]">
                        <span className="text-blue-400 font-bold">B:</span> Hope Harvest
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => setShowOtpModal(true)}
                    className="w-full py-2.5 rounded-xl bg-amber-600 font-black text-xs text-slate-950 flex items-center justify-center gap-1.5 shadow-md shadow-amber-600/30"
                  >
                    <QrCode className="w-3.5 h-3.5" />
                    <span>Open 6-Digit Handshake / QR Modal</span>
                  </button>
                </div>
              )}

              {currentTab === "ngos" && (
                <div className="space-y-3">
                  <span className="font-extrabold text-sm text-white">Verified Shelter Directory</span>
                  <div className="space-y-2">
                    <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-white">Hope Harvest Food Bank</span>
                        <span className="text-[9px] font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded">Active</span>
                      </div>
                      <p className="text-[10px] text-slate-400">128 Riverfront Blvd &bull; 1,500 daily meals capacity</p>
                      <div className="flex gap-2 pt-1">
                        <a
                          href="tel:+15558912345"
                          className="flex-1 py-1.5 rounded-lg bg-blue-600 text-center font-bold text-[10px] text-white"
                        >
                          1-Tap Call
                        </a>
                        <a
                          href="https://maps.google.com/?q=128+Riverfront+Blvd"
                          target="_blank"
                          rel="noreferrer"
                          className="flex-1 py-1.5 rounded-lg bg-emerald-600 text-center font-bold text-[10px] text-white"
                        >
                          Launch Maps
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {currentTab === "profile" && (
                <div className="space-y-3">
                  <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 space-y-2 text-center">
                    <div className="w-12 h-12 rounded-full bg-emerald-600 mx-auto flex items-center justify-center font-black text-base text-white">
                      {role.charAt(0).toUpperCase()}
                    </div>
                    <div className="font-extrabold text-xs text-white">Sarah Jenkins</div>
                    <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">
                      Active Role: {role}
                    </div>
                  </div>

                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">1-Tap Role Switch</span>
                    <div className="grid grid-cols-3 gap-2">
                      {(["donor", "ngo", "driver"] as MobileRole[]).map((r) => (
                        <button
                          key={r}
                          onClick={() => handleRoleChange(r)}
                          className={`py-2 rounded-xl text-[10px] font-bold uppercase ${
                            role === r
                              ? "bg-emerald-600 text-white"
                              : "bg-slate-900 text-slate-400 border border-slate-800"
                          }`}
                        >
                          {r}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {showOtpModal && (
              <div className="absolute inset-x-4 bottom-16 bg-slate-900 border border-slate-700 rounded-3xl p-4 shadow-2xl z-50 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-xs text-white">6-Digit Verification Handshake</span>
                  <button onClick={() => setShowOtpModal(false)} className="text-slate-400 font-bold text-xs">
                    &times;
                  </button>
                </div>

                <div className="text-[10px] text-slate-300">
                  Enter the 6-digit code provided by the donor at pickup (<span className="font-mono text-emerald-400">482910</span>)
                </div>

                <input
                  type="text"
                  maxLength={6}
                  value={enteredPickupOtp}
                  onChange={(e) => setEnteredPickupOtp(e.target.value)}
                  placeholder="482910"
                  className="w-full text-center text-lg font-mono font-black tracking-widest py-2 rounded-xl bg-slate-950 border border-slate-700 text-white"
                />

                <button
                  onClick={() => {
                    if (enteredPickupOtp === "482910" || enteredPickupOtp.length === 6) {
                      setOtpVerifyResult("Pickup verified! Items secured in van.");
                      setDriverMissionStatus("picked_up");
                      setTimeout(() => setShowOtpModal(false), 800);
                    } else {
                      setOtpVerifyResult("Invalid OTP code. Try: 482910");
                    }
                  }}
                  className="w-full py-2.5 rounded-xl bg-amber-600 text-slate-950 font-bold text-xs"
                >
                  Verify Pickup OTP
                </button>

                {otpVerifyResult && (
                  <div className="text-[10px] font-bold text-center text-emerald-400">
                    {otpVerifyResult}
                  </div>
                )}
              </div>
            )}

            <div className="px-2 py-2 border-t border-slate-800/80 bg-slate-950/90 flex items-center justify-around z-30">
              {role === "donor" && (
                <>
                  <button
                    onClick={() => setCurrentTab("rapid_donate")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "rapid_donate" ? "text-emerald-400 font-bold" : "text-slate-500"}`}
                  >
                    <Camera className="w-4 h-4" />
                    <span className="text-[8px]">Donate</span>
                  </button>
                  <button
                    onClick={() => setCurrentTab("sponsorship")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "sponsorship" ? "text-emerald-400 font-bold" : "text-slate-500"}`}
                  >
                    <DollarSign className="w-4 h-4" />
                    <span className="text-[8px]">Sponsor</span>
                  </button>
                  <button
                    onClick={() => setCurrentTab("history")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "history" ? "text-emerald-400 font-bold" : "text-slate-500"}`}
                  >
                    <Clock className="w-4 h-4" />
                    <span className="text-[8px]">History</span>
                  </button>
                  <button
                    onClick={() => setCurrentTab("ngos")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "ngos" ? "text-emerald-400 font-bold" : "text-slate-500"}`}
                  >
                    <Building2 className="w-4 h-4" />
                    <span className="text-[8px]">NGOs</span>
                  </button>
                  <button
                    onClick={() => setCurrentTab("profile")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "profile" ? "text-emerald-400 font-bold" : "text-slate-500"}`}
                  >
                    <Smartphone className="w-4 h-4" />
                    <span className="text-[8px]">Profile</span>
                  </button>
                </>
              )}

              {role === "ngo" && (
                <>
                  <button
                    onClick={() => setCurrentTab("alerts_feed")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "alerts_feed" ? "text-blue-400 font-bold" : "text-slate-500"}`}
                  >
                    <Flame className="w-4 h-4" />
                    <span className="text-[8px]">Radar</span>
                  </button>
                  <button
                    onClick={() => setCurrentTab("direct_call")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "direct_call" ? "text-blue-400 font-bold" : "text-slate-500"}`}
                  >
                    <Phone className="w-4 h-4" />
                    <span className="text-[8px]">Donor Dial</span>
                  </button>
                  <button
                    onClick={() => setCurrentTab("tracking")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "tracking" ? "text-blue-400 font-bold" : "text-slate-500"}`}
                  >
                    <Navigation className="w-4 h-4" />
                    <span className="text-[8px]">Tracking</span>
                  </button>
                  <button
                    onClick={() => setCurrentTab("ngos")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "ngos" ? "text-blue-400 font-bold" : "text-slate-500"}`}
                  >
                    <Building2 className="w-4 h-4" />
                    <span className="text-[8px]">Network</span>
                  </button>
                  <button
                    onClick={() => setCurrentTab("profile")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "profile" ? "text-blue-400 font-bold" : "text-slate-500"}`}
                  >
                    <Smartphone className="w-4 h-4" />
                    <span className="text-[8px]">Profile</span>
                  </button>
                </>
              )}

              {role === "driver" && (
                <>
                  <button
                    onClick={() => setCurrentTab("route_nav")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "route_nav" ? "text-amber-400 font-bold" : "text-slate-500"}`}
                  >
                    <Navigation className="w-4 h-4" />
                    <span className="text-[8px]">GPS Route</span>
                  </button>
                  <button
                    onClick={() => setShowOtpModal(true)}
                    className="flex flex-col items-center gap-0.5 text-amber-400 font-bold"
                  >
                    <QrCode className="w-4 h-4" />
                    <span className="text-[8px]">OTP / QR</span>
                  </button>
                  <button
                    onClick={() => setCurrentTab("ngos")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "ngos" ? "text-amber-400 font-bold" : "text-slate-500"}`}
                  >
                    <Building2 className="w-4 h-4" />
                    <span className="text-[8px]">Shelters</span>
                  </button>
                  <button
                    onClick={() => setCurrentTab("profile")}
                    className={`flex flex-col items-center gap-0.5 ${currentTab === "profile" ? "text-amber-400 font-bold" : "text-slate-500"}`}
                  >
                    <Smartphone className="w-4 h-4" />
                    <span className="text-[8px]">Profile</span>
                  </button>
                </>
              )}
            </div>

            <div className="pb-1 flex justify-center">
              <div className="w-32 h-1 bg-slate-600 rounded-full" />
            </div>
          </div>
        </div>

        <div className="lg:col-span-6 space-y-6">

          <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div className="flex items-center gap-2">
              <Smartphone className="w-5 h-5 text-emerald-600" />
              <h2 className="text-base font-black text-slate-900 dark:text-white">
                Cross-Platform Mobile Implementation
              </h2>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Built using <strong>React Native</strong> and <strong>Expo</strong> with full TypeScript typing, modular screen components, vector glyphs, and responsive bottom navigation that adapts automatically based on the active role.
            </p>

            <div className="space-y-3 pt-2">
              <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <Camera className="w-3.5 h-3.5 text-emerald-600" />
                  <span>1. Rapid Donation &amp; Camera Integration</span>
                </span>
                <p className="text-[11px] text-slate-500">
                  Captures surplus meals or clothes with embedded time and geo-tags. Monitors expiry with dynamic alerts for surplus under 2 hours.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <Flame className="w-3.5 h-3.5 text-rose-600" />
                  <span>2. NGO Alerts Radar &amp; Direct Dial</span>
                </span>
                <p className="text-[11px] text-slate-500">
                  Real-time proximity feed with 1-click claim, 15-minute reservation timer lock, and 1-tap phone dialer to coordinate with donor docks.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <Navigation className="w-3.5 h-3.5 text-amber-600" />
                  <span>3. Turn-by-Turn GPS Route &amp; Dual OTP</span>
                </span>
                <p className="text-[11px] text-slate-500">
                  Visual waypoint routing (Donor A ➔ Courier ➔ Shelter B) paired with 6-digit OTP verification inputs for secure physical pickup and drop-off.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 text-white rounded-3xl p-6 border border-slate-800 shadow-sm space-y-3 font-mono text-xs">
            <span className="text-emerald-400 font-bold flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              <span>Native Mobile Run Instructions</span>
            </span>
            <div className="bg-slate-950 p-3 rounded-xl space-y-1 text-[11px] text-slate-300">
              <p className="text-slate-500"># Navigate to mobile project</p>
              <p className="text-emerald-400">cd mobile</p>
              <p className="text-slate-500"># Start Expo cross-platform Metro bundler</p>
              <p className="text-emerald-400">npm start</p>
              <p className="text-slate-500"># Scan QR code in Expo Go app (iOS or Android)</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
