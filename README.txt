This is a climate value at risk model for real estate asset in the UK. It covers all domestic and non-domestic properties with EPC certificates.

The way to use it:

Install crrem package: pip install crrem
Import VAR function: from crrem.var import VAR
Run the function by specifying 5 arguments: BUILDING_REFERENCE_NUMBER, Warming scenario(1.5/2), RCP Scenario(4.5/8.5), discount factor and property price.

Default arguments values: VAR(building_id=None, target_temp=1.5, RCP_scenario=4.5, discount_factor=0.02, property_price=500000)

