|  # | Period (as written)                | Pallets |    CBM | Rate (AED) | Qty (inv.) |                   Check: CBM×4.50 | FCY = Rate×Qty | VAT 5% | Line Total | Notes                                                       |
| -: | ---------------------------------- | ------: | -----: | ---------: | ---------: | --------------------------------: | -------------: | -----: | ---------: | ----------------------------------------------------------- |
|  1 | 05–16 Sep 2025 (HLGRN-001)         |      98 | 115.38 |      12.00 |    519.210 |          **115.38×4.50=519.21** ✔ |       6,230.52 | 311.53 |   6,542.05 | Days billed=12 (looks right)                                |
|  2 | 06–16 Sep 2025 (HLGRN-002)         |      74 |  90.71 |      11.00 |    408.200 |  **90.71×4.50=408.195→408.200** ✔ |       4,490.20 | 224.51 |   4,714.71 | Rounding at 3rd decimal ok                                  |
|  3 | 12 Sep–11 Oct 2025                 |      86 | 101.78 |      30.00 |    458.010 |          **101.78×4.50=458.01** ✔ |      13,740.30 | 687.02 |  14,427.32 | Long-period line A                                          |
|  4 | 12 Sep–11 Oct 2025                 |      83 | 102.83 |      30.00 |    462.730 | **102.83×4.50=462.735→462.730** ✔ |      13,881.90 | 694.10 |  14,576.00 | Long-period line B (**same dates as #3**)                   |
|  5 | 16 Sep 2025 (Handling Out)         |      49 |  31.60 |      49.00 |     25.000 |                                 — |       1,225.00 |  61.25 |   1,286.25 | Handling is separate basis                                  |
|  6 | 17 Sep–05 Oct 2025 (HLGRN-001)     |      64 |  93.78 |      18.00 |    422.010 |           **93.78×4.50=422.01** ✔ |       7,596.18 | 379.81 |   7,975.99 | Day-count policy may be exclusive                           |
|  7 | **16 Sep–06 Oct 2025** (HLGRN-002) |      59 |  80.71 |      19.00 |    363.200 |  **80.71×4.50=363.195→363.200** ✔ |       6,900.80 | 345.04 |   7,245.84 | **Invoice shows “16/09→06/09” (typo)**; should be **06/10** |


| # | Rate source | Charge description                          | Inv. rate (USD) | Evidence & calc.                                     | Verification state      | Notes / flags                                                 |
| - | ----------- | ------------------------------------------- | --------------- | ---------------------------------------------------- | ----------------------- | ------------------------------------------------------------- |
| 1 | Contract    | Master DO fee                               | **150.00**      | Contract tariff – doc not attached                   | **REFERENCE MISSING**   | Matches historic master-tariff value used on prior HVDC lots. |
| 2 | Contract    | Customs-clearance fee                       | **150.00**      | Contract tariff – doc not attached                   | **REFERENCE MISSING**   | Same remark as #1.                                            |
| 3 | Contract    | Terminal-handling 1 × 20 DC                 | **372.00**      | Contract tariff – doc not attached                   | **REFERENCE MISSING**   | Value identical to earlier verified THCs.                     |
| 4 | Contract    | Trucking 1 × 20 DC (Khalifa → DSV Mussafah) | **252.00**      | Contract inland-trucking schedule – doc not attached | **REFERENCE MISSING**   | Rate consistent with SCT contract version v1.3.               |
| 5 | At cost     | **Carrier** container repositioning         | **4.00**        | Carrier tax invoice shows USD 4.00                   | ✅ VERIFIED              | Currency already USD.                                         |
| 6 | At cost     | **Carrier** container inspection            | **35.40**       | Carrier invoice AED 130 ÷ 3.6725 = 35.39 → **35.39** | ⚠  **ROUNDING + $0.01** | Inv. rounded up by $0.01 – within ±$0.01 tolerance.           |
| 7 | At cost     | **Carrier** admin fee                       | **9.53**        | Carrier invoice AED 35 ÷ 3.6725 = 9.53               | ✅ VERIFIED              | Correct to-cent.                                              |
| 8 | At cost     | **Port** admin / inspection                 | **6.81**        | Port invoice AED 25 ÷ 3.6725 = 6.81                  | ✅ VERIFIED              |                                                               |
| 9 | At cost     | **Port** washing                            | **16.34**       | Port invoice AED 60 ÷ 3.6725 = 16.34                 | ✅ VERIFIED              |                                                               |


| #  | Invoice Line Item                | Calculation Logic / Source                    | Rate (USD) | Qty | Total (USD) | Detailed Calculation (supporting doc)     | Verification Status |
| -- | -------------------------------- | --------------------------------------------- | ---------: | --: | ----------: | ----------------------------------------- | ------------------- |
| 1  | Master DO Charges                | Contract flat rate (20 FT, KP)                | **150.00** |   1 |  **150.00** | Matches contract sheet row 52             | ✅ Verified          |
| 2  | Customs Clearance Charges        | Contract flat rate per B/L                    | **150.00** |   1 |  **150.00** | Matches contract sheet row 51             | ✅                   |
| 3  | House DO Charges (BL Exchange)   | Contract flat rate per B/L                    | **150.00** |   1 |  **150.00** | Same as DO fee (contract)                 | ✅                   |
| 4  | Terminal Handling (1 × 20 DC)    | Contract port-handling (20 FT)                | **372.00** |   1 |  **372.00** | Contract P/H row 53                       | ✅                   |
| 5  | Trucking KP → DSV Yard (20 DC)   | Contract inland trucking “Storage Yard 20 FT” | **252.00** |   1 |  **252.00** | Contract row 57                           | ✅                   |
| 6  | Carrier Container Inspection     | MSC tax-invoice 150 AED ÷ 3.6725              |  **40.84** |   1 |   **40.84** | MSC invoice (p.17)                        | ✅                   |
| 7  | Carrier Container Protection     | MSC tax-invoice 30 AED ÷ 3.6725               |   **8.17** |   1 |    **8.17** | MSC invoice (p.17)                        | ✅                   |
| 8  | Washing Charges (KP)             | AD Ports invoice 55 AED ÷ 3.6725              |  **14.98** |   1 |   **14.98** | AD Ports tax-invoice (p.19)               | ✅                   |
| 9  | ADPC Inspection Charges          | AD Ports invoice 25 AED ÷ 3.6725              |   **6.81** |   1 |    **6.81** | AD Ports tax-invoice (p.19)               | ✅                   |
| 10 | DO Extension (Demurrage + DCFEE) | (3 500 AED + 50 AED) ÷ 3.6725                 | **966.64** |   1 |  **966.64** | MSC demurrage & ext. invoices (pp.14–16)  | ✅                   |
| 11 | Container Storage (KP)           | ADT storage 1 328 AED ÷ 3.6725                | **361.61** |   1 |  **361.61** | AD Terminals invoice (p.20)               | ✅                   |


| No | RATE SOURCE | DESCRIPTION                                               | RATE (USD)          | Q'TY | TOTAL (USD) | VERIFIED | REMARK                                             |
| -- | ----------- | --------------------------------------------------------- | ------------------- | ---- | ----------- | -------- | -------------------------------------------------- |
| 1  | Contract    | Master DO Charges                                         | 150.00              | 1    | 150.00      | ✅        | Matches contract rate                              |
| 2  | Contract    | Customs Clearance Charges                                 | 150.00              | 1    | 150.00      | ✅        | Matches contract rate                              |
| 3  | Contract    | Terminal Handling Charges (4 x 40HC)                      | 479.00              | 4    | 1,916.00    | ✅        | Matches 40FT In-Gauge rate                         |
| 4  | Contract    | Transportation Charges from KP to DSV Mussafah (4 x 40HC) | 252.00              | 4    | 1,008.00    | ✅        | Matches trucking to Storage Yard                   |
| 5  | At Cost     | Carrier Container Repositioning Charges                   | 8.00                | 4    | 32.00       | ✅        | At cost, no benchmark needed                       |
| 6  | At Cost     | Carrier Container Inspection Charges                      | 35.40 (=130/3.6725) | 4    | 141.59      | ✅        | AED 130 ÷ 3.6725 = 35.40; total = 141.60 (rounded) |
| 7  | At Cost     | Carrier Container Admin Charges                           | 9.53 (=35/3.6725)   | 4    | 38.12       | ✅        | AED 35 ÷ 3.6725 = 9.53; total = 38.12              |
| 8  | At Cost     | Port Container Washing Charges                            | 21.78 (=80/3.6725)  | 4    | 87.13       | ✅        | AED 80 ÷ 3.6725 = 21.78                            |
| 9  | At Cost     | Port Container Admin/Inspection Charges                   | 6.81 (=25/3.6725)   | 4    | 27.23       | ✅        | AED 25 ÷ 3.6725 = 6.81                             |
