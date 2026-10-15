**********************************
Legal Notice and Rights

© 2026 Zhongyuan(Woody) Hu. All rights reserved.

Unless otherwise stated, all source code, documentation, data models, configurations, and other materials contained in this repository are the intellectual property of Zhongyuan(Woody) Hu.

No part of this repository may be copied, reproduced, modified, distributed, published, sublicensed, or used for commercial purposes without prior written permission from the copyright holder, except as permitted by applicable law.

Access to this repository does not grant any license or other rights to its contents, whether express or implied.

All third-party names, trademarks, and materials remain the property of their respective owners.

For permission to use any materials in this repository, please contact the copyright holder.

Disclaimer: This repository and its contents are provided "AS IS", without warranties of any kind, express or implied. The copyright holder shall not be liable for any claims, damages, or other liabilities arising from the use of the repository or its contents, to the extent permitted by applicable law.

files from data_input folder are exempt from statement above
**********************************

Configuration:
    The following notebook are intended to be run on Databricks Environment with recommend runtime 18.0 LTS (Scala 2.13, Spark 4.1.0), 8GB Memory and 4 Cores.
     - Data_staging
     - automapping_staging
    And this configuration is used as reference for below performance calculation
Performance:
    Data Layer: within 5min with shorter time available on better cluster setting.
    Aggregation Layer: ~1:30min for 4600 rows 

Database structure:
    Staging
       - campaign_metadata
       - meta_ads_daily
       - google_ads_daily
       - store_visits
    Staging_mid
       - Automapping_Step1
       - Automapping_Step2
       - Automapping_Unmapped
    Staging_final (Not utilize for this version)
       - final_standard_table

**********************************

Answer to question Q1-Q4 please see docx

•	How to run your pipeline end-to-end 
    Ingestion phase / Staging phase / report-ready phase
      Azure bucket ->  Data_staging -> automapping_staging -> table
    – detail will be provided upon interview

•	The data model and grain of each table -- https://excalidraw.com/#json=XpObBv2s5Zk2Wm5YDppqt,p3WmkmuV6F7-C2aNjnunTg or Data_Architecture.png for offline access

•	Key decisions and tradeoffs you made (especially around the data quality issues) – see bullet points below
    
    Rank from least serverity to highest

    =============Data Quality issue=============
    1.	google_ads_daily: Instead of sending spend in micro, reach out to team to have report schedule as regular spend to avoid hard code for micro conversion.
    2.	Meta_ads_daily: Missing currency is filtered out for team to map correspondingly, also spot zero conversion_spend with Impression value --need to confirm with team

    =============Discrepancy issue=============
    3.	Campaign_meta: Mixed attribution_window_day will cause discrepancies due to any timely campaign activity will immediately reflect on short term than long term. –will take rolling 7 recorded day avg to smooth the spike and valley but sometime will lose accuracy. Idealy one analysis per attribution window.
    4.	Missing Budget in Metadata currently are calculated based on following:
        a.	Same product, same region lines with valid spend are used to calculate median average using percentile(0.5)
        b.	Median budget devided by flight day to get Med-budeget per day which is used to calculate approx. campaign budget based on missing budget campaign flight day
        c. This is highly unreliable due to possibility of Free tier campaign/Bonus Campaign/Holiday Campaign/other Financial Strategies so needs to flag rightaway instead of bandage this afterward.
    5.	Campaign_meta: Spotted Outdoor product only alive in WEST and EAST only, need to address this with team whether this is expected. Also worth noting that if national covers West or East?  If not the store_visits regional analysis wont be reliable.

    =============Impact Decision making=============
    6.	Store_visits: region was identified using geography West/East and leave National for other that are not clearly W/E (e.g. Detroit, Chicago, Dallas, etc.) Campaign team are REQUIRED to label them correctly or provide mapping file for reference. --will affect deicision making
    
    
•	What you'd do differently with more time 
    Didn’t have time for a fully constructed fail-safe staging_mid, final_staging and visualization. For example some of the missing value should be spotted before the staging process
    Didn't have time to track pacing and see what causes overspending
    Also certain tradeoff shouldn’t happen and blind guesses are not supposed to be on DE side, should check with client’s team to straighten things out
•	How you'd productionize this (orchestration, monitoring, testing, alerting) 
    1. Requirement gathering and pick the right tools for robust pipeline(Orchestration), 2.Testing, 3.Monitoring, 4.Alerting
