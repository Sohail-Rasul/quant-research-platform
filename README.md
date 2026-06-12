# ABOUT THE PROJECT

The Quantitative Research Platform is an end-to-end system for acquiring, storing, and maintaining market data for quantitative research. It uses Python ETL pipelines to ingest stock metadata and historical price data from Yahoo Finance into a PostgreSQL market data warehouse, supporting both one-time historical backfills and efficient incremental updates.

The broader goal of the project is to learn quantitative finance, backend engineering, data engineering, and system design by progressively building a complete research platform from first principles.

# Tech Stack

- Python
- PostgreSQL
- psycopg
- yfinance
- python-dotenv
- Git

# Current Status (M1 Complete)

The platform currently supports:

* Stock metadata ingestion
* Historical price backfills
* Incremental price updates
* Idempotent ETL pipelines
* PostgreSQL-based storage
* Data validation and quality checks

Future modules will extend the system with factor research, backtesting, portfolio analytics, experiment tracking, APIs, and deployment capabilities.

# Setup

## 1. Clone the Repository

```bash
git clone <repository-url>
cd quant-research-platform
```

## 2. Create and Activate a Virtual Environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Create the PostgreSQL Database

Create a PostgreSQL database named:

```text
quant_research_platform
```

Example local configuration:

```text
Host: localhost
Port: 5432
Database: quant_research_platform
User: postgres
```

## 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quant_research_platform
DB_USER=postgres
DB_PASSWORD=your_password_here
```

## 6. Create the Database Schema

Run the SQL migration file to create the required tables.

This migration creates:

* `stocks`
* `prices`

# Repository Structure

```text
quant-research-platform/
│
├── app/          # Reusable application logic
├── scripts/      # Executable ETL workflows
├── notebooks/    # Research and exploration
├── tests/        # Testing and validation
├── docs/         # Documentation
│
├── requirements.txt
├── .env
└── README.md
```

Folder Responsibilities:

* `app/` contains reusable code shared across the project.
* `scripts/` contains executable workflows such as metadata ingestion, historical backfills, and incremental updates.
* `notebooks/` are used for experimentation and exploratory analysis.
* `tests/` contains validation and testing artifacts.
* `docs/` stores architecture notes and supporting documentation.

# Script Usage

## ingest_metadata.py

Purpose:

Populate the `stocks` table using Yahoo Finance metadata.

Usage:

```bash
python scripts/ingest_metadata.py
```

---

## backfill_prices.py

Purpose:

Perform a one-time historical backfill of daily price data.

Features:

* Bulk inserts
* Idempotent loading
* Historical initialization

Usage:

```bash
python scripts/backfill_prices.py
```

---

## update_prices.py

Purpose:

Load only new price observations after the latest stored trading date.

Features:

* Incremental updates
* Reuse of ETL logic
* Safe reruns using conflict handling

Usage:

```bash
python scripts/update_prices.py
```

# Database Schema

## stocks

Stores stock metadata.

| Column       | Description                 |
| ------------ | --------------------------- |
| stock_id     | Primary key                 |
| ticker       | Yahoo Finance ticker symbol |
| company_name | Formal company name         |
| created_at   | Record creation timestamp   |

---

## prices

Stores daily historical price observations.

| Column    | Description             |
| --------- | ----------------------- |
| stock_id  | Foreign key to `stocks` |
| date      | Trading date            |
| open      | Opening price           |
| high      | Highest price           |
| low       | Lowest price            |
| close     | Closing price           |
| adj_close | Adjusted closing price  |
| volume    | Trading volume          |

Relationship:

```text
One stock
↓
Many price observations
```

