"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useApp } from "@/context/AppContext";
import { SupportTicket } from "@/lib/types";
import {
  LifeBuoy,
  MessageSquare,
  AlertTriangle,
  PhoneCall,
  CheckCircle2,
  Clock,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Send,
  ShieldCheck,
} from "lucide-react";

export default function HelpPage() {
  const { user } = useAuth();
  const { tickets, createSupportTicket } = useApp();

  const [subject, setSubject] = useState("");
  const [category, setCategory] = useState<"delivery" | "donation" | "ngo" | "technical" | "urgent">(
    "delivery"
  );
  const [priority, setPriority] = useState<"normal" | "high" | "urgent">("normal");
  const [description, setDescription] = useState("");
  const [ticketNotice, setTicketNotice] = useState<string | null>(null);

  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(0);

  const handleCreateTicket = (e: React.FormEvent) => {
    e.preventDefault();

    createSupportTicket({
      user_id: user?.id || "usr_guest",
      user_name: user?.name || "Guest User",
      user_role: user?.role || "donor",
      category,
      priority,
      subject,
      description,
    });

    setTicketNotice(`Support ticket "${subject}" submitted! Ticket ID has been assigned and queued for resolution.`);
    setSubject("");
    setDescription("");
  };

  const faqs = [
    {
      q: "How does the 6-Digit OTP Handshake verification work?",
      a: "When a donor registers a donation, S.T.S generates a secret 6-digit `pickup_otp`. The courier asks the donor for this code before loading items. When dropping off at an NGO, the intake coordinator provides a 6-digit `dropoff_otp` + image capture. Both sides are cryptographically verified to prevent missing surplus.",
    },
    {
      q: "What happens when cooked food has less than 2 hours before expiry?",
      a: "Our background perishable watchdog automatically flags the item with `CRITICAL_URGENCY`, doubles the notification search radius from 10km to 20km, and alerts active couriers immediately with audio/push priority.",
    },
    {
      q: "Can I donate monetary funds for specific items rather than physical food?",
      a: "Yes! Use the 'Earmarked Money' tab in the Donor Dashboard or browse the NGO Directory. You can sponsor tangible units like '50 Heavy Sleeping Bags @ $15/ea' directly.",
    },
    {
      q: "How do NGOs pause incoming donations if they reach capacity?",
      a: "In the NGO Dashboard, toggle the 'Intake Capacity' switch to 'INTAKE PAUSED (FULL)'. This instantly removes your shelter from proximity feed matching until you toggle it back on.",
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

      <div className="rounded-3xl bg-gradient-to-r from-slate-900 via-teal-950 to-slate-900 text-white p-6 sm:p-8 shadow-xl border border-teal-800/40 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-2xl space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/20 text-teal-300 border border-teal-400/30">
            <LifeBuoy className="w-3.5 h-3.5" />
            <span>24/7 Operations Desk</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
            Help &amp; Support Ticket Desk
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Need assistance with a delivery handshake, OTP code verification, or food safety guidelines? Submit a ticket or call our surplus dispatch hotline.
          </p>
        </div>
      </div>

      <div className="p-4 sm:p-5 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <PhoneCall className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-xs sm:text-sm font-bold text-amber-900 dark:text-amber-200">
              Immediate Surplus Rescue Emergency Hotline
            </h3>
            <p className="text-xs text-amber-800 dark:text-amber-300">
              For perishable food expiring in under 1 hour, bypass ticket queues and speak directly to live dispatchers.
            </p>
          </div>
        </div>
        <a
          href="tel:+18007873663"
          className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-mono font-bold text-xs shrink-0 shadow-sm"
        >
          Call: +1 (800) STS-FOOD
        </a>
      </div>

      {ticketNotice && (
        <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/80 border border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200 text-xs sm:text-sm font-bold flex items-center justify-between gap-3 animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{ticketNotice}</span>
          </div>
          <button onClick={() => setTicketNotice(null)} className="text-emerald-700 font-bold">
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 space-y-5">
            <div className="flex items-center gap-2 pb-4 border-b border-slate-100 dark:border-slate-800">
              <MessageSquare className="w-5 h-5 text-teal-600" />
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Submit Support or Dispatch Inquiry
              </h2>
            </div>

            <form onSubmit={handleCreateTicket} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Ticket Subject / Issue Summary
                </label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g. Courier unable to locate basement dock buzzer"
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
                  >
                    <option value="delivery">Delivery &amp; Transit</option>
                    <option value="donation">Surplus Donation Issue</option>
                    <option value="ngo">NGO Coordination</option>
                    <option value="technical">App / OTP Handshake</option>
                    <option value="urgent">Urgent Escalation</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Priority Level
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white"
                  >
                    <option value="normal">Normal Priority</option>
                    <option value="high">High Priority</option>
                    <option value="urgent">Urgent Priority</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Detailed Explanation
                </label>
                <textarea
                  rows={4}
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Please include mission ID, donor or NGO name, and specific address instructions..."
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="w-full py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-md shadow-teal-600/20 flex items-center justify-center gap-2 transition-all"
                >
                  <Send className="w-4 h-4" />
                  <span>Submit Ticket to Dispatch Ops</span>
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-teal-600" />
                <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                  Your Tickets &amp; Resolutions
                </h3>
              </div>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                {tickets.length} Total
              </span>
            </div>

            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {tickets.map((tkt) => (
                <div
                  key={tkt.id}
                  className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-700/60 space-y-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="text-xs font-bold text-slate-900 dark:text-white line-clamp-1">
                      {tkt.subject}
                    </h4>
                    <span
                      className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${
                        tkt.status === "resolved"
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                          : tkt.status === "in_progress"
                          ? "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
                          : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                      }`}
                    >
                      {tkt.status.replace("_", " ")}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2">
                    {tkt.description}
                  </p>

                  {tkt.response && (
                    <div className="p-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[11px] text-emerald-700 dark:text-emerald-400">
                      <strong>Dispatch Response:</strong> {tkt.response}
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                    <span className="capitalize">Category: {tkt.category}</span>
                    <span>{new Date(tkt.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-sm space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <HelpCircle className="w-5 h-5 text-teal-600" />
          <h2 className="text-base sm:text-lg font-black text-slate-900 dark:text-white">
            Frequently Asked Operations Questions
          </h2>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, idx) => {
            const isOpen = openFaqIndex === idx;
            return (
              <div
                key={idx}
                className="border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden transition-all"
              >
                <button
                  type="button"
                  onClick={() => setOpenFaqIndex(isOpen ? null : idx)}
                  className="w-full p-4 text-left flex items-center justify-between gap-4 font-bold text-xs sm:text-sm text-slate-900 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-800/50"
                >
                  <span>{faq.q}</span>
                  {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                </button>
                {isOpen && (
                  <div className="p-4 pt-0 text-xs text-slate-600 dark:text-slate-400 leading-relaxed border-t border-slate-100 dark:border-slate-800/80">
                    {faq.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
