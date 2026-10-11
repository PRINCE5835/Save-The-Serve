"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import {
  DonationItem,
  NGODirectoryItem,
  DeliveryMission,
  SupportTicket,
  WishlistItem,
  DonationCategory,
} from "@/lib/types";
import {
  initialDonations,
  initialNGOs,
  initialDeliveries,
  initialTickets,
} from "@/lib/mock-data";

interface AppContextType {
  donations: DonationItem[];
  ngos: NGODirectoryItem[];
  deliveries: DeliveryMission[];
  tickets: SupportTicket[];
  createDonation: (donation: Omit<DonationItem, "id" | "created_at" | "pickup_otp" | "dropoff_otp" | "status">) => DonationItem;
  claimDonationByNGO: (donationId: string, ngoId: string, ngoName: string) => boolean;
  toggleNGOCapacity: (ngoId: string, active: boolean) => void;
  createWishlistItem: (ngoId: string, item: Omit<WishlistItem, "id" | "ngo_id" | "ngo_name" | "funded_count" | "created_at">) => void;
  fundWishlistItem: (wishlistId: string, amountUnits: number) => void;
  claimDeliveryMission: (deliveryId: string, driverId: string, driverName: string) => boolean;
  verifyPickupOTP: (deliveryId: string, otp: string) => { success: boolean; message: string };
  verifyDropoffOTP: (deliveryId: string, otp: string, proofImageUrl?: string) => { success: boolean; message: string };
  createSupportTicket: (ticket: Omit<SupportTicket, "id" | "created_at" | "status">) => SupportTicket;
  esgStats: {
    mealsSaved: number;
    co2KgPrevented: number;
    activeDrivers: number;
    activePartners: number;
  };
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [donations, setDonations] = useState<DonationItem[]>(initialDonations);
  const [ngos, setNgos] = useState<NGODirectoryItem[]>(initialNGOs);
  const [deliveries, setDeliveries] = useState<DeliveryMission[]>(initialDeliveries);
  const [tickets, setTickets] = useState<SupportTicket[]>(initialTickets);

  useEffect(() => {
    try {
      const savedDonations = localStorage.getItem("sts_donations");
      if (savedDonations) setDonations(JSON.parse(savedDonations));

      const savedNgos = localStorage.getItem("sts_ngos");
      if (savedNgos) setNgos(JSON.parse(savedNgos));

      const savedDeliveries = localStorage.getItem("sts_deliveries");
      if (savedDeliveries) setDeliveries(JSON.parse(savedDeliveries));

      const savedTickets = localStorage.getItem("sts_tickets");
      if (savedTickets) setTickets(JSON.parse(savedTickets));
    } catch (e) {
      console.warn("Local storage loading error", e);
    }
  }, []);

  const saveState = (
    newDonations?: DonationItem[],
    newNgos?: NGODirectoryItem[],
    newDeliveries?: DeliveryMission[],
    newTickets?: SupportTicket[]
  ) => {
    try {
      if (newDonations) localStorage.setItem("sts_donations", JSON.stringify(newDonations));
      if (newNgos) localStorage.setItem("sts_ngos", JSON.stringify(newNgos));
      if (newDeliveries) localStorage.setItem("sts_deliveries", JSON.stringify(newDeliveries));
      if (newTickets) localStorage.setItem("sts_tickets", JSON.stringify(newTickets));
    } catch (e) {}
  };

  const createDonation = (
    data: Omit<DonationItem, "id" | "created_at" | "pickup_otp" | "dropoff_otp" | "status">
  ): DonationItem => {
    const pickupOtp = Math.floor(100000 + Math.random() * 900000).toString();
    const dropoffOtp = Math.floor(100000 + Math.random() * 900000).toString();

    const newDonation: DonationItem = {
      ...data,
      id: `don_${Date.now()}`,
      status: "open",
      pickup_otp: pickupOtp,
      dropoff_otp: dropoffOtp,
      created_at: new Date().toISOString(),
    };

    const updatedDonations = [newDonation, ...donations];
    setDonations(updatedDonations);
    saveState(updatedDonations);

    if (data.category !== "earmarked_money") {
      const newDelivery: DeliveryMission = {
        id: `del_${Date.now()}`,
        donation_id: newDonation.id,
        donation_title: newDonation.title,
        category: newDonation.category,
        donor_name: newDonation.donor_name,
        donor_address: newDonation.pickup_address,
        donor_phone: newDonation.donor_phone,
        ngo_name: "Pending NGO Claim",
        ngo_address: "Awaiting Claim",
        ngo_phone: "+1 (555) 000-0000",
        distance_km: parseFloat((Math.random() * 4 + 1.5).toFixed(1)),
        est_minutes: Math.floor(Math.random() * 20 + 10),
        urgency: newDonation.urgency,
        status: "available",
        pickup_otp: pickupOtp,
        dropoff_otp: dropoffOtp,
        created_at: new Date().toISOString(),
      };
      const updatedDeliveries = [newDelivery, ...deliveries];
      setDeliveries(updatedDeliveries);
      saveState(undefined, undefined, updatedDeliveries);
    }

    return newDonation;
  };

  const claimDonationByNGO = (donationId: string, ngoId: string, ngoName: string): boolean => {
    const donation = donations.find((d) => d.id === donationId);
    if (!donation || donation.status !== "open") return false;

    const claimExpiry = new Date(Date.now() + 15 * 60 * 1000).toISOString();

    const updatedDonations = donations.map((d) =>
      d.id === donationId
        ? {
            ...d,
            status: "claimed" as const,
            claimed_by_ngo_id: ngoId,
            claimed_by_ngo_name: ngoName,
            claim_expires_at: claimExpiry,
          }
        : d
    );
    setDonations(updatedDonations);

    const targetNGO = ngos.find((n) => n.id === ngoId);
    const updatedDeliveries = deliveries.map((del) =>
      del.donation_id === donationId
        ? {
            ...del,
            ngo_name: ngoName,
            ngo_address: targetNGO ? targetNGO.address : "Central NGO Intake Dock",
            ngo_phone: targetNGO ? targetNGO.phone : "+1 (555) 891-2345",
          }
        : del
    );
    setDeliveries(updatedDeliveries);

    saveState(updatedDonations, undefined, updatedDeliveries);
    return true;
  };

  const toggleNGOCapacity = (ngoId: string, active: boolean) => {
    const updatedNgos = ngos.map((ngo) =>
      ngo.id === ngoId ? { ...ngo, intake_capacity_active: active } : ngo
    );
    setNgos(updatedNgos);
    saveState(undefined, updatedNgos);
  };

  const createWishlistItem = (
    ngoId: string,
    item: Omit<WishlistItem, "id" | "ngo_id" | "ngo_name" | "funded_count" | "created_at">
  ) => {
    const ngo = ngos.find((n) => n.id === ngoId);
    if (!ngo) return;

    const newWishlist: WishlistItem = {
      ...item,
      id: `wsh_${Date.now()}`,
      ngo_id: ngoId,
      ngo_name: ngo.name,
      funded_count: 0,
      created_at: new Date().toISOString(),
    };

    const updatedNgos = ngos.map((n) =>
      n.id === ngoId ? { ...n, wishlists: [newWishlist, ...n.wishlists] } : n
    );
    setNgos(updatedNgos);
    saveState(undefined, updatedNgos);
  };

  const fundWishlistItem = (wishlistId: string, amountUnits: number) => {
    const updatedNgos = ngos.map((ngo) => ({
      ...ngo,
      wishlists: ngo.wishlists.map((w) =>
        w.id === wishlistId
          ? { ...w, funded_count: Math.min(w.target_count, w.funded_count + amountUnits) }
          : w
      ),
    }));
    setNgos(updatedNgos);
    saveState(undefined, updatedNgos);
  };

  const claimDeliveryMission = (deliveryId: string, driverId: string, driverName: string): boolean => {
    const updatedDeliveries = deliveries.map((del) =>
      del.id === deliveryId
        ? {
            ...del,
            status: "claimed" as const,
            driver_id: driverId,
            driver_name: driverName,
          }
        : del
    );
    setDeliveries(updatedDeliveries);
    saveState(undefined, undefined, updatedDeliveries);
    return true;
  };

  const verifyPickupOTP = (deliveryId: string, otp: string) => {
    const delivery = deliveries.find((d) => d.id === deliveryId);
    if (!delivery) return { success: false, message: "Mission not found." };
    if (delivery.pickup_otp !== otp.trim()) {
      return { success: false, message: "Invalid donor 6-digit pickup OTP code." };
    }

    const updatedDeliveries = deliveries.map((d) =>
      d.id === deliveryId ? { ...d, status: "picked_up" as const } : d
    );
    setDeliveries(updatedDeliveries);

    const updatedDonations = donations.map((d) =>
      d.id === delivery.donation_id ? { ...d, status: "in_transit" as const } : d
    );
    setDonations(updatedDonations);

    saveState(updatedDonations, undefined, updatedDeliveries);
    return { success: true, message: "Pickup handshake verified! Items secured in vehicle." };
  };

  const verifyDropoffOTP = (deliveryId: string, otp: string, proofImageUrl?: string) => {
    const delivery = deliveries.find((d) => d.id === deliveryId);
    if (!delivery) return { success: false, message: "Mission not found." };
    if (delivery.dropoff_otp !== otp.trim()) {
      return { success: false, message: "Invalid NGO 6-digit dropoff OTP code." };
    }

    const updatedDeliveries = deliveries.map((d) =>
      d.id === deliveryId
        ? {
            ...d,
            status: "delivered" as const,
            proof_image_url: proofImageUrl || "https://images.unsplash.com/photo-1593113598332-cd288d649433?w=400&auto=format&fit=crop&q=80",
          }
        : d
    );
    setDeliveries(updatedDeliveries);

    const updatedDonations = donations.map((d) =>
      d.id === delivery.donation_id ? { ...d, status: "delivered" as const } : d
    );
    setDonations(updatedDonations);

    saveState(updatedDonations, undefined, updatedDeliveries);
    return { success: true, message: "Handoff complete! Proof logged and NGO intake updated." };
  };

  const createSupportTicket = (
    data: Omit<SupportTicket, "id" | "created_at" | "status">
  ): SupportTicket => {
    const newTicket: SupportTicket = {
      ...data,
      id: `tkt_${Date.now()}`,
      status: "open",
      created_at: new Date().toISOString(),
    };
    const updatedTickets = [newTicket, ...tickets];
    setTickets(updatedTickets);
    saveState(undefined, undefined, undefined, updatedTickets);
    return newTicket;
  };

  const esgStats = {
    mealsSaved: 14820 + donations.filter((d) => d.category === "cooked_food").length * 60,
    co2KgPrevented: 28450 + donations.length * 45,
    activeDrivers: 48,
    activePartners: ngos.length,
  };

  return (
    <AppContext.Provider
      value={{
        donations,
        ngos,
        deliveries,
        tickets,
        createDonation,
        claimDonationByNGO,
        toggleNGOCapacity,
        createWishlistItem,
        fundWishlistItem,
        claimDeliveryMission,
        verifyPickupOTP,
        verifyDropoffOTP,
        createSupportTicket,
        esgStats,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
}
