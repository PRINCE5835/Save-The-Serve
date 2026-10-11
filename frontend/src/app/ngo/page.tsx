"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useApp } from "@/context/AppContext";
import { DonationCategory, DonationUrgency, WishlistItem } from "@/lib/types";
import {
  Building2,
  AlertTriangle,
  Clock,
  MapPin,
  CheckCircle2,
  Sliders,
  Plus,
  Flame,
  Radio,
  Eye,
  DollarSign,
  PackageCheck,
  ShieldCheck,
  Sparkles,
  Layers,
  UtensilsCrossed,
  Shirt,
  ShieldAlert,
  ChevronRight,
  Filter,
} from "lucide-react";

export default function NGODashboard() {
  const { user } = useAuth();
  const {
    donations,
    ngos,
    claimDonationByNGO,
    toggleNGOCapacity,
    createWishlistItem,
  } = useApp();

  const currentNgo =
    ngos.find((n) => n.id === "ngo_201") || ngos[0];

  const [capacityActive, setCapacityActive] = useState(
    currentNgo ? currentNgo.intake_capacity_active : true
  );
  const [operatingRadius, setOperatingRadius] = useState(
    currentNgo ? currentNgo.operating_radius_km : 25
  );

  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [filterUrgency, setFilterUrgency] = useState<string>("all");

  const [claimedDonationIds, setClaimedDonationIds] = useState<Record<string, number>>({});
  const [claimAlert, setClaimAlert] = useState<string | null>(null);

  const [showWishlistModal, setShowWishlistModal] = useState(false);
  const [wishlistTitle, setWishlistTitle] = useState("");
  const [wishlistUnitCost, setWishlistUnitCost] = useState(15);
  const [wishlistTargetCount, setWishlistTargetCount] = useState(100);
  const [wishlistCategory, setWishlistCategory] = useState<DonationCategory>("blankets");
  const [wishlistUrgent, setWishlistUrgent] = useState(true);

  useEffect(() => {
    const timer = setInterval(() => {
      setClaimedDonationIds((prev) => {
        const next: Record<string, number> = {};
        for (const [id, seconds] of Object.entries(prev)) {
          if (seconds > 1) {
            next[id] = seconds - 1;
          }
        }
        return next;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleCapacityToggle = () => {
    const nextVal = !capacityActive;
    setCapacityActive(nextVal);
    if (currentNgo) {
      toggleNGOCapacity(currentNgo.id, nextVal);
    }
  };

  const handleClaim = (donationId: string, title: string) => {
    const success = claimDonationByNGO(
      donationId,
      currentNgo ? currentNgo.id : "ngo_201",
      currentNgo ? currentNgo.name : "Hope Harvest Food Bank"
    );

    if (success) {

      setClaimedDonationIds((prev) => ({ ...prev, [donationId]: 900 }));
      setClaimAlert(`Claim lock secured for "${title}"! You have a 15-minute reservation hold. A volunteer driver has been dispatched.`);
    }
  };

  const handleCreateWishlist = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentNgo) return;

    createWishlistItem(currentNgo.id, {
      title: wishlistTitle,
      unit_cost: wishlistUnitCost,
      target_count: wishlistTargetCount,
      category: wishlistCategory,
      urgent: wishlistUrgent,
    });

    setShowWishlistModal(false);
    setWishlistTitle("");
    setClaimAlert(`Wishlist item "${wishlistTitle}" published! Donors can now sponsor this directly.`);
  };

  const formatTimer = (totalSeconds: number) => {
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  const filteredDonations = donations.filter((d) => {
    if (selectedCategory !== "all" && d.category !== selectedCategory) return false;
    if (filterUrgency !== "all" && d.urgency !== filterUrgency) return false;
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

      <div className="rounded-3xl bg-gradient-to-r from-blue-950 via-slate-900 to-indigo-950 text-white p-6 sm:p-8 shadow-xl border border-blue-800/40 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30">
              <Radio className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
              <span>Real-Time Geospatial Rescue Radar</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
              {currentNgo?.name || "Hope Harvest Food Bank & Shelter"}
            </h1>
            <p className="text-xs sm:text-sm text-blue-200/80 max-w-xl">
              Frontline rescue coordination center. Incoming surplus cooked food and goods within your radius appear instantly with dynamic urgency escalation.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/10 shrink-0 space-y-3">
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs font-bold text-slate-200">Intake Capacity:</span>
              <button
                type="button"
                onClick={handleCapacityToggle}
                className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all flex items-center gap-1.5 ${
                  capacityActive
                    ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/30"
                    : "bg-rose-500 text-white"
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${capacityActive ? "bg-slate-950" : "bg-white"} animate-ping`} />
                <span>{capacityActive ? "INTAKE ACTIVE (OPEN)" : "INTAKE PAUSED (FULL)"}</span>
              </button>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs text-blue-200">
                <span>Alert Radius:</span>
                <span className="font-mono font-bold text-white">{operatingRadius} km</span>
              </div>
              <input
                type="range"
                min={5}
                max={50}
                value={operatingRadius}
                onChange={(e) => setOperatingRadius(Number(e.target.value))}
                className="w-full accent-blue-500 h-1.5 bg-blue-900 rounded-lg cursor-pointer"
              />
            </div>
          </div>
        </div>
      </div>

      {claimAlert && (
        <div className="p-4 rounded-2xl bg-blue-50 dark:bg-blue-950/80 border border-blue-300 dark:border-blue-800 shadow-sm flex items-start justify-between gap-3 animate-in fade-in">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
            <p className="text-xs sm:text-sm font-bold text-blue-900 dark:text-blue-200">
              {claimAlert}
            </p>
          </div>
          <button
            onClick={() => setClaimAlert(null)}
            className="text-blue-700 hover:text-blue-900 text-xs font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

        <div className="lg:col-span-8 space-y-5">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-lg p-6">

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100 dark:border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <Flame className="w-5 h-5 text-rose-500 animate-bounce" />
                  <h2 className="text-base sm:text-lg font-black text-slate-900 dark:text-white">
                    Incoming Surplus Dispatch Feed
                  </h2>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Live PostGIS query active within {operatingRadius} km radius of your intake dock.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-xs font-semibold text-slate-700 dark:text-slate-300"
                >
                  <option value="all">All Categories</option>
                  <option value="cooked_food">Cooked Food</option>
                  <option value="clothes">Clothes</option>
                  <option value="blankets">Blankets</option>
                  <option value="medical">Medical</option>
                  <option value="earmarked_money">Earmarked Money</option>
                </select>

                <select
                  value={filterUrgency}
                  onChange={(e) => setFilterUrgency(e.target.value)}
                  className="px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-xs font-semibold text-slate-700 dark:text-slate-300"
                >
                  <option value="all">All Urgency</option>
                  <option value="critical">Critical (&lt; 2h)</option>
                  <option value="high">High</option>
                  <option value="normal">Normal</option>
                </select>
              </div>
            </div>

            <div className="space-y-4 pt-5">
              {filteredDonations.length === 0 ? (
                <div className="text-center py-12 text-slate-400 text-xs">
                  No open surplus matching your current filters in this radius.
                </div>
              ) : (
                filteredDonations.map((item) => {
                  const isClaimedByMe =
                    item.claimed_by_ngo_id === (currentNgo ? currentNgo.id : "ngo_201") ||
                    item.status === "claimed";
                  const remainingSeconds = claimedDonationIds[item.id] || 0;
                  const isCriticalUrgency = item.urgency === "critical";

                  return (
                    <div
                      key={item.id}
                      className={`p-4 sm:p-5 rounded-2xl border transition-all relative overflow-hidden ${
                        isCriticalUrgency
                          ? "border-rose-400/80 bg-rose-50/40 dark:bg-rose-950/20 animate-critical-pulse"
                          : "border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/30 hover:border-blue-400"
                      }`}
                    >

                      {isCriticalUrgency && (
                        <div className="bg-rose-600 text-white text-[10px] font-black uppercase tracking-wider py-0.5 px-3 -mt-4 -mx-4 sm:-mt-5 sm:-mx-5 mb-3 flex items-center justify-between">
                          <span className="flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            CRITICAL URGENCY: EXPIRING IN &lt; 2 HOURS
                          </span>
                          <span>SEARCH RADIUS EXPANDED 2X BY S.T.S WATCHDOG</span>
                        </div>
                      )}

                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                        <div className="space-y-2 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span
                              className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-md ${
                                item.category === "cooked_food"
                                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                                  : item.category === "clothes"
                                  ? "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
                                  : item.category === "blankets"
                                  ? "bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300"
                                  : "bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-300"
                              }`}
                            >
                              {item.category.replace("_", " ")}
                            </span>

                            <span className="text-[10px] font-bold text-slate-500 flex items-center gap-1">
                              <MapPin className="w-3 h-3 text-blue-500" />
                              <span>{item.distance_km || 2.4} km away</span>
                            </span>

                            {item.quantity && (
                              <span className="text-[10px] font-bold bg-slate-200/80 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-700 dark:text-slate-300">
                                {item.quantity} {item.unit}
                              </span>
                            )}
                          </div>

                          <h3 className="text-sm sm:text-base font-extrabold text-slate-900 dark:text-white">
                            {item.title}
                          </h3>

                          <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
                            {item.description}
                          </p>

                          {item.dietary_tags && item.dietary_tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 pt-1">
                              {item.dietary_tags.map((tag) => (
                                <span
                                  key={tag}
                                  className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}

                          <div className="flex items-center gap-3 text-[11px] text-slate-500 pt-1">
                            <span>Donor: <strong>{item.donor_name}</strong></span>
                            <span>&bull;</span>
                            <span className="line-clamp-1">{item.pickup_address}</span>
                          </div>
                        </div>

                        <div className="sm:text-right shrink-0 flex flex-col sm:items-end justify-between gap-3">
                          {item.status === "open" ? (
                            <button
                              type="button"
                              onClick={() => handleClaim(item.id, item.title)}
                              className={`px-4 py-2 rounded-xl text-xs font-black shadow-md transition-all flex items-center gap-2 ${
                                isCriticalUrgency
                                  ? "bg-rose-600 hover:bg-rose-700 text-white shadow-rose-600/30 animate-pulse"
                                  : "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-600/20"
                              }`}
                            >
                              <PackageCheck className="w-4 h-4" />
                              <span>1-Click Claim Rescue</span>
                            </button>
                          ) : isClaimedByMe ? (
                            <div className="space-y-1 sm:text-right">
                              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border border-blue-300 dark:border-blue-800">
                                <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
                                <span>Claimed By You</span>
                              </span>
                              {remainingSeconds > 0 && (
                                <div className="text-[11px] font-mono font-bold text-amber-600 dark:text-amber-400">
                                  Hold Lock: {formatTimer(remainingSeconds)}
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className="text-xs font-bold text-slate-400 uppercase">
                              Already Claimed
                            </span>
                          )}

                          {item.expires_at && (
                            <span className="text-[11px] font-medium text-rose-600 dark:text-rose-400 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              <span>
                                Expiry: {new Date(item.expires_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                              </span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-600" />
                <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                  Earmarked Wishlists
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowWishlistModal(true)}
                className="px-2.5 py-1 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center gap-1 shadow-sm"
              >
                <Plus className="w-3 h-3" />
                <span>New Wishlist</span>
              </button>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Publish tangible items your shelter needs. Donors can fund exact unit quantities directly through the app.
            </p>

            <div className="space-y-4">
              {currentNgo?.wishlists && currentNgo.wishlists.length > 0 ? (
                currentNgo.wishlists.map((w) => {
                  const percentFunded = Math.min(
                    100,
                    Math.round((w.funded_count / w.target_count) * 100)
                  );
                  return (
                    <div
                      key={w.id}
                      className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-700/60 space-y-2"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                          {w.title}
                        </h4>
                        {w.urgent && (
                          <span className="text-[10px] font-black uppercase px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300">
                            Urgent
                          </span>
                        )}
                      </div>

                      <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
                        <span>
                          ${w.unit_cost} / item
                        </span>
                        <span className="font-mono font-bold text-slate-900 dark:text-white">
                          {w.funded_count} / {w.target_count} Funded ({percentFunded}%)
                        </span>
                      </div>

                      <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                          style={{ width: `${percentFunded}%` }}
                        />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-6 text-xs text-slate-400">
                  No wishlists published yet. Click "New Wishlist" to post shelter requirements.
                </div>
              )}
            </div>
          </div>

          <div className="p-5 rounded-3xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs space-y-2">
            <div className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
              <span>Verified Shelter ID: {currentNgo?.registration_number || "EIN-84-93821"}</span>
            </div>
            <p className="text-slate-500 dark:text-slate-400 text-[11px]">
              Daily Feeding Capacity: {currentNgo?.current_daily_meals} / {currentNgo?.max_daily_meals} meals served today.
            </p>
          </div>
        </div>
      </div>

      {showWishlistModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 w-full max-w-md space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-black text-slate-900 dark:text-white">
                Create Earmarked Wishlist
              </h3>
              <button
                onClick={() => setShowWishlistModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateWishlist} className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Item Description
                </label>
                <input
                  type="text"
                  required
                  value={wishlistTitle}
                  onChange={(e) => setWishlistTitle(e.target.value)}
                  placeholder="e.g. Heavy Duty Cold-Weather Sleeping Bags"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Cost Per Unit ($)
                  </label>
                  <input
                    type="number"
                    min={1}
                    required
                    value={wishlistUnitCost}
                    onChange={(e) => setWishlistUnitCost(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Target Needed
                  </label>
                  <input
                    type="number"
                    min={1}
                    required
                    value={wishlistTargetCount}
                    onChange={(e) => setWishlistTargetCount(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Category
                </label>
                <select
                  value={wishlistCategory}
                  onChange={(e) => setWishlistCategory(e.target.value as DonationCategory)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
                >
                  <option value="blankets">Blankets &amp; Warmth</option>
                  <option value="clothes">Clothes &amp; Apparel</option>
                  <option value="cooked_food">Dry Food &amp; Grains</option>
                  <option value="medical">Medical &amp; Hygiene</option>
                  <option value="other">Other Supplies</option>
                </select>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="urgentToggle"
                  checked={wishlistUrgent}
                  onChange={(e) => setWishlistUrgent(e.target.checked)}
                  className="accent-emerald-600 rounded"
                />
                <label htmlFor="urgentToggle" className="font-semibold text-slate-700 dark:text-slate-300">
                  Mark as High Urgency Need
                </label>
              </div>

              <div className="flex gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowWishlistModal(false)}
                  className="w-1/2 py-2 rounded-xl border border-slate-200 dark:border-slate-800 font-bold text-slate-600 dark:text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-1/2 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold shadow-md"
                >
                  Publish Wishlist
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
