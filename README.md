# Enterprise Data Migration & Intelligent Data Quality Monitoring Platform

## Overview

The Enterprise Data Migration & Intelligent Data Quality Monitoring Platform is a Python-based academic project designed to support transaction data migration, automated data quality validation, anomaly detection, and migration monitoring.

The platform provides a Streamlit dashboard to inspect datasets, identify data quality issues, explore unusual transactions, and review migration results.

## Key Features

- **Data ingestion:** Reads transaction data from CSV files and supports PostgreSQL connectivity.
- **Data transformation:** Uses Pandas to standardize transaction identifiers, payment methods, numeric amounts, and dates.
- **Data quality validation:** Detects missing values, duplicate transaction IDs, invalid dates, non-positive amounts, unknown customers, and high-value transactions.
- **Anomaly detection:** Uses the Isolation Forest algorithm from Scikit-learn to flag potentially unusual transaction amounts.
- **Migration reconciliation:** Compares source and target record counts after migration.
- **Audit logging:** Maintains a migration history containing run IDs, timestamps, source and target paths, record counts, and status.
- **Interactive dashboard:** Uses Streamlit and Plotly to present data summaries, quality findings, anomaly results, and migration history.
- **Automated testing:** Uses Pytest to test the project's core modules.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core development |
| Pandas | Data processing |
| PostgreSQL | Relational database |
| Psycopg | PostgreSQL connectivity |
| Scikit-learn | Machine learning |
| Isolation Forest | Anomaly detection |
| Streamlit | Dashboard |
| Plotly | Data visualization |
| Joblib | Model persistence |
| Pytest | Automated testing |

## Project Structure

```text
enterprise-data-migration/
├── dashboard/
│   └── app.py
├── data/
│   └── sample/
│       └── transactions.csv
├── src/
│   ├── ingestion/
│   ├── transformation/
│   ├── validation/
│   └── ml/
├── tests/
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/kodaliabhiram/enterprise-data-migration.git
cd enterprise-data-migration
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS**
```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL (if using database features)

Create a local `.env` file in the project root with your PostgreSQL connection settings:

```env
PGHOST=localhost
PGPORT=5432
PGDATABASE=enterprise_migration
PGUSER=your_username
PGPASSWORD=your_password
```

Do not commit your `.env` file or database credentials to GitHub.

## Run the Dashboard

```bash
streamlit run dashboard/app.py
```

Open the local URL displayed in your terminal, usually:

`http://localhost:8501`

## Run Automated Tests

```bash
pytest -v
```

## Machine Learning Approach

The project uses the Isolation Forest algorithm for unsupervised anomaly detection. It identifies transaction records with unusual amount patterns.

An anomaly is an unusual observation and does not necessarily indicate fraud. The results should be reviewed and interpreted rather than treated as confirmed fraud predictions.

## Data Quality Checks

The platform checks for:

- Missing transaction amounts
- Duplicate transaction IDs
- Invalid transaction dates
- Non-positive transaction amounts
- Unknown customer IDs
- High-value transactions

## Current Scope and Limitations

This project is an academic prototype developed using sample transaction data.

- The anomaly detection model primarily uses transaction amount as its feature.
- Migration reconciliation currently checks source and target record counts; this alone does not guarantee complete field-level equality.
- The audit trail records successful migration runs.
- Production deployment, large-scale distributed processing, advanced security, and cloud integration are possible future enhancements.

## Future Enhancements

- Field-level data reconciliation
- More comprehensive migration failure logging
- Additional anomaly detection features
- Support for larger datasets
- Cloud database and storage integration
- Authentication and role-based access
- Production deployment and monitoring

## Author

**Abhiram Kodali**

GitHub: https://github.com/kodaliabhiram

## Project Purpose

Developed as a final-year academic project to demonstrate data engineering, database integration, data quality monitoring, machine learning, and dashboard development.




