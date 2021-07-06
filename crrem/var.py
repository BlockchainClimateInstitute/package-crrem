import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style
style.use('ggplot')
from crrem.database import DataQ
import datetime
import warnings
warnings.filterwarnings("ignore")

#impport raw data
target_level = DataQ("select * from crrem.target_levels").data
target_type = DataQ("select * from crrem.target_type").data
property_type = DataQ("select * from crrem.vw_epc_to_crrem_prop_type").data
country = DataQ("select * from crrem.country").data
country_factor = DataQ("select * from crrem.country_factor").data
currency = DataQ("select * from crrem.currency").data
energy_source = DataQ("select * from crrem.energy_source").data
price = DataQ("select * from crrem.price").data
price.set_index('year', inplace=True)
price['price'] = price['price'].astype(float)
epc_main_fuel_mapping = DataQ("select * from crrem.epc_main_fuel_mapping").data
scenario_gw = DataQ("select * from crrem.scenario_gw").data
zip_nuts = DataQ("select * from crrem.zip_to_nuts").data
zip_nuts.set_index('zip_code', inplace=True)
energy_use_type = DataQ("select * from crrem.energy_use_type").data
hdd_cdd_by_nuts = DataQ("select * from crrem.hdd_cdd_by_nuts").data
hdd_cdd_by_nuts.set_index('nuts_code', inplace=True)
for col in hdd_cdd_by_nuts.columns[1:]: #impute missing values with mean
    mean = hdd_cdd_by_nuts[col].mean(skipna=True)
    hdd_cdd_by_nuts.loc[hdd_cdd_by_nuts[col]==0, col] = mean
hdd_cdd_by_nuts_normalization = DataQ("select * from crrem.hdd_cdd_by_nuts_normalization").data
hdd_cdd_by_nuts_normalization.set_index('nuts_lvl2', inplace=True)
vw_emission_factors = DataQ("select * from crrem.vw_emission_factors").data
vw_emission_factors.set_index('factor_year', inplace=True)
vw_emission_factors_others = DataQ("select * from crrem.vw_emission_factors_others").data
vw_emission_factors_others.set_index('energy_name', inplace=True)
property_use_type = DataQ("select * from crrem.property_use_type").data
property_use_type.set_index('use_type_name', inplace=True)
vw_gwp = DataQ("select * from crrem.vw_gwp").data
vw_gwp.set_index('gas_name',inplace=True)
vw_energy_use_per_type_country = DataQ("select * from crrem.vw_energy_use_per_type_country").data
vw_share_per_month_region = DataQ("select * from crrem.vw_share_per_month_region").data
vw_share_per_month_region.set_index('type',inplace=True)
vw_energy_cons_per_month_region = DataQ("select * from crrem.vw_energy_cons_per_month_region").data

class Building:
    def __init__(self, building_details, building_price, crrem_data='uk_epc'):
        #add 7 EPC columns as property_details, in a json object
        if crrem_data == 'crrem':
            self.epc = building_details
        elif crrem_data == 'uk_epc': 
            if type(building_details) is int:
                epc = DataQ(f"""select * from public.epcsourcedata where "BUILDING_REFERENCE_NUMBER" = {building_details} """).data
                self.epc = epc.set_index('BUILDING_REFERENCE_NUMBER')
                self.building_price = building_price
            elif type(building_details) is dict:
            	#deal with wrong NUTS codes
                if self.epc['NutsCode']=='UKK24' or 'UKK25':
                    self.epc['NutsCode'] = 'UKK23'
                #convert row of json to dataframe row
                self.epc = pd.DataFrame(data=building_details,index=[0])
        self.building_price = building_price
        self.stranding_year = None
        self.loss_vlaue = None

    def VAR(self, target_temp=1.5, RCP_scenario=4.5, discount_factor=0.02, end_year=2050, Diagram=False, crrem_data='uk_epc'):
    # /////////////////////////////////////////////////////////////////
    # Original CRREM Model
    # ///////////////////////////////////////////////////////////////// 
        if crrem_data == 'crrem':
            ## Estimate current emissions
            #set range of years for analysis
            years = list(range(2018,2051))
            '''
            a. data normalisation
            '''
            #1. weather noramlisation: heat/cool
            #AR, country acronym, set to UK 
            AR = 'UK'

            #AP: NUTS3
            ZIP = AR + str(self.epc['input_O'])
            AP = zip_nuts.loc[ZIP]['nuts_code'].iloc[0]

            cdd_level = hdd_cdd_by_nuts_normalization.loc[hdd_cdd_by_nuts_normalization['hdd_cdd'] == 'CDD']
            hdd_level = hdd_cdd_by_nuts_normalization.loc[hdd_cdd_by_nuts_normalization['hdd_cdd'] == 'HDD']
            try:
                if cdd_level.loc[AP[:4]]['2018_lvl']!=0:
                    AXA = cdd_level.loc[AP[:4]]['avg']/cdd_level.loc[AP[:4]]['2018_lvl']
                elif cdd_level.loc[AP[:4]]['2018_lvl']==0:
                    AXA = 1

                if hdd_level.loc[AP[:4]]['2018_lvl']!=0:
                    AWZ = hdd_level.loc[AP[:4]]['avg']/hdd_level.loc[AP[:4]]['2018_lvl']
                elif hdd_level.loc[AP[:4]]['2018_lvl']==0:
                    AWZ = 1
            except KeyError:
                AXA = 1
                AWZ = 1
                
            #2. data coverage normalisation
            if self.epc['input_AQ']!= 0:
                AWT = self.epc['input_AR']/self.epc['input_AQ']
            else:
                AWT = 0

            if self.epc['input_AG']!= 0:
                AWQ = self.epc['input_AR']/self.epc['input_AG']
            else:
                AWQ = 0

            if self.epc['input_AJ']!= 0:
                AWR = self.epc['input_AR']/self.epc['input_AJ'] 
            else:
                AWR= 0

            if self.epc['input_AM']!= 0:
                AWS = self.epc['input_AR']/self.epc['input_AM'] 
            else:
                AWS = 0

            if self.epc['input_AU']!= 0:
                AWU = self.epc['input_AR']/self.epc['input_AU'] 
            else:
                AWU = 0

            if self.epc['input_AY']!= 0:
                AWV = self.epc['input_AR']/self.epc['input_AY'] 
            else:
                AWV = 0

            #3. month noramlisation
            AWX = 12/self.epc['input_AJ'] #month normalisation

            #4. vacant area normalisation
            AWY = self.epc['input_AR']/(self.epc['input_AR']-self.epc['input_AD']) 

            #5. Electricity normalisation by month across different regions(North Atlantic, Continental, Mediterranean)
            #CTX - CUS
            #CTZ - starting month number
            CTZ = datetime.datetime.strptime(self.epc['input_I'], "%B").month

            #CUA - ending month number
            CUA = CTZ + self.epc['input_J'] - 1
            #CUB_CUM: Month included

            months = list(range(1,13))
            CUB_CUM = list(range(1,13))
            for month in months:
                if (month >= CTZ and month <= CUA) or (month+12 >= CTZ and month+12 <= CUA):
                        CUB_CUM[month-1] = 1
                else:
                    CUB_CUM[month-1] = 0

            #CTX/CTY/CUN
            CUB_CUM_i = pd.DataFrame(CUB_CUM).reset_index().drop(['index'], axis = 1)
            CUS = 1/(CUB_CUM_i*pd.DataFrame(vw_energy_cons_per_month_region['percentage'][-12:]).reset_index().drop(columns='index').rename(columns = {'percentage': 0})).sum()[0]

            #CUO: Heat_norm_12
            CUN3 = pd.DataFrame(vw_share_per_month_region.loc[vw_share_per_month_region.index=='1']['percentage'])
            CUN3 = CUN3.reset_index().drop(columns='type').rename(columns = {'percentage': 0})
            CUO = 1/(CUB_CUM_i * CUN3).sum()[0]

            #CUQ: Cool_norm_12
            CUP3 = pd.DataFrame(vw_share_per_month_region.loc[vw_share_per_month_region.index=='2']['percentage'])
            CUP3 = CUP3.reset_index().drop(columns='type').rename(columns = {'percentage': 0})
            CUQ = 1/(CUB_CUM_i * CUP3).sum()[0]

            '''
            b. BI_CO - HDD index and CT_DZ - CDD index
            '''

            #BI_CO - HDD index
            BI_CO = pd.Series(0.0,index=years)
            for year in years:
                if RCP_scenario == 4.5:
                    BI_CO[year] = ((hdd_cdd_by_nuts.loc[AP]['hdd_2015'] + (year-2015)*hdd_cdd_by_nuts.loc[AP]['hdd_rcp45_pa'])/(hdd_cdd_by_nuts.loc[AP]['hdd_2015'] + 3*hdd_cdd_by_nuts.loc[AP]['hdd_rcp45_pa']))
                elif RCP_scenario == 8.5:
                    BI_CO[year] = ((hdd_cdd_by_nuts.loc[AP]['hdd_2015'] + (year-2015)*hdd_cdd_by_nuts.loc[AP]['hdd_rcp85_pa'])/(hdd_cdd_by_nuts.loc[AP]['hdd_2015'] + 3*hdd_cdd_by_nuts.loc[AP]['hdd_rcp85_pa']))

            #CT_DZ - CDD index
            CT_DZ = pd.Series(0.0,index=years)
            for year in years:
                if RCP_scenario == 4.5:
                    CT_DZ[year] = ((hdd_cdd_by_nuts.loc[AP]['cdd_2015'] + (year-2015)*hdd_cdd_by_nuts.loc[AP]['cdd_rcp45_pa'])/(hdd_cdd_by_nuts.loc[AP]['cdd_2015'] + 3*hdd_cdd_by_nuts.loc[AP]['cdd_rcp45_pa']))
                elif RCP_scenario == 8.5:
                    CT_DZ[year] = ((hdd_cdd_by_nuts.loc[AP]['cdd_2015'] + (year-2015)*hdd_cdd_by_nuts.loc[AP]['cdd_rcp85_pa'])/(hdd_cdd_by_nuts.loc[AP]['cdd_2015'] + 3*hdd_cdd_by_nuts.loc[AP]['cdd_rcp85_pa']))

            '''
            c. KA:KH: emission share
            '''
            #KA: export emission
            A32_year = vw_emission_factors.loc[self.epc['input_F']]['value']

            #slice A32 for UK 2018
            A32_UK_base = vw_emission_factors.loc[years[0]]['value']

            #slice A32 for 2018
            A32_base = vw_emission_factors.loc[years[0]]['value']

            KA = -AWT*self.epc['input_BQ']*vw_emission_factors_others.loc['District Heating (Steam)']['kgco2e_per_kwh']-AWQ*self.epc['input_BL']*A32_year

            #JT - JZ
            #JT - Electricity emission
            JT = AWQ*(self.epc['input_AF']-self.epc['input_BM'])*A32_base + self.epc['input_BM']*A32_year

            #JU - Gas emission
            JU = AWR*self.epc['input_AI']*vw_emission_factors_others.loc['Natural Gas']['kgco2e_per_kwh']

            #JV - Oil emission
            JV = AWS*self.epc['input_AL']*vw_emission_factors_others.loc['Fuel Oil']['kgco2e_per_kwh']

            #JW - District heating emission
            JW = AWT*self.epc['input_AO']*vw_emission_factors_others.loc['District Heating (Steam)']['kgco2e_per_kwh']*A32_base/A32_UK_base

            #JX - District cooling emission
            JX = AWU*self.epc['input_AS']*vw_emission_factors_others.loc['District Heating (Steam)']['kgco2e_per_kwh']*A32_base/A32_UK_base

            #JY - Other emission # can add another
            JY = 0
            for energy, amount in zip(self.epc['input_AW'],self.epc['input_AX']):
                emission_factor = vw_emission_factors_others.loc[energy]['kgco2e_per_kwh']
                JY += AWV*amount*emission_factor

            #JZ - Fugitive emission  # can add another
            #fugitive gas - global warming potential
            C63_BF = vw_gwp.loc[self.epc['input_BF']]['gwp']
            AT = C63_BF*self.epc['input_BG'] #leak
            JZ = AT

            #Total emission calculation
            #KJ: AS.LENG_norm 
            KJ = JT*CUS+(JU+JV+JW+JY)*CUO+JX*CUQ+JZ*AWX+KA*AWX

            # KB: Electricity emission share
            KB = JT/(JT+JU+JV+JW+JX+JY+JZ)

            # KC: Gas emission share
            KC = JU/(JT+JU+JV+JW+JX+JY+JZ)

            # KD: Oil emission share
            KD = JV/(JT+JU+JV+JW+JX+JY+JZ)

            # KE: Gas emission share
            KE = JW/(JT+JU+JV+JW+JX+JY+JZ)

            # KF: Gas emission share
            KF = JX/(JT+JU+JV+JW+JX+JY+JZ)

            # KG: Gas emission share
            KG = JY/(JT+JU+JV+JW+JX+JY+JZ)

            # KH: Gas emission share
            KH = JZ/(JT+JU+JV+JW+JX+JY+JZ)

            '''
            d. KK: final total emissions(kgCO2e)
            '''
            KK = -KA+(KJ+KA)*(AWY*KB*(1+(vw_energy_use_per_type_country['percentage'][1]/100)*(BI_CO[years[0]]*AWZ-1) 
                        + vw_energy_use_per_type_country['percentage'][0]/100*(CT_DZ[years[0]]*AXA-1)) + (KC+KD+KE)
                        * (1+(vw_energy_use_per_type_country['percentage'][2]/100*(BI_CO[years[0]]*AWZ-1)))*AWZ+KF*AXA)

            '''
            e. EE_FK: grid index
            '''
            EE_FK = pd.Series(0.0,index=years)
            for year in years:
                EE_FK[year] = (vw_emission_factors.loc[year]['value']/vw_emission_factors.loc[years[0]]['value'])

            '''
            f. CZZ_DBF: Electricity procurement
            '''
            CZZ = AWQ*self.epc['input_AF']*AWY*((1+(vw_energy_use_per_type_country['percentage'][1]/100*(BI_CO[years[0]]*AWZ-1))+(vw_energy_use_per_type_country['percentage'][0]/100*(CT_DZ[years[0]]*AXA-1))))*CUS
            '''
            g. KP: emissions projection(kgCO2e)
            '''
            KP = pd.Series(0.0,index=years)
            for year in years:
                KP[year] = KK*(KB*(((EE_FK[year]/EE_FK[years[0]])*(self.epc['input_AF']/CZZ)
                +(1-self.epc['input_AF']/CZZ))*(1+vw_energy_use_per_type_country['percentage'][1]/100*(BI_CO[year]-1))) + (KC+KD+KG)*
                (BI_CO[year]/BI_CO[years[0]])*(1+vw_energy_use_per_type_country['percentage'][2]/100*(BI_CO[year]-1))
                + KF*(CT_DZ[year]/CT_DZ[years[0]]) + KE*BI_CO[year]+KH)

            '''
            h. MA: emissions intensity projection(kgCO2e/m2)
            '''
            MA = KP/self.epc['input_AC']

            '''
            i. emission_target
            '''
            property_type_id = property_use_type.loc[self.epc['input_Q']]['prop_use_type_id']

            # specify target based on property type/target type/scenario
            years = list(range(2018,end_year+1))
            if target_temp == 1.5:
                gw_scenario_id = 1
            elif target_temp == 2.0:
                gw_scenario_id = 2
            emission_target = target_level[(target_level['prop_use_type_id']==property_type_id) & (target_level['target_type_id']==1) & (target_level['gw_scenario_id']==gw_scenario_id)]['target_level']
            emission_target = emission_target[:end_year-2018+1]
            emission_target.index = years

            '''
            j. VAR
            '''
            ## VAR calculation
            floor_area = self.epc['input_AC']
            emission = MA
            total_emission = emission * floor_area
            total_target = emission_target * floor_area
            carbon_price = price[price['source']=='carbon']['price'][:end_year-2018+1]
            excess_cost = carbon_price * (total_emission - total_target)

            costs = pd.Series(np.nan, index=years)
            value = pd.Series(np.nan, index=years)
            for year in years:
                if excess_cost[year] < 0:
                    costs[year] = 0
                    value[year] = excess_cost[year]
                else:
                    costs[year] = excess_cost[year]
                    value[year] = 0

            discount_costs = costs.tolist().copy()
            discount_value = value.tolist().copy()

            for year in years:
                discount_costs[year - 2018] = discount_costs[year - 2018] / (1 + discount_factor) ** (year - 2018)
                discount_value[year - 2018] = discount_value[year - 2018] / (1 + discount_factor) ** (year - 2018)

            VAR = (sum(discount_costs) + sum(discount_value)) / self.building_price
            
            #stranding year and loss value
            stranding = emission_target - emission
            self.stranding_year = stranding[stranding < 0].index[0]
            self.loss_value = sum(discount_costs) + sum(discount_value)
            
            '''
            k. Plotting
            '''
            if Diagram == True:
                #import MA as emission metric
                Baseline = [emission.iloc[0]]*len(emission) #create baseline pandas series with same index as climate_grid
                baseline = pd.Series(Baseline, index = emission.index)   

                #plot diagram
                plt.figure(figsize = (20,10))
                plt.plot(emission_target, 'g', label = 'Decarbonisation target')
                plt.plot(emission, 'k', label = 'Climate and grid corrected asset performance')
                plt.plot(baseline, ':k', label = 'Baseline asset performance')
                plt.plot(baseline.iloc[[0]],'kD', markersize = 10, label = '2018 performance') 

                #highlight stranding year
                plt.plot(emission[[self.stranding_year]], 'ro', markersize = 20, label = 'Stranding')

                #Excess emissions
                plt.fill_between(years, emission_target.tolist(), emission.tolist(), where = (emission_target < emission), color='C1', alpha=0.3, label = 'Excess emissions')
                plt.legend(loc = 'best', fontsize = 12)

                #set title and axis labels
                plt.title(f'Stranding Diagram', fontsize = 25)
                plt.xlabel('Year', fontsize = 15)
                plt.ylabel('GHG intensity [kgCO2e/m²/a]', fontsize = 15)
                plt.show()
            
    # /////////////////////////////////////////////////////////////////
    # EPC Model
    # /////////////////////////////////////////////////////////////////  
        elif crrem_data == 'uk_epc':
            '''
            a. Data preparation GHG emission target
            '''
            # find property type id
            property_type_id = property_type.loc[property_type['epc_prop_type'] == self.epc['PROPERTY_TYPE'].iloc[0]]['prop_use_type_id'].iloc[0]

            # specify target based on property type/target type/scenario
            years = list(range(2018,end_year+1))
            if target_temp == 1.5:
                gw_scenario_id = 1
            elif target_temp == 2.0:
                gw_scenario_id = 2
            emission_target = target_level[(target_level['prop_use_type_id']==property_type_id) & (target_level['target_type_id']==1) & (target_level['gw_scenario_id']==gw_scenario_id)]['target_level']
            emission_target = emission_target[:end_year-2018+1]
            emission_target.index = years
            energy_target = target_level[(target_level['prop_use_type_id']==property_type_id) & (target_level['target_type_id']==2) & (target_level['gw_scenario_id']==gw_scenario_id)]['target_level']
            energy_target = energy_target[:end_year-2018+1]
            energy_target.index = years

            # HDD/CDD projection
            # HDD - HDD index
            RCP = 'RCP' + str(RCP_scenario)

    #         if self.epc['POSTCODE'].iloc[0] != 0:
    #             NUTS3 = 'UK' + self.epc['POSTCODE'].iloc[0].split(' ')[0]

            years_index = list(range(3, 36))
            HDD = pd.DataFrame(columns=years_index, index=[1])
            for year in years_index:
                if RCP == 'RCP4.5':
                    if len(self.epc['NutsCode']) > 1:
                        HDD.iloc[0, year - 3] = (hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_2015'].iloc[0] + year *
                                                 hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_rcp45_pa'].iloc[0]) / (
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']][
                                                                'hdd_2015'].iloc[0] + 3 *
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_rcp45_pa'].iloc[0])
                    else:
                        HDD.iloc[0, year - 3] = (hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_2015'].iloc[0] + year *
                                                 hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_rcp45_pa'].iloc[0]) / (
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_2015'].iloc[0] + 3 *
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_rcp45_pa'].iloc[0])
                elif RCP == 'RCP8.5':
                    if len(self.epc['NutsCode']) > 1:
                        HDD.iloc[0, year - 3] = (hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_2015'].iloc[0] + year *
                                                 hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_rcp85_pa'].iloc[0]) / (
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']][
                                                                'hdd_2015'].iloc[0] + 3 *
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_rcp85_pa'].iloc[0])
                    else:
                        HDD.iloc[0, year - 3] = (hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_2015'].iloc[0] + year *
                                                 hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_rcp85_pa'].iloc[0]) / (
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_2015'].iloc[0] + 3 *
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['hdd_rcp85_pa'].iloc[0])

            # assumption1: if one zip macthes multiple nuts, take the first nuts
            # CDD - CDD index
            CDD = pd.DataFrame(columns=years_index, index=[1])
            for year in years_index:
                if RCP == 'RCP4.5':
                    if len(self.epc['NutsCode']) > 1:
                        CDD.iloc[0, year - 3] = (hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_2015'].iloc[0] + year *
                                                 hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_rcp45_pa'].iloc[0]) / (
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']][
                                                                'cdd_2015'].iloc[0] + 3 *
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_rcp45_pa'].iloc[0])
                    else:
                        CDD.iloc[0, year - 3] = (hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_2015'].iloc[0] + year *
                                                 hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_rcp45_pa'].iloc[0]) / (
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_2015'].iloc[0] + 3 *
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_rcp45_pa'].iloc[0])
                else:
                    if len(self.epc['NutsCode']) > 1:
                        CDD.iloc[0, year - 3] = (hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_2015'].iloc[0] + year *
                                                 hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_rcp85_pa'].iloc[0]) / (
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']][
                                                                'cdd_2015'].iloc[0] + 3 *
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_rcp85_pa'].iloc[0])
                    else:
                        CDD.iloc[0, year - 3] = (hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_2015'].iloc[0] + year *
                                                 hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_rcp85_pa'].iloc[0]) / (
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_2015'].iloc[0] + 3 *
                                                            hdd_cdd_by_nuts.loc[self.epc['NutsCode']]['cdd_rcp85_pa'].iloc[0])
            CDD.columns = list(range(2018, 2051))
            HDD.columns = list(range(2018, 2051))
            HDD.fillna(0, inplace=True)
            CDD.fillna(0, inplace=True)
            HDD = HDD.iloc[:,:end_year-2018+1]
            CDD = CDD.iloc[:,:end_year-2018+1]

            '''
            b. GHG emission projection
            '''
            # emission data
            #impute missing data with median of property type
            if self.epc['CO2_EMISS_CURR_PER_FLOOR_AREA'].iloc[0] == None:
                current_emission = self.epc['CO2_EMISS_CURR_PER_FLOOR_AREA_Median'].iloc[0]
            else:
                current_emission = self.epc['CO2_EMISS_CURR_PER_FLOOR_AREA'].iloc[0]
            if self.epc['ENERGY_CONSUMPTION_CURRENT'].iloc[0] == None:
                current_energy = self.epc['ENERGY_CONSUMPTION_CURRENT_Median'].iloc[0]
            else:
                current_energy = self.epc['ENERGY_CONSUMPTION_CURRENT'].iloc[0]

            elec_heat = vw_energy_use_per_type_country['percentage'][1] / 100  # share of electricity for heating in UK
            elec_cool = vw_energy_use_per_type_country['percentage'][0] / 100
            fuel_heat = vw_energy_use_per_type_country['percentage'][2] / 100
            grid = vw_emission_factors['value']  # emission factor for UK
            start = grid[2018]
            for i in grid.index:
                grid[i] = grid[i]/start

            # electricity usage share
            electricity_share = epc_main_fuel_mapping.loc[epc_main_fuel_mapping['epc_main_fuel'] == self.epc['MAIN_FUEL'].iloc[0]]['weight_elec'].iloc[0]
            elec_energy = current_energy*electricity_share
            elec_procured = elec_energy*((1+(elec_heat*(HDD.iloc[0, 0]-1)+elec_cool*(CDD.iloc[0, 0]-1))))

            emission = pd.Series(0, index=list(range(2018, 2051)))

            # assumption 2: district heating/cooling and fugitive emission not considered
            for year in years:
                emission.iloc[year - 2018] = current_emission*(electricity_share*(((grid[year]/grid[2018])
                            *(elec_energy/elec_procured)+(1-elec_energy/elec_procured))
                            *(1+elec_heat*(HDD.iloc[0, year-2018]-1)+elec_cool*(CDD.iloc[0, year-2018]-1)))
                            +(1 - electricity_share)*(HDD.iloc[0, year - 2018]/HDD.iloc[0, 2018 - 2018])
                            *(1 + fuel_heat*(HDD.iloc[0, year - 2018])))

            emission = emission[:end_year-2018+1]
            emission_baseline = pd.Series(emission[2018])
            emission_baseline = emission_baseline.repeat(len(emission.T))
            emission_baseline.index = years 
            emission_excess = emission - emission_target
            if len(emission_excess[emission_excess > 0]) == 0:
                emission_stranding_year = 2050
            else:
                emission_stranding_year = emission_excess[emission_excess > 0].index[0]

            '''
            c. VAR
            '''
            carbon_price = price[price['source']=='carbon']['price'][:end_year-2018+1] #carbon price incl. VAT
            floor_area = self.epc['TOTAL_FLOOR_AREA'].iloc[0]
            total_emission = emission * floor_area
            total_target = emission_target * floor_area
            excess_cost = carbon_price * (total_emission - total_target)

            costs = pd.Series(np.nan, index=years)
            value = pd.Series(np.nan, index=years)
            for year in years:
                if excess_cost[year] < 0:
                    costs[year] = 0
                    value[year] = excess_cost[year]
                else:
                    costs[year] = excess_cost[year]
                    value[year] = 0

            discount_costs = costs.tolist().copy()
            discount_value = value.tolist().copy()

            for year in years:
                discount_costs[year - 2018] = discount_costs[year - 2018] / (1 + discount_factor) ** (year - 2018)
                discount_value[year - 2018] = discount_value[year - 2018] / (1 + discount_factor) ** (year - 2018)

            VAR = (sum(discount_costs) + sum(discount_value)) / self.building_price

            self.stranding_year = emission_stranding_year
            self.loss_value = sum(discount_costs) + sum(discount_value)
            '''
            d. Plotting
            '''
            if Diagram == True:
                years = list(range(2018,end_year+1))
                plt.figure(figsize = (20,10))
                plt.plot(emission_target, 'g', label = 'Decarbonisation emission_target')
                plt.plot(emission, 'k', label = 'Climate and grid corrected asset performance')
                plt.plot(emission_baseline, ':k', label = 'emission_baseline asset performance')
                plt.plot(emission_baseline.iloc[[0]],'kD', markersize = 10, label = '2018 performance') 

                #highlight stranding year
                plt.plot(emission[[self.stranding_year]], 'ro', markersize = 20, label = 'Stranding')

                #Excess emissions
                plt.fill_between(years, emission_target.tolist(), emission.tolist(), where = (emission_target < emission), color='C1', alpha=0.3, label = 'Excess emissions')
                plt.legend(loc = 'best', fontsize = 12)

                #set title and axis labels
                plt.title(f'Stranding Diagram(Asset #{self.epc.index.tolist()[0]})', fontsize = 25)
                plt.xlabel('Year', fontsize = 15)
                plt.ylabel('GHG intensity [kgCO2e/m²/a]', fontsize = 15)
                plt.show()

        return VAR

class Portfolio:
    def __init__(self, buildings):
        self.buildings = buildings
    
    def add_building(self, building):
        self.buildings.append(building)
        
    def VAR(self,target_temp=1.5, RCP_scenario=4.5, discount_factor=0.02, end_year=2050, Diagram=False, crrem_data='uk_epc'):
        total_loss = 0
        total_price = 0
        years = list(range(2018,end_year+1))
        
        strand_buildings = pd.Series(0, index=years)
        for building in self.buildings:
            building.VAR(target_temp=target_temp, RCP_scenario=RCP_scenario, discount_factor=discount_factor, end_year=end_year, Diagram=False, crrem_data=crrem_data)
            total_loss += building.loss_value
            total_price += building.building_price
            if building.stranding_year < end_year:
                strand_buildings[building.stranding_year] += 1
        if Diagram == True:
            strand_buildings = strand_buildings.cummax()
            plt.figure(figsize = (20,10))
            plt.plot(strand_buildings, 'g', label = 'Decarbonisation emission_target')
            plt.title('Number of stranding assets over time', fontsize=25)
            plt.show()          
        return total_loss/total_price