import type { Domain } from "@/lib/api";

/** Static fallback so the domain picker works even when the API is unreachable. */
export const STATIC_DOMAINS: Domain[] = [
  { id: "oil-gas", label: "Oil & Gas", category: "Energy", description: "Upstream, midstream, and downstream software.", compliance: ["ISO 27001", "NERC CIP"], typical_systems: ["SCADA", "Asset management"] },
  { id: "solar", label: "Solar Energy", category: "Energy", description: "Solar farm monitoring and grid integration.", compliance: ["IEC 62446", "ISO 27001"], typical_systems: ["Performance monitoring", "O&M"] },
  { id: "battery", label: "Battery Storage", category: "Energy", description: "BESS control and grid arbitrage software.", compliance: ["UL 9540", "IEEE 1547"], typical_systems: ["BMS integration", "Dispatch"] },
  { id: "waves", label: "Wave Energy", category: "Energy", description: "Marine energy and offshore operations.", compliance: ["DNV standards", "ISO 27001"], typical_systems: ["Sensor telemetry", "Monitoring"] },
  { id: "water", label: "Water Utilities", category: "Energy", description: "Water treatment and smart metering.", compliance: ["EPA SDWA", "ISO 27001"], typical_systems: ["SCADA", "Leak detection"] },
  { id: "wind", label: "Wind Energy", category: "Energy", description: "Wind farm operations and turbine analytics.", compliance: ["IEC 61400", "ISO 27001"], typical_systems: ["Turbine CMS", "Forecasting"] },
  { id: "legal-analytics", label: "Legal Analytics", category: "Legal", description: "Case research and contract analysis.", compliance: ["GDPR", "SOC 2"], typical_systems: ["Document review", "NLP search"] },
  { id: "healthcare", label: "Healthcare", category: "Healthcare", description: "Clinical systems and patient engagement.", compliance: ["HIPAA", "HL7 FHIR"], typical_systems: ["EHR integration", "Telehealth"] },
  { id: "hospitals", label: "Hospitals", category: "Healthcare", description: "Hospital operations and clinical workflows.", compliance: ["HIPAA", "Joint Commission"], typical_systems: ["EHR", "Bed management"] },
  { id: "hotels", label: "Residential Hotels", category: "Hospitality", description: "Property management and guest experience.", compliance: ["PCI DSS", "GDPR"], typical_systems: ["PMS", "Guest app"] },
  { id: "trading", label: "Trading", category: "Finance", description: "Order management and algo trading.", compliance: ["SEC", "MiFID II"], typical_systems: ["OMS/EMS", "Risk engine"] },
  { id: "banking", label: "Banking", category: "Finance", description: "Core banking and digital channels.", compliance: ["PCI DSS", "SOX"], typical_systems: ["Core banking", "KYC/AML"] },
  { id: "finance", label: "Banking & Finance", category: "Finance", description: "Wealth management and fintech platforms.", compliance: ["PCI DSS", "SOC 2"], typical_systems: ["Portfolio mgmt", "Fraud detection"] },
];

export function groupDomainsByCategory(domains: Domain[]): Record<string, Domain[]> {
  return domains.reduce<Record<string, Domain[]>>((acc, domain) => {
    if (!acc[domain.category]) acc[domain.category] = [];
    acc[domain.category].push(domain);
    return acc;
  }, {});
}
