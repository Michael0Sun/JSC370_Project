# JSC370_Project

# Los Angeles Parking Citations Analysis (2021–2025)

## Overview

This project analyzes parking citation data from the City of Los Angeles between 2021 and 2025. The goal is to explore temporal, spatial, and violation type patterns in parking enforcement using real-world administrative data.

This project was completed as part of JSC 370 and uses the official Socrata Open Data API (SODA) to programmatically acquire the dataset.

---

## Data Source

Data were retrieved from the City of Los Angeles Open Data Portal:

- Dataset: Parking Citations  
- Dataset ID: 4f5p-udkv  
- API: Socrata Open Data API (SODA 2.0)  
- Source: https://data.lacity.org  

Data were accessed via authenticated API requests using an application token.

---

## How to Run This Project

### 1️ Set Your API Token (Required)

This project requires a Socrata App Token.

If you are using **Windows**, open PowerShell and run:

setx SOCRATA_APP_TOKEN "your_token_here"

Then restart VS Code or your terminal.

### 2️ Verify Token Setup

Run the following in Python:

```python
import os
print(os.getenv("SOCRATA_APP_TOKEN"))
```

If your token prints successfully, setup is complete.

