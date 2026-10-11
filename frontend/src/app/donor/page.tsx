"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useApp } from "@/context/AppContext";
import { DonationCategory, DonationUrgency } from "@/lib/types";
import {
  Gift,
  UtensilsCrossed,
  Shirt,
  ShieldAlert,
  Flame,
  Clock,
  MapPin,
  CheckCircle2,
  DollarSign,
  Package,
  Layers,
  Sparkles,
  TrendingUp,
  Leaf,
  Users,
  Award,
  ChevronRight,
  ArrowRight,
  AlertTriangle,
  QrCode,
  Heart,
} from "lucide-react";

export default function DonorDashboard() {
  const { user } = useAuth();
  const { donations, ngos, createDonation, esgStats } = useApp();

  const [activeTab, setActiveTab] = useState<DonationCategory>("cooked_food");
  const [step, setStep] = useState<1 | 2>(1);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [quantity, setQuantity] = useState(25);
  const [unit, setUnit] = useState("servings");
  const [pickupAddress, setPickupAddress] = useState(
    user?.address || "742 Evergreen Terrace, Kitchen Loading Dock"
  );
  const [urgency, setUrgency] = useState<DonationUrgency>("high");

  const [preparedHoursAgo, setPreparedHoursAgo] = useState(1);
  const [expiresInHours, setExpiresInHours] = useState(3);
  const [dietaryTags, setDietaryTags] = useState<string[]>(["Vegetarian", "Hot"]);

  const [clothesCondition, setClothesCondition] = useState("Brand New / Like New");
  const [seasonType, setSeasonType] = useState("Winter Heavy");

  const [targetNgoId, setTargetNgoId] = useState(ngos[0]?.id || "ngo_201");
  const [unitCost, setUnitCost] = useState(15);
  const [itemGoalCount, setItemGoalCount] = useState(50);
  const [earmarkedItemName, setEarmarkedItemName] = useState("Thermal Winter Blankets");

  const categoryConfigs: Record<
    DonationCategory,
    { label: string; icon: any; color: string; defaultUnit: string; badge: string }
  > = {
    cooked_food: {
      label: "Cooked Food",
      icon: UtensilsCrossed,
      color: "emerald",
      defaultUnit: "servings / trays",
      badge: "Perishable Watchdog",
    },
    clothes: {
      label: "Clothes",
      icon: Shirt,
      color: "blue",
      defaultUnit: "pieces / bags",
      badge: "Apparel Overstock",
    },
    blankets: {
      label: "Blankets",
      icon: Layers,
      color: "indigo",
      defaultUnit: "blankets",
      badge: "Emergency Warmth",
    },
    medical: {
      label: "Medical Supplies",
      icon: ShieldAlert,
      color: "rose",
      defaultUnit: "kits / boxes",
      badge: "Sterile & Sealed",
    },
    other: {
      label: "Custom Item",
      icon: Package,
      color: "amber",
      defaultUnit: "units",
      badge: "Custom Surplus",
    },
    earmarked_money: {
      label: "Earmarked Money",
      icon: DollarSign,
      color: "teal",
      defaultUnit: "units to fund",
      badge: "Direct Impact",
    },
  };

  const currentConfig = categoryConfigs[activeTab];
  const CategoryIcon = currentConfig.icon;

  const handleTabChange = (tab: DonationCategory) => {
    setActiveTab(tab);
    setUnit(categoryConfigs[tab].defaultUnit);
    if (tab === "cooked_food") {
      setTitle("Surplus Catering Trays (Warm Buffet)");
      setUrgency("high");
    } else if (tab === "clothes") {
      setTitle("Warm Winter Coats & Thermal Hoodies");
      setUrgency("normal");
    } else if (tab === "blankets") {
      setTitle("Heavy Emergency Fleece Blankets");
      setUrgency("high");
    } else if (tab === "medical") {
      setTitle("First Aid Wound Care & Disinfectant Kits");
      setUrgency("normal");
    } else if (tab === "earmarked_money") {
      setTitle(`Direct Sponsorship: ${earmarkedItemName}`);
      setUrgency("normal");
    } else {
      setTitle("Surplus Kitchen Storage Racks & Trays");
      setUrgency("normal");
    }
  };

  const handleCreateDonation = (e: React.FormEvent) => {
    e.preventDefault();

    const preparedAt =
      activeTab === "cooked_food"
        ? new Date(Date.now() - preparedHoursAgo * 3600 * 1000).toISOString()
        : undefined;
    const expiresAt =
      activeTab === "cooked_food"
        ? new Date(Date.now() + expiresInHours * 3600 * 1000).toISOString()
        : undefined;

    const targetNgo = ngos.find((n) => n.id === targetNgoId);

    const calculatedUrgency: DonationUrgency =
      activeTab === "cooked_food" && expiresInHours <= 2 ? "critical" : urgency;

    const newDonation = createDonation({
      donor_id: user?.id || "usr_donor_1",
      donor_name: user?.organizationName || user?.name || "Grand Central Hospitality",
      donor_phone: user?.phone || "+1 (555) 234-8901",
      category: activeTab,
      title: title || `${currentConfig.label} Surplus Batch`,
      description:
        description ||
        `High quality surplus donation generated from ${user?.name || "Community Partner"}. Packaged safely.`,
      quantity: activeTab === "earmarked_money" ? itemGoalCount : quantity,
      unit: unit,
      prepared_at: preparedAt,
      expires_at: expiresAt,
      pickup_address: pickupAddress,
      latitude: 37.7749 + (Math.random() - 0.5) * 0.05,
      longitude: -122.4194 + (Math.random() - 0.5) * 0.05,
      urgency: calculatedUrgency,
      dietary_tags: activeTab === "cooked_food" ? dietaryTags : undefined,
      cost_per_unit: activeTab === "earmarked_money" ? unitCost : undefined,
      amount_goal: activeTab === "earmarked_money" ? unitCost * itemGoalCount : undefined,
      amount_funded: activeTab === "earmarked_money" ? unitCost * itemGoalCount : undefined,
      target_ngo_id: activeTab === "earmarked_money" ? targetNgoId : undefined,
      target_ngo_name: activeTab === "earmarked_money" ? targetNgo?.name : undefined,
    });

    setSuccessBanner(
      `Donation registered successfully! Your Pickup Verification OTP is ${newDonation.pickup_otp}. Frontline NGOs & Couriers within radius have been notified!`
    );
    setStep(1);

    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const donorDonations = donations.filter(
    (d) => d.donor_id === user?.id || d.donor_name.includes("Grand") || d.donor_name.includes("Sarah")
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

      <div className="relative rounded-3xl bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 text-white p-6 sm:p-8 overflow-hidden shadow-xl border border-emerald-800/40">
        <div className="absolute right-0 top-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Donor Impact Hub &bull; S.T.S Certified</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
              Welcome, {user?.name || "Corporate Donor Partner"}
            </h1>
            <p className="text-xs sm:text-sm text-emerald-200/80 max-w-xl">
              Turn commercial surplus into immediate community relief. Every tray of prepared food and relief box is dispatched via PostGIS proximity matching.
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-3">
            <a
              href="#donation-wizard"
              className="px-5 py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold text-xs shadow-lg shadow-emerald-500/30 transition-all flex items-center gap-2"
            >
              <Gift className="w-4 h-4" />
              <span>Create New Surplus Donation</span>
            </a>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-white/10">
          <div className="bg-white/5 backdrop-blur-md rounded-2xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold mb-1">
              <Leaf className="w-4 h-4" />
              <span>CO₂ Prevented</span>
            </div>
            <div className="text-xl sm:text-2xl font-black font-mono">
              {esgStats.co2KgPrevented.toLocaleString()} kg
            </div>
            <p className="text-[11px] text-slate-300 mt-0.5">Landfill methane averted</p>
          </div>

          <div className="bg-white/5 backdrop-blur-md rounded-2xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-teal-400 text-xs font-bold mb-1">
              <UtensilsCrossed className="w-4 h-4" />
              <span>Meals Rescued</span>
            </div>
            <div className="text-xl sm:text-2xl font-black font-mono">
              {esgStats.mealsSaved.toLocaleString()}
            </div>
            <p className="text-[11px] text-slate-300 mt-0.5">Surplus served to shelters</p>
          </div>

          <div className="bg-white/5 backdrop-blur-md rounded-2xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold mb-1">
              <Users className="w-4 h-4" />
              <span>Partner NGOs</span>
            </div>
            <div className="text-xl sm:text-2xl font-black font-mono">
              {ngos.length} Verified
            </div>
            <p className="text-[11px] text-slate-300 mt-0.5">Active feeding centers</p>
          </div>

          <div className="bg-white/5 backdrop-blur-md rounded-2xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-amber-400 text-xs font-bold mb-1">
              <Award className="w-4 h-4" />
              <span>ESG Impact Tier</span>
            </div>
            <div className="text-xl sm:text-2xl font-black font-mono">
              Platinum Star
            </div>
            <p className="text-[11px] text-slate-300 mt-0.5">Top 5% Corporate Donors</p>
          </div>
        </div>
      </div>

      {successBanner && (
        <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/80 border border-emerald-300 dark:border-emerald-800 shadow-sm flex items-start justify-between gap-3 animate-in fade-in">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-xs sm:text-sm font-bold text-emerald-900 dark:text-emerald-200">
                {successBanner}
              </p>
              <p className="text-xs text-emerald-700 dark:text-emerald-400 mt-0.5">
                Keep your 6-digit pickup OTP ready. You will share it with the driver upon physical handoff.
              </p>
            </div>
          </div>
          <button
            onClick={() => setSuccessBanner(null)}
            className="text-emerald-700 hover:text-emerald-900 text-xs font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

        <div id="donation-wizard" className="lg:col-span-7 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-lg overflow-hidden">

            <div className="p-6 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center text-emerald-700 dark:text-emerald-300">
                    <CategoryIcon className="w-4 h-4" />
                  </div>
                  <h2 className="text-lg font-black text-slate-900 dark:text-white">
                    Multi-Step Donation Wizard
                  </h2>
                </div>
                <div className="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  Step {step} of 2
                </div>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Choose what you are donating. The S.T.S matching engine calculates radius and alerts nearby food banks and relief centers in real time.
              </p>

              <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5 mt-5">
                {(
                  [
                    "cooked_food",
                    "clothes",
                    "blankets",
                    "medical",
                    "other",
                    "earmarked_money",
                  ] as DonationCategory[]
                ).map((cat) => {
                  const conf = categoryConfigs[cat];
                  const Icon = conf.icon;
                  const isActive = activeTab === cat;
                  return (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => handleTabChange(cat)}
                      className={`flex flex-col items-center justify-center p-2 rounded-xl text-center transition-all ${
                        isActive
                          ? "bg-emerald-600 text-white font-bold shadow-md shadow-emerald-600/20 scale-[1.02]"
                          : "bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 font-medium"
                      }`}
                    >
                      <Icon className="w-4 h-4 mb-1" />
                      <span className="text-[10px] leading-tight line-clamp-1">{conf.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <form onSubmit={handleCreateDonation} className="p-6 space-y-5">
              {step === 1 ? (

                <div className="space-y-4">

                  <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 text-xs">
                    <span className="font-bold text-slate-800 dark:text-slate-200">
                      Configuring: {currentConfig.label}
                    </span>
                    <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                      {currentConfig.badge}
                    </span>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Title / Description of Donation
                    </label>
                    <input
                      type="text"
                      required
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder={
                        activeTab === "cooked_food"
                          ? "e.g. 85 Freshly Prepared Buffet Rice & Dal Trays"
                          : activeTab === "earmarked_money"
                          ? "e.g. 50 Winter Blankets Direct Sponsorship"
                          : "e.g. 40 Warm Heavy Winter Fleeces"
                      }
                      className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>

                  {activeTab === "cooked_food" && (
                    <div className="p-4 rounded-2xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 space-y-4">
                      <div className="flex items-center gap-2 text-xs font-bold text-amber-800 dark:text-amber-300">
                        <Flame className="w-4 h-4 text-amber-600" />
                        <span>Perishable Food Safety &amp; Expiry Watchdog</span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                        <div>
                          <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                            When was it prepared?
                          </label>
                          <select
                            value={preparedHoursAgo}
                            onChange={(e) => setPreparedHoursAgo(Number(e.target.value))}
                            className="w-full p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200"
                          >
                            <option value={0.5}>Just prepared (30 mins ago)</option>
                            <option value={1}>1 hour ago</option>
                            <option value={2}>2 hours ago</option>
                            <option value={4}>4 hours ago</option>
                          </select>
                        </div>

                        <div>
                          <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                            Remaining Safe Window (Hours)
                          </label>
                          <select
                            value={expiresInHours}
                            onChange={(e) => setExpiresInHours(Number(e.target.value))}
                            className="w-full p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200"
                          >
                            <option value={1.5}>1.5 Hours (&lt; 2h: Auto-Critical Escalation)</option>
                            <option value={3}>3 Hours (Urgent Rescue)</option>
                            <option value={6}>6 Hours (Standard Perishable)</option>
                            <option value={12}>12 Hours (Refrigerated)</option>
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                          Dietary Tags &amp; Handling
                        </label>
                        <div className="flex flex-wrap gap-1.5">
                          {["Vegetarian", "Vegan", "Halal", "Non-Veg", "Nut-Free", "Hot Thermal Contained"].map(
                            (tag) => {
                              const selected = dietaryTags.includes(tag);
                              return (
                                <button
                                  key={tag}
                                  type="button"
                                  onClick={() =>
                                    setDietaryTags(
                                      selected
                                        ? dietaryTags.filter((t) => t !== tag)
                                        : [...dietaryTags, tag]
                                    )
                                  }
                                  className={`px-2.5 py-1 text-[11px] rounded-lg font-semibold transition-all ${
                                    selected
                                      ? "bg-amber-600 text-white shadow-sm"
                                      : "bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700"
                                  }`}
                                >
                                  {tag}
                                </button>
                              );
                            }
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === "earmarked_money" && (
                    <div className="p-4 rounded-2xl bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40 space-y-4">
                      <div className="flex items-center gap-2 text-xs font-bold text-teal-800 dark:text-teal-300">
                        <DollarSign className="w-4 h-4 text-teal-600" />
                        <span>Earmarked Monetary Sponsorship Calculator</span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                        <div>
                          <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                            Target NGO Recipient
                          </label>
                          <select
                            value={targetNgoId}
                            onChange={(e) => setTargetNgoId(e.target.value)}
                            className="w-full p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200"
                          >
                            {ngos.map((ngo) => (
                              <option key={ngo.id} value={ngo.id}>
                                {ngo.name} ({ngo.city})
                              </option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                            Specific Item To Fund
                          </label>
                          <input
                            type="text"
                            value={earmarkedItemName}
                            onChange={(e) => setEarmarkedItemName(e.target.value)}
                            placeholder="e.g. 50 Thermal Blankets"
                            className="w-full p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200"
                          />
                        </div>

                        <div>
                          <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                            Cost Per Item Unit ($)
                          </label>
                          <input
                            type="number"
                            min={1}
                            value={unitCost}
                            onChange={(e) => setUnitCost(Number(e.target.value))}
                            className="w-full p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200"
                          />
                        </div>

                        <div>
                          <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                            Units To Sponsor
                          </label>
                          <input
                            type="number"
                            min={1}
                            value={itemGoalCount}
                            onChange={(e) => setItemGoalCount(Number(e.target.value))}
                            className="w-full p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200"
                          />
                        </div>
                      </div>

                      <div className="p-3 rounded-xl bg-white dark:bg-slate-900 border border-teal-200 dark:border-teal-800 flex items-center justify-between">
                        <div>
                          <span className="text-[11px] text-slate-500 font-semibold">Total Earmarked Funding:</span>
                          <p className="text-xs text-slate-700 dark:text-slate-300">
                            {itemGoalCount} &times; ${unitCost} = <strong className="text-teal-600">${itemGoalCount * unitCost}</strong>
                          </p>
                        </div>
                        <span className="px-3 py-1 rounded-full text-xs font-black bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200">
                          100% Tax Deductible
                        </span>
                      </div>
                    </div>
                  )}

                  {activeTab !== "earmarked_money" && (
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                          Quantity
                        </label>
                        <input
                          type="number"
                          min={1}
                          required
                          value={quantity}
                          onChange={(e) => setQuantity(Number(e.target.value))}
                          className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                          Unit / Container Type
                        </label>
                        <input
                          type="text"
                          required
                          value={unit}
                          onChange={(e) => setUnit(e.target.value)}
                          placeholder="e.g. sealed trays, boxes"
                          className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
                        />
                      </div>
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Packaging Details &amp; Handling Instructions
                    </label>
                    <textarea
                      rows={2}
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="e.g. Packed in stackable containers. Heavy boxes, dolly recommended. Loading bay elevator on left."
                      className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
                    />
                  </div>

                  <div className="pt-2">
                    <button
                      type="button"
                      onClick={() => setStep(2)}
                      className="w-full py-2.5 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold flex items-center justify-center gap-2 hover:opacity-90 transition-all"
                    >
                      <span>Proceed to Logistics &amp; Dispatch (Step 2)</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ) : (

                <div className="space-y-4">
                  <div className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 text-xs flex items-center justify-between">
                    <div>
                      <span className="font-bold text-slate-900 dark:text-white">Summary: </span>
                      <span className="text-slate-600 dark:text-slate-300">{title || currentConfig.label}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setStep(1)}
                      className="text-xs text-emerald-600 font-bold hover:underline"
                    >
                      Edit Details
                    </button>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      Pickup Address &amp; Dock Location
                    </label>
                    <div className="relative">
                      <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                      <input
                        type="text"
                        required
                        value={pickupAddress}
                        onChange={(e) => setPickupAddress(e.target.value)}
                        placeholder="742 Evergreen Terrace, Kitchen Dock B"
                        className="w-full pl-9 pr-3 py-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                      Urgency Classification
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {(["normal", "high", "critical"] as DonationUrgency[]).map((urg) => (
                        <button
                          key={urg}
                          type="button"
                          onClick={() => setUrgency(urg)}
                          className={`p-2.5 rounded-xl border text-xs font-bold capitalize transition-all text-center ${
                            urgency === urg
                              ? urg === "critical"
                                ? "bg-rose-50 border-rose-500 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300"
                                : urg === "high"
                                ? "bg-amber-50 border-amber-500 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300"
                                : "bg-emerald-50 border-emerald-500 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
                              : "border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800"
                          }`}
                        >
                          {urg}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-xs space-y-1">
                    <div className="font-bold text-emerald-900 dark:text-emerald-200 flex items-center gap-1.5">
                      <QrCode className="w-4 h-4 text-emerald-600" />
                      <span>Dual-Handshake 6-Digit OTP Security</span>
                    </div>
                    <p className="text-emerald-700 dark:text-emerald-400 text-[11px]">
                      Upon creation, S.T.S generates a secret 6-digit `pickup_otp` for you. Do not release the items until the driver provides this matching code.
                    </p>
                  </div>

                  <div className="flex gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setStep(1)}
                      className="w-1/3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      className="w-2/3 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 flex items-center justify-center gap-2 transition-all"
                    >
                      <Sparkles className="w-4 h-4" />
                      <span>Publish Donation &amp; Notify Radius</span>
                    </button>
                  </div>
                </div>
              )}
            </form>
          </div>
        </div>

        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-600" />
                <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                  Your Active Donations &amp; Status
                </h3>
              </div>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                {donorDonations.length} Active
              </span>
            </div>

            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
              {donorDonations.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-400">
                  No active donations yet. Use the wizard to generate your first surplus dispatch!
                </div>
              ) : (
                donorDonations.map((don) => {
                  const conf = categoryConfigs[don.category] || categoryConfigs.other;
                  const Icon = conf.icon;
                  return (
                    <div
                      key={don.id}
                      className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-700/60 space-y-2 hover:border-emerald-500/40 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-lg bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center text-emerald-700 dark:text-emerald-300 shrink-0">
                            <Icon className="w-3.5 h-3.5" />
                          </div>
                          <div>
                            <h4 className="text-xs font-bold text-slate-900 dark:text-white line-clamp-1">
                              {don.title}
                            </h4>
                            <span className="text-[10px] text-slate-500 font-medium capitalize">
                              {don.category.replace("_", " ")} &bull; {don.quantity} {don.unit}
                            </span>
                          </div>
                        </div>

                        <span
                          className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-md shrink-0 ${
                            don.status === "open"
                              ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                              : don.status === "claimed"
                              ? "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
                              : don.status === "in_transit"
                              ? "bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300"
                              : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                          }`}
                        >
                          {don.status}
                        </span>
                      </div>

                      <div className="flex items-center justify-between p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
                        <span className="text-[11px] font-semibold text-slate-500">
                          Donor Pickup OTP:
                        </span>
                        <span className="font-mono font-black text-emerald-600 dark:text-emerald-400 text-xs tracking-wider bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
                          {don.pickup_otp}
                        </span>
                      </div>

                      {don.expires_at && (
                        <div className="flex items-center gap-1.5 text-[11px] text-rose-600 dark:text-rose-400 font-medium">
                          <Clock className="w-3.5 h-3.5 shrink-0" />
                          <span>
                            Perishable Expiry: {new Date(don.expires_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>

          <div className="p-5 rounded-3xl bg-gradient-to-br from-slate-900 to-slate-800 text-white space-y-3 border border-slate-700 shadow-md">
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-emerald-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                Corporate Social Responsibility (CSR)
              </h4>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Every surplus meal logged through S.T.S generates verified Scope 3 waste diversion carbon certificates for corporate environmental audits.
            </p>
            <div className="pt-1 flex items-center justify-between text-xs font-bold">
              <span className="text-emerald-400 font-mono">Status: Audit Verified</span>
              <span className="text-[11px] text-slate-400 underline cursor-pointer">
                Download ESG PDF Summary &rarr;
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
