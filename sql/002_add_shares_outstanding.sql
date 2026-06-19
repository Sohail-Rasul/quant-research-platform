/*
Migration: 002_add_shares_outstanding.sql

Purpose:
Add shares_outstanding to stocks table
*/ 

BEGIN;

ALTER TABLE stocks
ADD COLUMN shares_outstanding BIGINT;

COMMIT;