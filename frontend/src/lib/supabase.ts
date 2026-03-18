import { createClient, type SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string || ''

/**
 * Returns true if Supabase env vars are configured.
 * Used to gate auth flows in dev when no Supabase project is connected yet.
 */
export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey)

// Create client with placeholder values if not configured — auth calls will
// fail gracefully rather than crashing the entire app on import.
export const supabase: SupabaseClient = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-key',
)
