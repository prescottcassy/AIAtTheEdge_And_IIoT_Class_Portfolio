# Smartwatch Telemetry Dashboard – Capstone Project  
A complete Edge‑to‑Cloud pipeline using ThingsBoard Cloud

## 1. Problem Overview
Modern wearable devices generate continuous health and activity data, but turning that raw telemetry into meaningful insights requires a reliable pipeline.  
The goal of this project was to:

- Simulate smartwatch sensor data  
- Stream telemetry to ThingsBoard Cloud  
- Build dashboards that visualize activity, intensity, calories, and latency  
- Evaluate the performance of the pipeline end‑to‑end  

This project demonstrates how an **Edge AI device** can integrate with an **IIoT cloud platform** to support real‑time monitoring and analytics.

---

## 2. Approach & Methods
To solve this problem, I built a full telemetry workflow:

### Smartwatch Data Simulation
- Generated synthetic activity data (steps, calories, intensity, timestamps)  
- Batched and streamed data in memory‑safe chunks  
- Implemented latency tracking for each telemetry packet  

### Edge → Cloud Telemetry Pipeline
- Sent data to ThingsBoard Cloud using REST API  
- Created a custom device profile for smartwatch metrics  
- Defined telemetry keys for activity, intensity, and timestamps  

### Dashboard Development
Built multiple dashboards inside ThingsBoard Cloud:

- Activity Trends Dashboard  
  - Line charts for steps, calories, and intensity  
- Latency Monitoring Dashboard  
  - Real‑time latency visualization  
  - Alerts for high‑latency packets  
- Daily Summary Dashboard  
  - Cards for total steps, calories, and active minutes  

### Tools & Technologies
- Python (telemetry simulator)  
- ThingsBoard Cloud  
- REST API  
- JSON telemetry payloads  

---

## 3. Results & Interpretation
The final system successfully:

- Streamed smartwatch telemetry to the cloud in real time  
- Visualized activity patterns across hours and days  
- Measured and displayed end‑to‑end latency  
- Demonstrated how edge devices integrate with IIoT platforms  
- Produced dashboards that clearly communicate user activity and system performance  

What this means:  
The project shows that a simulated smartwatch can behave like a real IIoT device, sending structured telemetry to a cloud platform where it can be monitored, analyzed, and used for decision‑making. It also highlights the importance of latency tracking and data modeling in edge‑to‑cloud systems.

