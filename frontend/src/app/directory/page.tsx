"use client";

import React, { useState } from "react";
import { useApp } from "@/context/AppContext";
import { DonationCategory } from "@/lib/types";
import {
  Compass,
  Search,
  MapPin,
  Phone,
  Mail,
  ShieldCheck,
  Building2,
  CheckCircle2,
  Heart,
  DollarSign,
  Radio,
  Sliders,
  ExternalLink,
  Sparkles,
} from "lucide-react";

export default function NGODirectoryPage() {
  const { ngos, fundWishlistItem } = useApp();

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [activeOnly, setActiveOnly] = useState(false);
  const [sponsorshipNotice, setSponsorshipNotice] = useState<string | null>(null);

  const [selectedWishlistId, setSelectedWishlistId] = useState<string | null>(null);
  const [donateUnits, setDonateUnits] = useState(5);

  const handleFund = (wishlistId: string, itemTitle: string, unitCost: number) => {
    fundWishlistItem(wishlistId, donateUnits);
    setSelectedWishlistId(null);
    setSponsorshipNotice(
      `Thank you! You successfully sponsored ${donateUnits} units of "${itemTitle}" ($${donateUnits * unitCost}). Receipt logged to your profile.`
    );
  };

  const filteredNgos = ngos.filter((ngo) => {
    const matchesSearch =
      ngo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ngo.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ngo.mission.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      selectedCategory === "all" ||
      ngo.accepted_categories.includes(selectedCategory as DonationCategory);

    const matchesActive = !activeOnly || ngo.intake_capacity_active;

    return matchesSearch && matchesCategory && matchesActive;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

      <div className="rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 sm:p-8 shadow-xl border border-indigo-800/40 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-2xl space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
            <Compass className="w-3.5 h-3.5" />
            <span>Public Verified Relief Network</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
            NGO &amp; Community Shelter Directory
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Locate verified food banks, disaster relief centers, and homeless shelters. Inspect their real-time intake capacity, accepted surplus categories, and urgent wishlists.
          </p>
        </div>
      </div>

      {sponsorshipNotice && (
        <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/80 border border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200 text-xs sm:text-sm font-bold flex items-center justify-between gap-3 animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{sponsorshipNotice}</span>
          </div>
          <button
            onClick={() => setSponsorshipNotice(null)}
            className="text-emerald-700 hover:text-emerald-900 font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-4 sm:p-6 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3">

          <div className="md:col-span-6 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by NGO name, city, or mission focus..."
              className="w-full pl-9 pr-3 py-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="md:col-span-3">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full py-2.5 px-3 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All Accepted Categories</option>
              <option value="cooked_food">Cooked Food</option>
              <option value="clothes">Clothes &amp; Apparel</option>
              <option value="blankets">Blankets &amp; Bedding</option>
              <option value="medical">Medical &amp; First Aid</option>
              <option value="earmarked_money">Earmarked Money</option>
            </select>
          </div>

          <div className="md:col-span-3 flex items-center gap-2 pl-1">
            <input
              type="checkbox"
              id="activeIntakeOnly"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              className="accent-indigo-600 rounded"
            />
            <label
              htmlFor="activeIntakeOnly"
              className="text-xs font-bold text-slate-700 dark:text-slate-300 cursor-pointer"
            >
              Active Intake Capacity Only
            </label>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredNgos.length === 0 ? (
          <div className="col-span-2 text-center py-16 text-slate-400 text-xs">
            No registered NGOs match your search criteria.
          </div>
        ) : (
          filteredNgos.map((ngo) => (
            <div
              key={ngo.id}
              className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">

                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                        {ngo.name}
                      </h3>
                      {ngo.verified && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 flex items-center gap-1">
                          <ShieldCheck className="w-3 h-3 text-blue-600" />
                          <span>Verified</span>
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 font-medium">{ngo.registration_number}</p>
                  </div>

                  <span
                    className={`text-[10px] font-black uppercase px-2.5 py-1 rounded-full shrink-0 flex items-center gap-1.5 ${
                      ngo.intake_capacity_active
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800"
                        : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-300 dark:border-rose-800"
                    }`}
                  >
                    <span
                      className={`w-2 h-2 rounded-full ${
                        ngo.intake_capacity_active ? "bg-emerald-600 animate-ping" : "bg-rose-600"
                      }`}
                    />
                    <span>{ngo.intake_capacity_active ? "Intake Active" : "Capacity Full"}</span>
                  </span>
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  {ngo.mission}
                </p>

                <div className="flex flex-wrap gap-1.5 pt-1">
                  {ngo.accepted_categories.map((cat) => (
                    <span
                      key={cat}
                      className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 capitalize"
                    >
                      {cat.replace("_", " ")}
                    </span>
                  ))}
                </div>

                <div className="space-y-1.5 pt-2 text-xs text-slate-600 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{ngo.address}, {ngo.city}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <a href={`tel:${ngo.phone}`} className="hover:underline text-indigo-600 dark:text-indigo-400 font-mono">
                      {ngo.phone}
                    </a>
                  </div>
                  <div className="flex items-center gap-2">
                    <Mail className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <a href={`mailto:${ngo.contact_email}`} className="hover:underline">
                      {ngo.contact_email}
                    </a>
                  </div>
                </div>

                {ngo.wishlists && ngo.wishlists.length > 0 && (
                  <div className="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      Active Sponsorship Wishlist:
                    </span>
                    <div className="space-y-2">
                      {ngo.wishlists.map((w) => (
                        <div
                          key={w.id}
                          className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 flex items-center justify-between gap-2"
                        >
                          <div>
                            <div className="text-xs font-bold text-slate-900 dark:text-white">
                              {w.title}
                            </div>
                            <div className="text-[11px] text-slate-500">
                              ${w.unit_cost} / unit &bull; {w.funded_count}/{w.target_count} funded
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => setSelectedWishlistId(w.id)}
                            className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shrink-0 shadow-sm"
                          >
                            Fund Units
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-2 flex items-center justify-between text-xs text-slate-500">
                <span>Coverage: <strong>{ngo.operating_radius_km} km radius</strong></span>
                <span className="text-indigo-600 dark:text-indigo-400 font-bold hover:underline cursor-pointer">
                  View Full Profile &rarr;
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {selectedWishlistId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 w-full max-w-sm space-y-4 text-xs">
            <h3 className="text-base font-black text-slate-900 dark:text-white">
              Sponsor Shelter Wishlist Item
            </h3>
            <p className="text-slate-500">
              Select how many units you wish to sponsor for direct delivery.
            </p>

            <div className="space-y-2">
              <label className="block font-bold text-slate-700 dark:text-slate-300">
                Quantity of Units:
              </label>
              <div className="flex gap-2">
                {[5, 10, 20, 50].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setDonateUnits(num)}
                    className={`flex-1 py-2 rounded-xl font-bold border transition-all ${
                      donateUnits === num
                        ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                        : "border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300"
                    }`}
                  >
                    {num} units
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-2 pt-3">
              <button
                type="button"
                onClick={() => setSelectedWishlistId(null)}
                className="w-1/2 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 font-bold text-slate-600"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleFund(selectedWishlistId, "Wishlist Item", 15)}
                className="w-1/2 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold shadow-md"
              >
                Confirm Sponsorship
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
