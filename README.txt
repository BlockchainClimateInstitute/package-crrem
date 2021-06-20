This is a climate value at risk model for real estate asset and portfolio in the UK. It covers all domestic and non-domestic properties with EPC certificates.

How to use:
       1. Install crrem package: pip install crrem
       2. To import class: from crrem.var import Building, Portfolio

There are two classes in the UK depending on your use case. You can either:

1. Conduct ASSET-LEVEL analysis with the Building class using methods VAR to calculate climate value at risk or have the option to see the stranding diagram. When initialising Building, you need to specify Building(building_details, building_price), where building_details is either building EPC's BUILDING_REFERENCE_NUMBER or a json object specifying users' own input, property_price is self-defined price of the property. 

here is an example json object: 
json = {
       'BUILDING_REFERENCE_NUMBER':5336094578,
       'PROPERTY_GROUPING':'Domestic',
       'PROPERTY_TYPE':'House',
       'CO2_EMISS_CURR_PER_FLOOR_AREA': 66.0,
       'MAIN_FUEL':'mains gas (not community)',
       'ENERGY_CONSUMPTION_CURRENT':375,
       'TOTAL_FLOOR_AREA':101.0,'NutsCode':'UKC11'}

2. Conduct PORTFOLIO-LEVEL analysis with the Portfolio class using VAR to calculate climate value at risk and have the option to see the plot of the number of stranding assets over time. When initialising Portfolio, you need to specify Portfolio(buildings), where buildings is a list of Building instances.


VAR default arguments for both classes: (target_temp=1.5, RCP_scenario=4.5, discount_factor=0.02, end_year=2050, Diagram=True)
