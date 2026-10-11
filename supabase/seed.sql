INSERT INTO profiles (id, role, full_name, email, phone_number, is_verified, location)
VALUES
    ('a0000000-0000-0000-0000-000000000001', 'admin', 'System Administrator', 'admin@savetheserve.org', '+14155550100', true, ST_SetSRID(ST_MakePoint(-122.4194, 37.7749), 4326)::geography),
    ('b0000000-0000-0000-0000-000000000002', 'ngo', 'Hope Food Bank Director', 'contact@hopefoodbank.org', '+14155550102', true, ST_SetSRID(ST_MakePoint(-122.4089, 37.7833), 4326)::geography),
    ('c0000000-0000-0000-0000-000000000003', 'donor', 'The French Bakery & Bistro', 'manager@frenchbakerysf.com', '+14155550103', true, ST_SetSRID(ST_MakePoint(-122.4200, 37.7690), 4326)::geography),
    ('d0000000-0000-0000-0000-000000000004', 'driver', 'Alex Courier', 'alex.driver@stsrescue.org', '+14155550104', true, ST_SetSRID(ST_MakePoint(-122.4150, 37.7710), 4326)::geography)
ON CONFLICT (id) DO NOTHING;

INSERT INTO ngo_details (id, profile_id, organization_name, registration_number, tax_exemption_number, operating_radius_km, hq_location, is_approved, website_url, contact_email, contact_phone, capacity_description)
VALUES
    ('e0000000-0000-0000-0000-000000000005', 'b0000000-0000-0000-0000-000000000002', 'Hope Food Rescue Foundation', 'US-EIN-987654321', '501C3-ACTIVE', 35.0, ST_SetSRID(ST_MakePoint(-122.4089, 37.7833), 4326)::geography, true, 'https://hopefoodbank.org', 'contact@hopefoodbank.org', '+14155550102', 'Walk-in cold storage with 5,000 kg daily intake capacity.')
ON CONFLICT (id) DO NOTHING;

INSERT INTO donations (id, donor_id, kind, category, status, title, description, quantity_amount, quantity_unit, pickup_address, pickup_location, is_perishable, expiry_time, dietary_tags)
VALUES
    ('f0000000-0000-0000-0000-000000000006', 'c0000000-0000-0000-0000-000000000003', 'physical_item', 'cooked_food', 'available', '50 Fresh Artisan Baguettes & Croissants', 'Surplus from morning bake cycle, freshly packed in food-grade bakery boxes.', 50.00, 'servings', '550 Valencia St, San Francisco, CA', ST_SetSRID(ST_MakePoint(-122.4215, 37.7648), 4326)::geography, true, NOW() + INTERVAL '12 hours', ARRAY['vegetarian'])
ON CONFLICT (id) DO NOTHING;
