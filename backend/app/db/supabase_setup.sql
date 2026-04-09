-- supabase_setup.sql
-- Run once in Supabase SQL editor — only needed for lead capture table

CREATE TABLE IF NOT EXISTS chat_leads (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name             text NOT NULL,
    email            text NOT NULL,
    company          text NOT NULL,
    role             text,
    industry         text,
    phone            text,
    chat_transcript  jsonb  DEFAULT '[]',
    buying_signals   text[] DEFAULT '{}',
    utm_source       text,
    utm_medium       text,
    utm_campaign     text,
    session_id       text,
    status           text DEFAULT 'new',
    notes            text,
    created_at       timestamptz DEFAULT now()
);
