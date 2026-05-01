/**
 * supabaseClient.js
 * -----------------
 * Shared Supabase browser client for the Indian Stock Analyzer frontend.
 *
 * Uses the ANON (publishable) key — safe to expose in the browser.
 * All sensitive writes (signals, alerts) go through the FastAPI backend
 * which uses the secret key.
 *
 * Usage:
 *   import { supabase } from './supabaseClient'
 *   const { data, error } = await supabase.from('signals').select('*')
 */

import { createClient } from '@supabase/supabase-js'

const supabaseUrl  = import.meta.env.VITE_SUPABASE_URL
const supabaseAnon = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnon) {
  console.warn(
    '[Supabase] Missing env vars VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY. ' +
    'DB features will be disabled.'
  )
}

export const supabase = createClient(supabaseUrl ?? '', supabaseAnon ?? '')

// ── Convenience helpers ──────────────────────────────────────────────────────

/**
 * Fetch all signals ordered by most recent first.
 * @param {number} limit - Max rows to fetch (default 50)
 */
export async function fetchSignals(limit = 50) {
  const { data, error } = await supabase
    .from('signals')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(limit)

  if (error) {
    console.error('[Supabase] fetchSignals error:', error.message)
    return []
  }
  return data ?? []
}

/**
 * Fetch signal for a specific symbol.
 * @param {string} symbol - e.g. "RELIANCE.NS"
 */
export async function fetchSignalForSymbol(symbol) {
  const { data, error } = await supabase
    .from('signals')
    .select('*')
    .eq('symbol', symbol.toUpperCase())
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle()

  if (error) {
    console.error('[Supabase] fetchSignalForSymbol error:', error.message)
    return null
  }
  return data
}

/**
 * Fetch recent alert history.
 * @param {number} limit - Max rows to fetch (default 100)
 */
export async function fetchAlertHistory(limit = 100) {
  const { data, error } = await supabase
    .from('alerts')
    .select('*')
    .order('sent_at', { ascending: false })
    .limit(limit)

  if (error) {
    console.error('[Supabase] fetchAlertHistory error:', error.message)
    return []
  }
  return data ?? []
}

/**
 * Subscribe to realtime signal changes.
 * @param {Function} callback - called with the new row on INSERT/UPDATE
 * @returns Supabase RealtimeChannel (call .unsubscribe() on cleanup)
 */
export function subscribeToSignals(callback) {
  const channel = supabase
    .channel('signals-realtime')
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'signals' },
      (payload) => callback(payload.new)
    )
    .subscribe()

  return channel
}

/**
 * Subscribe to realtime alert events.
 * @param {Function} callback - called with the new row on INSERT
 * @returns Supabase RealtimeChannel
 */
export function subscribeToAlerts(callback) {
  const channel = supabase
    .channel('alerts-realtime')
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'alerts' },
      (payload) => callback(payload.new)
    )
    .subscribe()

  return channel
}
