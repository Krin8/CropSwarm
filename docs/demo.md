# CropSwarm demo

## Script · about 2½ minutes

| Time | Screen | Talk track |
|---|---|---|
| 0:00–0:20 | US High Plains B | “A farmer often has several plausible rotations and limited time to compare them. CropSwarm starts with a supplied baseline rotation and brings NASA observations and local assumptions into one comparison.” |
| 0:20–0:45 | Rainfall and vegetation | “NASA POWER shows the seasonal water pattern. Terra MODIS shows a spring 2019 vegetation peak over a neighborhood classified as fallow by CDL. The cause remains unexplained.” |
| 0:45–1:05 | Inputs and priorities | “The Kansas reference is rainfed, with zero irrigation supplied in the model. The farmer can edit crops, soil water and water supply assumptions. Here I put more weight on water. The chart updates the scores of the displayed rotations.” |
| 1:05–1:30 | Compare rotations | “CropSwarm compares the configured baseline with four distinct alternatives for the reference farm. Each shows how it trades off water, nitrogen, erosion, climate fit, income and risk. Open one to see its evidence.” |
| 1:30–1:55 | Warmer and drier | “The percentiles show a range of modeled outcomes. Wins show each strategy’s share of the top scores across draws under the selected preset. Tied strategies split the credit.” |
| 1:55–2:15 | Telangana, then Makueni | “Telangana's second season is tentative, and repeated paddy keeps its rotation warning. Makueni's cropland status is unverified.” |
| 2:15–2:30 | Optimizer check | “We checked ant colony search against exact enumeration. The best of five searches reached the optimum in all 30 trials for each farm and preset. Validate the results locally. The farmer decides.” |

For a longer demo, open [What to check first](sensitivity.md) after choosing a priority preset. Show one of its ranked local checks and its evidence grade. The priority reflects sensitivity under the tested model ranges. Open [Opportunity windows](opportunity_windows.md) to show that Kansas has recurring low greenness at the reference cutoff. Winter-wheat dormancy is plausible, the field's availability is unknown, and no crop passes the fit screen at that cutoff.

## Slide outline

1. Describe the decision and the reference baseline rotation.
2. Show the site's NASA rainfall and vegetation charts alongside the soil context.
3. Adjust the farmer's six priorities.
4. Compare the baseline with four alternatives. Show one benefit, one trade-off and one evidence source.
5. Explain the scenario percentiles and wins, then show the Makueni flag.
6. Close with exact optimizer verification and the evidence the farmer needs for a local decision.
