This is a climate value at risk model for real estate asset in the UK. It covers all domestic and non-domestic properties with EPC certificates.

The way to use it:

Install crrem package: pip install crrem
Import VAR function: from crrem.var import VAR
Run the function by specifying 3 arguments: BUILDING_REFERENCE_NUMBER, Warming scenario(1.5/2), RCP Scenario(4.5/8.5), discount factor and property price.