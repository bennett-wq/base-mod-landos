# Spark BBO Signal Intelligence — Step 4.5 Reference

STATUS: UNBLOCKED. BBO credentials confirmed March 2026.

BBO = Broker Back Office. Private-role Spark API key required.

6 SIGNAL FAMILIES AND KEY FIELDS:

FAMILY 1 — Developer Exit
  OffMarketDate, WithdrawalDate, CancellationDate,
  MajorChangeTimestamp, MajorChangeType

FAMILY 2 — Listing Behavior
  CumulativeDaysOnMarket (★ real staleness), PreviousListPrice,
  OriginalEntryTimestamp, StatusChangeTimestamp,
  PriceChangeTimestamp, BackOnMarketDate

FAMILY 3 — Language Intelligence (regex Phase 1, LLM deferred)
  PrivateRemarks (★ agent-to-agent signal), ShowingInstructions

FAMILY 4 — Agent/Office Clustering
  ListAgentKey (★ UUID, reliable), CoListAgentKey,
  CoListOfficeKey, BuyerAgentKey, BuyerOfficeKey

FAMILY 5 — Subdivision Remnant
  LegalDescription (★ Lot/Block/Plat), TaxLegalDescription,
  LotDimensions, FrontageLength, PossibleUse, NumberOfLots

FAMILY 6 — Market Velocity
  ClosePrice, CloseDate, PurchaseContractDate

Land detail (extends existing):
  Zoning, ZoningDescription, LotFeatures, RoadFrontageType,
  RoadSurfaceType, Utilities, Sewer, WaterSource, CurrentUse
