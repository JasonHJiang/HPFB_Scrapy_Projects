from elasticsearch import Elasticsearch, exceptions
from elasticsearch import helpers

### list of new active substances ###
nas = ["Lancora","Lixiana","Praluent","Uptravi","Zontivity","Blexten","Rupatadine","Taltz","Dotarem","MDK-Nitisinone","Nitisinone Tablets","Orfadin","Ravicti","Epclusa","Sunvepra","Xtoro","Zepatier","BAT","Bridion","Brivlera","Zinbryta","Adynovate","Afstyla","Alecensaro","Cotellic","Darzalex","Empliciti","Ibrance","Idelvion","Kyprolis","Lynparza","Ninlaro","Praxbind","Tagrisso","Venclexta","Cinqair","Orkambi"]
notyet = []
already = []
for ele in nas:
    res=es.search(index="drug_mono5*", body={"query": {"match_phrase": {"pm_page_one": ele}}})
    if (res['hits']['total'] != 0):
        print('yes')
        already.append(ele)
    else:
        print(ele)
        notyet.append(ele)

### Check whether NAS are on already in the index drug_mono5, if so, reindex them to new_active_substance;
### otherwise, scrape them by using Scrapy spider. 
        
es_src = Elasticsearch('http://elastic-gate.hc.local:80')
for ele in already:
    body = {"query": {"match_phrase": {"pm_page_one": ele}}}
    helpers.reindex(es_src, 'drug_mono5', 'new_active_substance',query=body)

### Combine ATC Codes ###
atc_df = pd.read_csv('updated_atc.csv', delimiter=',')
atc_list = []
for i in range(0,len(atc_df)):
    atc_code_short = atc_df['atc_code5'][i]
    atc_code_long = atc_df['atc_code1'][i] + '/'+atc_df['atc_code2'][i] + '/'+atc_df['atc_code3'][i] + '/'+atc_df['atc_code4'][i] + '/'+atc_df['atc_code5'][i]
    atc_code_desc = atc_df['atc_desc1'][i] + '/' + atc_df['atc_desc2'][i] + '/' + atc_df['atc_desc3'][i] + '/' + atc_df['atc_desc4'][i] + '/' + atc_df['atc_desc5'][i]
    atc_list.append([atc_code_short,atc_code_long,atc_code_desc])

### already_list includes PM numbers for all NAS that are already in the index new_active_substance 
### update their information by linking corresponding rows in the Master table
    
already_list = [00035488,00037208,00034574,00035253,00034224,00035744,00033418,00036372,00038667,00037160,00038206,00035497,00034296,00034135,00036648,00033728,00037753,00037169,00037720,00035572,00035596,00035897,00035758,00037831,00033433,00037776,00037668,00037220,00037539,00037011,00035229,00036371,00022870,00023900,00023901,00037358,00033680,00034348,00034816,00036333,00035616,00037035,00037012,00033863,00035402,00037132,00037131,00035073,00038374,00033628,00037183,00036522,00035378,00033437,00033354,00034821,00036605,00034918,00035093,00034041,00033417,00036652,00036559,00034017,00036768,00037890,00034692,00034693,00036661,00038529,00035778,00038559,00034014,00037118,00037182,00033797,00037982,00035463,00037570,00033502,00034876,00035983,00036576,00038484]
xl = pd.ExcelFile('Superlist_Rebuild_Aug_10_2017.xlsx')
df = xl.parse('Masterlist July')
df = df[['Drug Code','Drug Product (DIN name)','DIN','PM ENG','PM FR','ATC Code']]
df = df.drop_duplicates()
# already_list = [4619,4620,4621,9983,9984,9985,9986,9987,9988,9989,9990,2048,9072,9073,7912,3311,10421,2072,2076,2077,2078,2079,2080,613,2618,2711,2712,3929,3930,3931,4468,4469,4470,4715,5819,5820,5821,7231,9070,9071,10159,10160,10161,10162,2381]
df_already = df.ix[already_list]
df_already = df_already.groupby('PM ENG', as_index=False).agg(lambda x: x.tolist())
already_list_pm_eng = list(df_already['PM ENG'])
already_list_pm_fr = list(df_already['PM FR'])

### format PM numbers into 8 digits ###
for i in range(0,len(already_list_pm_eng)):
    already_list_pm_eng[i] = str('{0:08}'.format(int(df_already['PM ENG'][i])))

for i in range(0,len(already_list_pm_fr)):
    for j in range(0,len(already_list_pm_fr[i])):
        #already_list_pm_fr[i][j] = float(already_list_pm_fr[i][j])
        if (math.isnan(already_list_pm_fr[i][j])):
            already_list_pm_fr[i][j] = ''
        else:
            already_list_pm_fr[i][j] = str('{0:08}'.format(int(already_list_pm_fr[i][j])))

for i in range(0,len(already_list_pm_fr)):
    already_list_pm_fr[i] = list(set(already_list_pm_fr[i]))

### Contents to be updated ###
already_list_din = list(df_already['DIN'])
for i in range(0,len(already_list_din)):
    already_list_din[i] = list(set(already_list_din[i]))

already_list_drug_code = list(df_already['Drug Code'])
for i in range(0,len(already_list_drug_code)):
    already_list_drug_code[i] = list(set(already_list_drug_code[i]))

already_list_drug_product = list(df_already['Drug Product (DIN name)'])
for i in range(0,len(already_list_drug_product)):
    already_list_drug_product[i] = list(set(already_list_drug_product[i]))

already_list_atc_code = list(df_already['ATC Code'])
for i in range(0,len(already_list_atc_code)):
    already_list_atc_code[i] = list(set(already_list_atc_code[i]))
    already_list_atc_code[i] = already_list_atc_code[i][0]

already_list_atc_code_desc = []
for i in range(0,len(already_list_atc_code)):
    atc_index = findItem(atc_list,already_list_atc_code[i])
    if atc_index == []:
        already_list_atc_code[i] = ''
        already_list_atc_code_desc.append('')
    else:
        already_list_atc_code[i] = atc_list[atc_index[0][1]]
        already_list_atc_code_desc.append(atc_list[atc_index[0][2]])

### Use the following script to update documents partially by query (change content manually) ###        
for i in range(0,len(df_already)):
    q = {
      "script": {
        "inline": "ctx._source.drug_product='%s'"%str(already_list_drug_product[i][0]),
        "lang": "painless"
      },
      "query": {
        "match": {
          "pm_number": already_list_pm_eng[i]
        }
      }
    }
    es.update_by_query(body=q,index='new_active_substance')
