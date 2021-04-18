This is a climate value at risk model for real estate asset and portfolio in the UK. It covers all domestic and non-domestic properties with EPC certificates.

The way to use it:

1. Install crrem package: pip install crrem
2. To import class: from crrem.var import Building, Portfolio

There are two classes in the UK depending on your use case:
You can either:

1. Conduct asset-level analysis with class Building using methods VAR to calculate climate value at risk or have the option to see the stranding diagram. When initialising Building, you need to specify Building(building_id, property_price), where building_id is from EPC's BUILDING_REFERENCE_NUMBER, property_price is self-defined price of the property. 

2. Conduct portfolio-level analysis with class Portfolio using VAR to calculate climate value at risk and have the option to see the plot of the number of stranding assets over time. When initialising Portfolio, you need to specify Portfolio(buildings), where buildings is a list of Building instances.


VAR default arguments for both classes: (target_temp=1.5, RCP_scenario=4.5, discount_factor=0.02, end_year=2050, Diagram=True)


