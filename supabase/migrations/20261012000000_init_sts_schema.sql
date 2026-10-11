CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM (
        'donor',
        'ngo',
        'driver',
        'admin'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE donation_kind AS ENUM (
        'physical_item',
        'monetary_direct',
        'monetary_earmarked'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE item_category AS ENUM (
        'cooked_food',
        'grocery',
        'clothes',
        'blanket',
        'medical',
        'other'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE donation_status AS ENUM (
        'pending',
        'available',
        'reserved',
        'in_transit',
        'delivered',
        'completed',
        'cancelled',
        'expired'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE delivery_status AS ENUM (
        'assigned',
        'accepted',
        'picked_up',
        'in_transit',
        'delivered',
        'failed',
        'cancelled'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ticket_priority AS ENUM (
        'low',
        'medium',
        'high',
        'urgent'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ticket_status AS ENUM (
        'open',
        'in_progress',
        'resolved',
        'closed'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CLOCK_TIMESTAMP();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SCHEMA IF NOT EXISTS auth;
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid() REFERENCES auth.users(id) ON DELETE CASCADE,
    role user_role NOT NULL DEFAULT 'donor',
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password TEXT,
    phone_number VARCHAR(25),
    avatar_url TEXT,
    address_line TEXT,
    location GEOGRAPHY(POINT, 4326),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT chk_phone_format CHECK (phone_number IS NULL OR phone_number ~* '^\+?[0-9\s\-]{7,20}$')
);

CREATE TRIGGER trg_profiles_updated_at
BEFORE UPDATE ON profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS ngo_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
    organization_name VARCHAR(255) NOT NULL,
    registration_number VARCHAR(100) NOT NULL UNIQUE,
    tax_exemption_number VARCHAR(100),
    operating_radius_km NUMERIC(6, 2) NOT NULL DEFAULT 25.00 CHECK (operating_radius_km > 0),
    hq_location GEOGRAPHY(POINT, 4326) NOT NULL,
    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
    website_url TEXT,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(25) NOT NULL,
    capacity_description TEXT,
    verification_documents JSONB DEFAULT '[]'::jsonb,
    bank_account_info JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_ngo_details_updated_at
BEFORE UPDATE ON ngo_details
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS donations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    assigned_ngo_id UUID REFERENCES ngo_details(id) ON DELETE SET NULL,
    kind donation_kind NOT NULL DEFAULT 'physical_item',
    category item_category,
    status donation_status NOT NULL DEFAULT 'pending',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    quantity_amount NUMERIC(12, 2) NOT NULL CHECK (quantity_amount > 0),
    quantity_unit VARCHAR(50),
    monetary_currency VARCHAR(3) DEFAULT 'USD',
    earmarked_cause TEXT,
    pickup_address TEXT,
    pickup_location GEOGRAPHY(POINT, 4326),
    pickup_window_start TIMESTAMPTZ,
    pickup_window_end TIMESTAMPTZ,
    is_perishable BOOLEAN NOT NULL DEFAULT FALSE,
    prepared_at TIMESTAMPTZ,
    expiry_time TIMESTAMPTZ,
    reserved_until TIMESTAMPTZ,
    dietary_tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    image_urls TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_physical_donation_requirements CHECK (
        (kind != 'physical_item') OR
        (category IS NOT NULL AND pickup_location IS NOT NULL AND quantity_unit IS NOT NULL)
    ),
    CONSTRAINT chk_monetary_currency CHECK (
        (kind = 'physical_item') OR
        (monetary_currency IS NOT NULL AND LENGTH(monetary_currency) = 3)
    ),
    CONSTRAINT chk_pickup_window CHECK (
        pickup_window_start IS NULL OR
        pickup_window_end IS NULL OR
        pickup_window_end >= pickup_window_start
    ),
    CONSTRAINT chk_perishable_expiry CHECK (
        (NOT is_perishable) OR (expiry_time IS NOT NULL)
    )
);

CREATE TRIGGER trg_donations_updated_at
BEFORE UPDATE ON donations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donation_id UUID NOT NULL UNIQUE REFERENCES donations(id) ON DELETE CASCADE,
    driver_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    destination_ngo_id UUID NOT NULL REFERENCES ngo_details(id) ON DELETE RESTRICT,
    status delivery_status NOT NULL DEFAULT 'assigned',
    pickup_location GEOGRAPHY(POINT, 4326) NOT NULL,
    dropoff_location GEOGRAPHY(POINT, 4326) NOT NULL,
    current_driver_location GEOGRAPHY(POINT, 4326),
    proof_of_pickup_url TEXT,
    proof_of_delivery_url TEXT,
    pickup_otp_hash TEXT,
    delivery_otp_hash TEXT,
    estimated_distance_km NUMERIC(8, 2) CHECK (estimated_distance_km IS NULL OR estimated_distance_km >= 0),
    estimated_duration_mins INT CHECK (estimated_duration_mins IS NULL OR estimated_duration_mins >= 0),
    picked_up_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_delivery_timeline CHECK (
        delivered_at IS NULL OR picked_up_at IS NULL OR delivered_at >= picked_up_at
    )
);

CREATE TRIGGER trg_deliveries_updated_at
BEFORE UPDATE ON deliveries
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    assigned_agent_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    related_donation_id UUID REFERENCES donations(id) ON DELETE SET NULL,
    related_delivery_id UUID REFERENCES deliveries(id) ON DELETE SET NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    priority ticket_priority NOT NULL DEFAULT 'medium',
    status ticket_status NOT NULL DEFAULT 'open',
    resolution_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_support_tickets_updated_at
BEFORE UPDATE ON support_tickets
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_profiles_location_gist
    ON profiles USING GIST (location);

CREATE INDEX IF NOT EXISTS idx_ngo_details_hq_location_gist
    ON ngo_details USING GIST (hq_location);

CREATE INDEX IF NOT EXISTS idx_donations_pickup_location_gist
    ON donations USING GIST (pickup_location);

CREATE INDEX IF NOT EXISTS idx_deliveries_pickup_location_gist
    ON deliveries USING GIST (pickup_location);

CREATE INDEX IF NOT EXISTS idx_deliveries_dropoff_location_gist
    ON deliveries USING GIST (dropoff_location);

CREATE INDEX IF NOT EXISTS idx_deliveries_driver_location_gist
    ON deliveries USING GIST (current_driver_location);

CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles (role);
CREATE INDEX IF NOT EXISTS idx_ngo_details_profile_id ON ngo_details (profile_id);
CREATE INDEX IF NOT EXISTS idx_ngo_details_is_approved ON ngo_details (is_approved);

CREATE INDEX IF NOT EXISTS idx_donations_donor_id ON donations (donor_id);
CREATE INDEX IF NOT EXISTS idx_donations_assigned_ngo_id ON donations (assigned_ngo_id);
CREATE INDEX IF NOT EXISTS idx_donations_status ON donations (status);
CREATE INDEX IF NOT EXISTS idx_donations_kind_status ON donations (kind, status);
CREATE INDEX IF NOT EXISTS idx_donations_expiry_time ON donations (expiry_time) WHERE status = 'available';

CREATE INDEX IF NOT EXISTS idx_deliveries_donation_id ON deliveries (donation_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_driver_id ON deliveries (driver_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_destination_ngo_id ON deliveries (destination_ngo_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries (status);

CREATE INDEX IF NOT EXISTS idx_support_tickets_creator_id ON support_tickets (creator_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_assigned_agent ON support_tickets (assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status_priority ON support_tickets (status, priority);

CREATE OR REPLACE FUNCTION get_available_donations_within_radius(
    center_lon DOUBLE PRECISION,
    center_lat DOUBLE PRECISION,
    radius_meters DOUBLE PRECISION DEFAULT 25000
)
RETURNS TABLE (
    donation_id UUID,
    title VARCHAR,
    category item_category,
    quantity_amount NUMERIC,
    quantity_unit VARCHAR,
    distance_meters DOUBLE PRECISION,
    pickup_location GEOGRAPHY,
    pickup_address TEXT,
    expiry_time TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id AS donation_id,
        d.title,
        d.category,
        d.quantity_amount,
        d.quantity_unit,
        ST_Distance(d.pickup_location, ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography) AS distance_meters,
        d.pickup_location,
        d.pickup_address,
        d.expiry_time
    FROM donations d
    WHERE d.status = 'available'
      AND d.pickup_location IS NOT NULL
      AND ST_DWithin(d.pickup_location, ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography, radius_meters)
    ORDER BY distance_meters ASC;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_nearby_approved_ngos(
    user_lon DOUBLE PRECISION,
    user_lat DOUBLE PRECISION,
    max_search_meters DOUBLE PRECISION DEFAULT 50000
)
RETURNS TABLE (
    ngo_id UUID,
    organization_name VARCHAR,
    operating_radius_km NUMERIC,
    distance_meters DOUBLE PRECISION,
    contact_phone VARCHAR,
    contact_email VARCHAR,
    hq_location GEOGRAPHY
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id AS ngo_id,
        n.organization_name,
        n.operating_radius_km,
        ST_Distance(n.hq_location, ST_SetSRID(ST_MakePoint(user_lon, user_lat), 4326)::geography) AS distance_meters,
        n.contact_phone,
        n.contact_email,
        n.hq_location
    FROM ngo_details n
    WHERE n.is_approved = TRUE
      AND ST_DWithin(n.hq_location, ST_SetSRID(ST_MakePoint(user_lon, user_lat), 4326)::geography, max_search_meters)
    ORDER BY distance_meters ASC;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM profiles
        WHERE id = auth.uid() AND role = 'admin'
    );
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.get_current_role()
RETURNS user_role AS $$
DECLARE
    u_role user_role;
BEGIN
    SELECT role INTO u_role FROM profiles WHERE id = auth.uid();
    RETURN u_role;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE ngo_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE donations ENABLE ROW LEVEL SECURITY;
ALTER TABLE deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_policy"
ON profiles FOR SELECT
USING (
    auth.uid() = id
    OR is_admin()
    OR id IN (SELECT profile_id FROM ngo_details WHERE is_approved = TRUE)
);

CREATE POLICY "profiles_insert_policy"
ON profiles FOR INSERT
WITH CHECK (
    auth.uid() = id
);

CREATE POLICY "profiles_update_policy"
ON profiles FOR UPDATE
USING (
    auth.uid() = id OR is_admin()
)
WITH CHECK (
    auth.uid() = id OR is_admin()
);

CREATE POLICY "profiles_delete_policy"
ON profiles FOR DELETE
USING (
    auth.uid() = id OR is_admin()
);

CREATE POLICY "ngo_details_select_public_approved"
ON ngo_details FOR SELECT
USING (
    is_approved = TRUE
    OR profile_id = auth.uid()
    OR is_admin()
);

CREATE POLICY "ngo_details_insert_owner"
ON ngo_details FOR INSERT
WITH CHECK (
    profile_id = auth.uid()
);

CREATE POLICY "ngo_details_update_owner_or_admin"
ON ngo_details FOR UPDATE
USING (
    profile_id = auth.uid() OR is_admin()
)
WITH CHECK (

    (profile_id = auth.uid() AND is_approved = (SELECT n.is_approved FROM ngo_details n WHERE n.id = ngo_details.id))
    OR is_admin()
);

CREATE POLICY "ngo_details_delete_owner_or_admin"
ON ngo_details FOR DELETE
USING (
    profile_id = auth.uid() OR is_admin()
);

CREATE POLICY "donations_select_policy"
ON donations FOR SELECT
USING (
    donor_id = auth.uid()
    OR status = 'available'
    OR assigned_ngo_id IN (SELECT id FROM ngo_details WHERE profile_id = auth.uid())
    OR id IN (SELECT donation_id FROM deliveries WHERE driver_id = auth.uid())
    OR is_admin()
);

CREATE POLICY "donations_insert_donor"
ON donations FOR INSERT
WITH CHECK (
    donor_id = auth.uid()
);

CREATE POLICY "donations_update_policy"
ON donations FOR UPDATE
USING (
    (donor_id = auth.uid() AND status IN ('pending', 'available'))
    OR assigned_ngo_id IN (SELECT id FROM ngo_details WHERE profile_id = auth.uid())
    OR is_admin()
)
WITH CHECK (
    donor_id = auth.uid()
    OR assigned_ngo_id IN (SELECT id FROM ngo_details WHERE profile_id = auth.uid())
    OR is_admin()
);

CREATE POLICY "donations_delete_policy"
ON donations FOR DELETE
USING (
    (donor_id = auth.uid() AND status = 'pending')
    OR is_admin()
);

CREATE POLICY "deliveries_select_policy"
ON deliveries FOR SELECT
USING (
    driver_id = auth.uid()
    OR destination_ngo_id IN (SELECT id FROM ngo_details WHERE profile_id = auth.uid())
    OR donation_id IN (SELECT id FROM donations WHERE donor_id = auth.uid())
    OR is_admin()
);

CREATE POLICY "deliveries_insert_ngo_or_admin"
ON deliveries FOR INSERT
WITH CHECK (
    destination_ngo_id IN (SELECT id FROM ngo_details WHERE profile_id = auth.uid())
    OR is_admin()
);

CREATE POLICY "deliveries_update_policy"
ON deliveries FOR UPDATE
USING (
    driver_id = auth.uid()
    OR destination_ngo_id IN (SELECT id FROM ngo_details WHERE profile_id = auth.uid())
    OR is_admin()
)
WITH CHECK (
    driver_id = auth.uid()
    OR destination_ngo_id IN (SELECT id FROM ngo_details WHERE profile_id = auth.uid())
    OR is_admin()
);

CREATE POLICY "deliveries_delete_admin"
ON deliveries FOR DELETE
USING (
    is_admin()
);

CREATE POLICY "support_tickets_select_policy"
ON support_tickets FOR SELECT
USING (
    creator_id = auth.uid()
    OR assigned_agent_id = auth.uid()
    OR is_admin()
);

CREATE POLICY "support_tickets_insert_creator"
ON support_tickets FOR INSERT
WITH CHECK (
    creator_id = auth.uid()
);

CREATE POLICY "support_tickets_update_policy"
ON support_tickets FOR UPDATE
USING (
    (creator_id = auth.uid() AND status = 'open')
    OR assigned_agent_id = auth.uid()
    OR is_admin()
)
WITH CHECK (
    (creator_id = auth.uid() AND status = 'open')
    OR assigned_agent_id = auth.uid()
    OR is_admin()
);

CREATE POLICY "support_tickets_delete_admin"
ON support_tickets FOR DELETE
USING (
    is_admin()
);
