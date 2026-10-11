"use client";

import React from "react";
import Link from "next/link";
import { HeartHandshake, ShieldCheck, Leaf, Globe2, PhoneCall, Sparkles } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">

          <div className="md:col-span-1 space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white">
                <HeartHandshake className="w-5 h-5" />
              </div>
              <span className="font-extrabold text-base tracking-tight text-slate-900 dark:text-white">
                Save The Serve
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              AI &amp; PostGIS geospatial routing bridging food surplus, essential relief goods, and frontline NGO networks with zero-waste speed.
            </p>
            <div className="flex items-center gap-3 pt-2">
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 px-2.5 py-1 rounded-md border border-emerald-200 dark:border-emerald-800">
                <Leaf className="w-3.5 h-3.5" />
                ESG Certified 100%
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-950/60 px-2.5 py-1 rounded-md border border-blue-200 dark:border-blue-800">
                <ShieldCheck className="w-3.5 h-3.5" />
                PostGIS ST_DWithin
              </span>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3">
              Role Sub-Portals
            </h4>
            <ul className="space-y-2 text-xs font-medium text-slate-600 dark:text-slate-400">
              <li>
                <Link href="/donor" className="hover:text-emerald-600 transition-colors">
                  Donor Hub &amp; ESG Tracker
                </Link>
              </li>
              <li>
                <Link href="/ngo" className="hover:text-emerald-600 transition-colors">
                  NGO Command &amp; Live Rescue Feed
                </Link>
              </li>
              <li>
                <Link href="/driver" className="hover:text-emerald-600 transition-colors">
                  Driver Fleet &amp; Handshake Verification
                </Link>
              </li>
              <li>
                <Link href="/auth" className="hover:text-emerald-600 transition-colors">
                  Role Authentication &amp; Onboarding
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3">
              Shared Utilities
            </h4>
            <ul className="space-y-2 text-xs font-medium text-slate-600 dark:text-slate-400">
              <li>
                <Link href="/directory" className="hover:text-emerald-600 transition-colors">
                  Verified NGO Directory
                </Link>
              </li>
              <li>
                <Link href="/help" className="hover:text-emerald-600 transition-colors">
                  Support Ticket Desk
                </Link>
              </li>
              <li>
                <Link href="/settings" className="hover:text-emerald-600 transition-colors">
                  Notification &amp; Proximity Settings
                </Link>
              </li>
            </ul>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-900 dark:text-white">
              <PhoneCall className="w-3.5 h-3.5 text-emerald-600" />
              <span>Surplus Escalation Hotline</span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Perishable food rescue under 2 hours urgency: Direct dispatch helpline.
            </p>
            <div className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400">
              +1 (800) STS-FOOD (787-3663)
            </div>
            <div className="text-[10px] text-slate-400 flex items-center gap-1 pt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping inline-block" />
              <span>Matching Engine: 24/7 Radius Polling</span>
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-200/80 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-4">
          <p>© 2026 Save The Serve (S.T.S). All rights reserved. Open API &amp; PostGIS Geo-routing.</p>
          <div className="flex gap-4">
            <span className="hover:underline cursor-pointer">Security Whitepaper</span>
            <span className="hover:underline cursor-pointer">Food Safety Guidelines</span>
            <span className="hover:underline cursor-pointer">PostGIS ST_Distance Docs</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
