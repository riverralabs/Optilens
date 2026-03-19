-- Migration: Add progress tracking columns to audits table
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New Query)
--
-- These columns allow the Supabase-fallback SSE path to report
-- granular progress instead of only 0/25/50/75/100%.

ALTER TABLE audits ADD COLUMN IF NOT EXISTS current_agent TEXT;
ALTER TABLE audits ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0;
