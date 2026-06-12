/*
Migration: 001_create_tables.sql

Purpose:
Initial database schema for M1 Historical Data Platform.

Tables:
1. stocks
2. prices
*/

BEGIN;


CREATE TABLE stocks (
    stock_id BIGSERIAL PRIMARY KEY , -- Primary key implies not null
    ticker VARCHAR(20) unique NOT NULL,
    company_name TEXT NOT NULL, -- We use Text here as we do not know how long the company name might be 
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP -- Adds default timestamp (handled by SQL)
);

CREATE TABLE prices (
    stock_id BIGINT NOT NULL ,
    date date NOT NULL,

    open NUMERIC(12,4) NOT NULL CHECK (open>0),
    high NUMERIC(12,4) NOT NULL CHECK (high>0),
    low NUMERIC(12,4) NOT NULL CHECK (low>0),
    close NUMERIC(12,4) NOT NULL CHECK (close>0),
    adj_close NUMERIC(12,4) NOT NULL CHECK (adj_close>0),

    volume BIGINT NOT NULL CHECK (volume>=0),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (stock_id, date),
    
    FOREIGN KEY (stock_id) 
    REFERENCES stocks(stock_id) 
    ON DELETE RESTRICT,

    CHECK (
    high >= low
    AND high >= open
    AND high >= close
    AND low <= open
    AND low <= close
    )
);


COMMIT;