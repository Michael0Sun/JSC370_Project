# JSC370_Project

# Los Angeles Parking Citations Analysis (2021–2025)

## Project Website

https://michael0sun.github.io/JSC370_Project/

## GitHub Repository

https://github.com/Michael0Sun/JSC370_Project

---

## Overview

This project analyzes parking citation data from the City of Los Angeles between 2021 and 2025. It focuses on identifying temporal trends, spatial clustering, and relationships between vehicle characteristics and violation types.

The analysis includes:

- Exploratory Data Analysis (EDA)
- Spatial visualization using interactive maps
- Temporal pattern analysis
- Predictive modeling using Decision Tree and XGBoost

The goal is to understand whether parking violations follow structured patterns rather than random behavior.

---

## Data Source

Data were retrieved from the City of Los Angeles Open Data Portal:

- Dataset: Parking Citations  
- Dataset ID: 4f5p-udkv  
- API: Socrata Open Data API (SODA 2.0)  
- Source: https://data.lacity.org  

Data are accessed via authenticated API requests using an application token.

---

## Reproducibility

To reproduce the full project:

### 1. Set Your API Token (Required)

This project requires a Socrata App Token.

If you are using Windows, open PowerShell and run:

setx SOCRATA_APP_TOKEN "your_token_here"

Then restart your terminal or VS Code.

---

### 2. Verify Token Setup

Run the following in Python:

import os
print(os.getenv("SOCRATA_APP_TOKEN"))

If your token prints successfully, setup is complete.

---

### 3. Run Data Preparation

python prepare_website_data.py

---

### 4. Render the Website

quarto render index.qmd

---

### 5. (Optional) Render the Final Report

quarto render Final_report.qmd

---

## Project Structure

- index.qmd → main website (interactive visualizations)
- index.html → rendered website
- Final_report.qmd / Final_report.pdf → final report
- Midterm_report.html → midterm report
- prepare_website_data.py → data extraction and preprocessing script
- outputs/ → processed data used for visualizations

---

## Notes on Data Availability

The dataset is not stored locally in this repository due to its large size.

All data are dynamically retrieved from the Socrata Open Data API.  
Users must provide their own API token to reproduce the analysis.

---

## Interactive Visualizations

The project website includes interactive visualizations such as:

- Spatial map of citation concentration
- Monthly time-series trends
- Vehicle make and body style composition

Each visualization includes a caption and a brief description.

---

## Acknowledgments

Data provided by the City of Los Angeles Open Data Portal.
