"""Industry domain catalog for software engineering RFP generation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Domain:
    id: str
    label: str
    category: str
    description: str
    compliance: list[str]
    typical_systems: list[str]


DOMAINS: list[Domain] = [
    # Energy
    Domain(
        id="oil-gas",
        label="Oil & Gas",
        category="Energy",
        description="Upstream, midstream, and downstream software for exploration, production, and refining.",
        compliance=["ISO 27001", "NERC CIP", "API standards"],
        typical_systems=["SCADA integration", "Asset management", "Predictive maintenance", "HSE reporting"],
    ),
    Domain(
        id="solar",
        label="Solar Energy",
        category="Energy",
        description="Solar farm monitoring, inverter management, and grid integration platforms.",
        compliance=["IEC 62446", "NERC", "ISO 27001"],
        typical_systems=["Performance monitoring", "O&M ticketing", "Forecasting", "Billing"],
    ),
    Domain(
        id="battery",
        label="Battery Storage",
        category="Energy",
        description="BESS control, state-of-health analytics, and grid arbitrage software.",
        compliance=["UL 9540", "IEEE 1547", "ISO 27001"],
        typical_systems=["BMS integration", "Dispatch optimization", "Telemetry", "Market bidding"],
    ),
    Domain(
        id="waves",
        label="Wave Energy",
        category="Energy",
        description="Marine energy capture systems, condition monitoring, and offshore operations.",
        compliance=["DNV standards", "ISO 27001", "Maritime safety"],
        typical_systems=["Sensor telemetry", "Predictive maintenance", "Environmental monitoring"],
    ),
    Domain(
        id="water",
        label="Water Utilities",
        category="Energy",
        description="Water treatment, distribution, and smart metering software platforms.",
        compliance=["EPA SDWA", "ISO 27001", "AWWA standards"],
        typical_systems=["SCADA", "Leak detection", "Customer portal", "GIS integration"],
    ),
    Domain(
        id="wind",
        label="Wind Energy",
        category="Energy",
        description="Wind farm operations, turbine analytics, and renewable portfolio management.",
        compliance=["IEC 61400", "NERC", "ISO 27001"],
        typical_systems=["Turbine CMS", "Power forecasting", "Work management", "Grid compliance"],
    ),
    # Legal
    Domain(
        id="legal-analytics",
        label="Legal Analytics",
        category="Legal",
        description="Case research, contract analysis, e-discovery, and litigation support platforms.",
        compliance=["ABA ethics", "GDPR", "SOC 2", "ISO 27001"],
        typical_systems=["Document review", "NLP search", "Matter management", "Billing integration"],
    ),
    # Healthcare
    Domain(
        id="healthcare",
        label="Healthcare",
        category="Healthcare",
        description="Clinical systems, patient engagement, and population health software.",
        compliance=["HIPAA", "HITECH", "HL7 FHIR", "SOC 2"],
        typical_systems=["EHR integration", "Patient portal", "Telehealth", "Analytics"],
    ),
    Domain(
        id="hospitals",
        label="Hospitals",
        category="Healthcare",
        description="Hospital operations, bed management, clinical workflows, and revenue cycle.",
        compliance=["HIPAA", "Joint Commission", "HL7 FHIR", "SOC 2"],
        typical_systems=["EHR", "Lab/Radiology", "Bed management", "Revenue cycle"],
    ),
    # Hospitality
    Domain(
        id="hotels",
        label="Residential Hotels",
        category="Hospitality",
        description="Property management, guest experience, and revenue management for hotels.",
        compliance=["PCI DSS", "GDPR", "ISO 27001"],
        typical_systems=["PMS", "Channel manager", "Guest app", "Housekeeping ops"],
    ),
    # Finance
    Domain(
        id="trading",
        label="Trading",
        category="Finance",
        description="Order management, market data, algo trading, and risk platforms.",
        compliance=["SEC", "MiFID II", "SOC 2", "ISO 27001"],
        typical_systems=["OMS/EMS", "Market data", "Risk engine", "Compliance surveillance"],
    ),
    Domain(
        id="banking",
        label="Banking",
        category="Finance",
        description="Core banking, digital channels, lending, and payment processing systems.",
        compliance=["PCI DSS", "SOX", "GLBA", "SOC 2", "ISO 27001"],
        typical_systems=["Core banking", "Mobile banking", "KYC/AML", "Loan origination"],
    ),
    Domain(
        id="finance",
        label="Banking & Finance",
        category="Finance",
        description="Wealth management, insurance, fintech, and financial analytics platforms.",
        compliance=["PCI DSS", "SOX", "GDPR", "SOC 2"],
        typical_systems=["Portfolio management", "Claims processing", "Fraud detection", "Reporting"],
    ),
]

DOMAIN_BY_ID = {d.id: d for d in DOMAINS}
CATEGORIES = sorted({d.category for d in DOMAINS})
