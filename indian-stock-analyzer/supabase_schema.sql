-- ============================================================
-- Indian Stock Analyzer — Supabase Schema
-- Run this in the Supabase SQL Editor (once)
-- ============================================================

-- ── Enable UUID extension (already enabled on Supabase by default) ──────────
-- create extension if not exists "uuid-ossp";


-- ── signals ─────────────────────────────────────────────────────────────────
-- Stores the latest calculated signal for each stock symbol (upserted on write)

create table if not exists signals (
  id          bigint generated always as identity primary key,
  symbol      text        not null unique,          -- e.g. "RELIANCE.NS"
  signal      text        not null default 'HOLD',  -- BUY / SELL / HOLD / STRONG BUY / STRONG SELL
  confidence  integer     not null default 0,        -- 0-100 integer %
  price       numeric(18,4),                         -- last traded price
  reasons     jsonb       default '[]'::jsonb,       -- array of reason strings
  risk_flags  jsonb       default '[]'::jsonb,       -- array of risk flag strings
  data_status text        not null default 'OK',     -- OK | PARTIAL | FALLBACK
  created_at  timestamptz not null default now()
);

-- Index for fast dashboard queries
create index if not exists signals_signal_idx    on signals (signal);
create index if not exists signals_created_idx   on signals (created_at desc);


-- ── alerts ───────────────────────────────────────────────────────────────────
-- Immutable audit log — every BUY/SELL alert that was dispatched

create table if not exists alerts (
  id          bigint generated always as identity primary key,
  symbol      text        not null,
  signal      text        not null,
  price       numeric(18,4),
  confidence  integer     default 0,
  sent_at     timestamptz not null default now()
);

create index if not exists alerts_symbol_idx  on alerts (symbol);
create index if not exists alerts_sent_at_idx on alerts (sent_at desc);


-- ── watchlist ─────────────────────────────────────────────────────────────────
-- User-managed list of tracked symbols

create table if not exists watchlist (
  id        bigint generated always as identity primary key,
  symbol    text        not null unique,
  added_at  timestamptz not null default now()
);


-- ── Row Level Security ────────────────────────────────────────────────────────
-- The backend connects with the SECRET key (bypasses RLS).
-- Optionally enable for frontend anon reads:

-- alter table signals   enable row level security;
-- alter table alerts    enable row level security;
-- alter table watchlist enable row level security;

-- Allow anonymous (frontend) read access:
-- create policy "Public read signals"   on signals   for select using (true);
-- create policy "Public read alerts"    on alerts    for select using (true);
-- create policy "Public read watchlist" on watchlist for select using (true);
