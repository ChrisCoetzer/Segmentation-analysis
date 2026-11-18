# MVP implementation review

Reviewed October 20, 2026 against the mandate: how much effort should the client place into segmentation?

## Implemented through the opportunity feature

- Main visual: balanced nested segmentation and responsive audiences found in the uplift benchmark. No claim of universally optimal segments.
- Second visual: campaign-specific and pooled advertising frequency, observed conversion labels, and audience sizes from the separate attribution release.
- Opportunity: an interactive investment scenario comparing added contribution with explicit segmentation costs at equal targeting volume.
- One scrolling page, with optional detail panels beneath straightforward charts and controls.

## Review decisions

1. **Keep the second chart descriptive.** Frequency can reflect customer intent, repeated labels, sampling, and impressions after conversion. It provides campaign context; it cannot score causal segmentation readiness or set an optimal frequency cap.
2. **Count at a consistent grain.** Positive impression labels are collapsed to one flag per user–campaign pair. The chart supplies the denominator and a separate audience-distribution measure.
3. **Use equal campaign volume for economics.** The investment feature draws from fixed-reach policies, not the unequal audience sizes in the main story cards.
4. **Separate evidence from assumptions.** The pipeline supplies benchmark relative gains. The client supplies audience, baseline incrementality, contribution, transfer, and costs. Dollar outputs are scenario calculations.
5. **Allow “do not add complexity.”** Broad targeting remains an option at zero additional cost. Zero assumed transfer, zero baseline, or full reach cannot produce an artificial segmentation gain.
6. **Avoid a spurious winner.** Close net-value options receive a sensitivity note. No financial recommendation is based on small point-estimate differences.
7. **Keep calculations auditable.** Scenario exports include all assumptions and computed outcomes; formulas and counting definitions remain accessible.

## Verification

Mathematical tests and actual Streamlit control checks cover the models, frequency aggregation, ROI-scenario arithmetic, empty frequency filters, outcome switches, full reach, transfer changes, and high costs. Browser review checks that the charts render and the page stays understandable when scrolling between the main result, frequency context, and investment scenario.

Final verification: 17 mathematical tests passed; the full Streamlit control script passed; browser inspection showed no chart errors. The final presentation corrects currency rendering, reduces axis tick clutter, collapses secondary frequency controls/data, and identifies close scenario options rather than implying a decisive winner.

## Remaining scope

The app does not yet implement an AI assistant, deployment, the revised five-slide submission deck, the course's AI Client critique, or the submission zip. No critique has been fabricated. These are separate from the completed working opportunity feature. Retraining stability and client transportability remain analytical limitations; segmentation costs are explicit inputs rather than measured consequences of tree depth.
