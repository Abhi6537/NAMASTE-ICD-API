# Healthcare Terminology Integration API

This project provides a FastAPI-based API to integrate and map healthcare terminologies from WHO ICD-11 and the Indian NAMASTE system. It also supports generating FHIR resources.

## Features

*   **Search**: Search for terms across ICD-11 and NAMASTE.
*   **Mapping**: Map NAMASTE terms to ICD-11 classifications with similarity scoring.
*   **FHIR Conversion**: Generate FHIR Condition resources from mapped terms.
*   **Bulk Mapping**: Process multiple term mappings concurrently.
*   **Terminology System Information**: Get details about supported terminology systems.

## Project Structure

healthcare_api_project/
├── app/
│   ├── init.py
│   ├── api/
│   │   ├── init.py
│   │   ├── endpoints/       # API route handlers
│   │   │   ├── init.py
│   │   │   ├── general.py
│   │   │   ├── search.py
│   │   │   ├── mapping.py
│   │   │   ├── fhir.py
│   │   │   └── bulk_mapping.py
│   │   │   └── terminology_systems.py
│   │   ├── models/          # Pydantic data models
│   │   │   ├── init.py
│   │   │   ├── common.py
│   │   │   └── fhir.py
│   │   └── services/        # Business logic and external integrations
│   │       ├── init.py
│   │       ├── icd11.py
│   │       ├── namaste.py
│   │       ├── mapping.py
│   │       └── fhir.py
│   ├── core/                # Core configurations and utilities
│   │   ├── init.py
│   │   └── config.py
│   └── main.py              # FastAPI application entry point
├── data/                    # Local data files (e.g., for NAMASTE)
│   ├── init.py
│   └── namaste_data.json
├── tests/                   # Unit and integration tests
│   ├── init.py
│   └── ...
├── .env.example             # Environment variable configuration template
├── docker-compose.yml       # Docker Compose for running services
├── Dockerfile               # Dockerfile for building the API image
├── requirements.txt         # Python dependencies
└── README.md                # This file

## Setup and Running

### Prerequisites

*   [Docker](https://www.docker.com/get-started/)
*   [Docker Compose](https://docs.docker.com/compose/install/)
*   [Python 3.7+](https://www.python.org/downloads/)

### Steps

1.  **Clone the repository**:
    ```bash
    git clone <your-repository-url>
    cd healthcare_api_project
    ```

2.  **Create a `.env` file**:
    Copy the `.env.example` file and rename it to `.env`.
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file to add your ICD-11 API credentials and any other necessary configurations.

3.  **Build and Run with Docker Compose**:
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker image for the API and start the application.

### API Endpoints

*   **Root**: `GET /`
*   **Health Check**: `GET /health`
*   **Search**: `GET /api/v1/search?q=<query>&source=<namaste|icd11|both>&ayush_system=<system>`
*   **Map Terminology**: `POST /api/v1/map?namaste_id=<id>&include_fhir=<true|false>`
*   **FHIR Condition**: `GET /api/v1/fhir/condition?namaste_id=<id>&patient_id=<patient_id>`
*   **Bulk Map Terms**: `POST /api/v1/bulk-map?terms=<term1>&terms=<term2>...` (pass multiple `terms` query parameters)
*   **Terminology Systems**: `GET /api/v1/terminology-systems`

## Development Notes

*   **NAMASTE Data**: The `NAMASTEService` currently reads from a local `data/namaste_data.json` file. Ensure this file is populated with relevant data.
*   **ICD-11 API Credentials**: You must obtain and set `ICD11_CLIENT_ID` and `ICD11_CLIENT_SECRET` in your `.env` file for the ICD-11 integration to work.
*   **Error Handling**: Basic error handling is implemented, but can be further enhanced.
*   **Logging**: Logging is configured to `INFO` level by default.
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload