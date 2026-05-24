![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Research-orange)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey)
![Telemetry](https://img.shields.io/badge/RF-Telemetry-red)

\# Dynamic D-IDOE Framework for Rural Wireless Radio Links



Dynamic operational characterization framework for rural wireless radio links using temporal RF telemetry, adaptive thresholding, and multivariable operational state validation.



\---



\# Overview



This repository contains the complete telemetry acquisition, preprocessing, modeling, validation, and reporting framework developed for the research paper:



> \*\*Dynamic Operational State Characterization of Rural Wireless Radio Links Using Temporal RF Telemetry and Adaptive Thresholding\*\*



The framework was designed and validated using a real rural point-to-point wireless radio link deployed in the Andean region of Cajamarca, Peru.



The system integrates:



\- Real RF telemetry acquisition from Cambium ePMP devices

\- Longitudinal telemetry monitoring

\- Temporal feature engineering

\- Dynamic RF operational index generation (D-IDOE)

\- Adaptive threshold optimization

\- Composite operational reference modeling

\- Machine learning validation

\- Automated IEEE-ready figure and table generation



\---



\# Experimental Scenario



| Parameter | Description |

|---|---|

| Deployment type | Real rural wireless radio link |

| Architecture | AP-SM |

| Distance | \~12 km |

| Region | Cajamarca, Peru |

| Environment | High-altitude Andean terrain |

| Equipment | Cambium ePMP 400C |

| Frequency band | 5.8 GHz |

| Telemetry acquisition | SSH-based polling |

| Monitoring duration | Longitudinal continuous monitoring |

| Sampling interval | Periodic automated acquisition |



\---



\# Repository Structure



```text

dynamic-didoe-rf-telemetry/

│

├── data/

├── docs/

├── figures/

├── paper/

├── tables/

│

├── scripts/

│   ├── acquisition/

│   ├── preprocessing/

│   ├── modeling/

│   ├── reporting/

│   ├── advanced\_monitoring/

│   └── maintenance/

│

├── README.md

├── requirements.txt

├── .gitignore

└── LICENSE

```



\---



\# Telemetry Acquisition Layer



The telemetry acquisition layer was implemented using Linux Bash automation scripts capable of periodically retrieving RF telemetry from Cambium ePMP devices through SSH-based polling.



The acquisition system automatically generated longitudinal CSV telemetry datasets including:



\- RSSI

\- SNR

\- MCS

\- Downlink rate

\- Uplink rate

\- RF quality indicators

\- Temporal operational metrics



Main acquisition scripts:



| Script | Function |

|---|---|

| `poll\_epmp.sh` | Main telemetry polling engine |

| `capture\_agg\_ap.sh` | Aggregated telemetry acquisition |

| `auto\_csv\_pipeline.sh` | Automated telemetry pipeline |

| `check\_poll.sh` | Polling validation |

| `check\_agg.sh` | Aggregated acquisition validation |



\---



\# Processing Pipeline



The framework follows a multistage processing architecture:



```text

RF Telemetry Acquisition

&#x20;       ↓

Dataset Construction

&#x20;       ↓

Temporal Feature Engineering

&#x20;       ↓

Dynamic D-IDOE Modeling

&#x20;       ↓

Adaptive Threshold Optimization

&#x20;       ↓

Composite Operational Reference

&#x20;       ↓

Validation and Evaluation

&#x20;       ↓

IEEE Figure/Table Generation

```



\---



\# Modeling Components



\## Preprocessing



| Script | Description |

|---|---|

| `01\_build\_dataset\_master.py` | Dataset consolidation |

| `02\_temporal\_features.py` | Temporal feature extraction |



\## Dynamic Modeling



| Script | Description |

|---|---|

| `03\_dynamic\_idoe.py` | Initial D-IDOE generation |

| `04\_ml\_validation.py` | Machine learning validation |

| `05\_dynamic\_idoe\_v2.py` | Improved D-IDOE framework |

| `06\_threshold\_optimization.py` | Adaptive threshold optimization |

| `08\_operational\_reference.py` | Composite operational reference |

| `09\_operational\_reference\_thresholds.py` | Adaptive operational states |

| `10\_validate\_against\_operational\_reference.py` | Final validation |



\## Reporting



| Script | Description |

|---|---|

| `11\_generate\_final\_figures.py` | IEEE-ready figures |

| `12\_generate\_ieee\_tables.py` | IEEE-ready tables |

| `13\_generate\_ieee\_results\_text.py` | Automatic results generation |



\---



\# Advanced Monitoring Components



The repository additionally includes experimental operational monitoring tools for predictive RF analysis and alert generation.



These components include:



\- Predictive RF degradation analysis

\- Temporal anomaly detection

\- Telegram alerting

\- Operational state prediction

\- Database synchronization

\- Automated monitoring services



\---



\# Key Findings



The proposed D-IDOE framework demonstrated substantially better agreement when validated against a multivariable composite operational reference than against instantaneous throughput alone.



| Validation Strategy | F1-score |

|---|---|

| Throughput-only reference | 0.3626 |

| Composite operational reference | 0.4767 |



These results suggest that wireless link degradation cannot be adequately represented using a single metric, and instead requires the integration of RF quality, modulation dynamics, and temporal stability indicators.



\---



\# Figures and Tables



Generated IEEE-ready outputs are available in:



\- `figures/`

\- `tables/`



These include:



\- Confusion matrices

\- Temporal evolution plots

\- D-IDOE distributions

\- Operational state comparisons

\- Feature importance analysis

\- Throughput-state relationships



\---



\# Installation



Install dependencies:



```bash

pip install -r requirements.txt

```



\---



\# Reproducibility



This repository was designed to support reproducible RF telemetry research workflows.



Sensitive information including:

\- passwords,

\- API keys,

\- Telegram tokens,

\- and private IP addresses



has been removed or anonymized.



\---



\# Citation



If you use this framework in your research, please cite the associated paper.



Citation information will be updated after publication.



\---



\# License



This project is released for academic and research purposes.

