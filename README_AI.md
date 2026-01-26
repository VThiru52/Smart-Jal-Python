# Smart Jal AI & Analytics Backend Documentation

This document outlines the AI, Machine Learning, and Analytical services integrated into the Smart Jal backend to drive intelligent groundwater management.

## 🧠 AI & ML Core Services

### 1. Water Level Forecasting (`forecasting_service.py`)
Predicts future groundwater trends to help in pre-monsoon planning.
- **Model**: [Facebook Prophet](https://facebook.github.io/prophet/)
- **Technique**: Additive regression model with yearly and weekly seasonality.
- **Explainability**: SHAP (SHapley Additive exPlanations) and Component Decomposition (Trend vs. Seasonality) to explain *why* a level is predicted to rise or fall.
- **Capabilities**: 3, 6, and 12-month automated forecasting windows.

### 2. Autonomous Anomaly Detection (`anomaly_service.py`)
Monitors real-time data ingestion to detect sensor failures or environmental shocks.
- **Technique**: Statistical Outlier Detection (Z-Score Analysis).
- **Threshold**: Readings with a Z-score > 3 are flagged as high-severity anomalies.
- **Future Roadmap**: Integration of Isolation Forest and Autoencoders for non-linear anomaly detection.

### 3. Piezometer Sustainability Analysis (`analysis_service.py`)
Computes high-level health metrics for individual monitoring stations.
- **Sustainability Score**: Uses **Linear Regression** (NumPy) to calculate the slope of the phreatic surface over 30 years.
- **Recharge Efficiency**: Analyzes **Hydrological Recovery Cycles** (Drawdown vs. Recovery) to score how effectively an aquifer replenishes post-monsoon.
- **Dynamic Insights**: Generates automated hydrologist notes based on trend slope and efficiency thresholds.

---

## 🗺️ Spatial & Decision Intelligence

### 4. Managed Aquifer Recharge (MAR) Priority (`recharge_service.py`)
A decision-support system to rank villages for recharge interventions.
- **Logic**: Multi-factor weighted scoring.
- **Inputs**: Calculated Average Depth (RPC), Historical Rainfall, and Population density.
- **Output**: Suitability Ranks (1-3) and Priority Scores (0-10).

### 5. Geographic Context Engine (`spatial_service.py`)
Enriches sensor data with environmental parameters.
- **Capabilities**:
    - **Soil Analysis**: Point-in-polygon lookups for soil characteristics.
    - **Elevation Profiling**: Radius-based statistical elevation checks for runoff potential.
    - **Aquifer Mapping**: Identification of principal aquifer systems and model zones.

---

## 🛠️ Technology Stack
- **Languages**: Python 3.10+
- **ML/Math Libraries**: `prophet`, `pandas`, `numpy`, `shap`, `scikit-learn`
- **Spatial Libraries**: `geopandas`, `shapely`
- **Data Layer**: Supabase (PostgreSQL + PostGIS)

---
*Created for Smart Jal AI - Advanced Agentic Coding Implementation*
