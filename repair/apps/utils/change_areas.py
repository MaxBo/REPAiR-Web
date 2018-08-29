import json
import csv
import simplejson

# load area data as json
area_data = open('./../../fixtures/sandbox_data.json').read()
area_data = json.loads(area_data)

# make dict of area and parent area:
area_parent_files = ['./studyarea_municipality.csv',
                     './studyarea_cityneighbourhood.csv',
                     './studyarea_nuts1.csv',
                     './studyarea_nuts3.csv']
parent_dict = dict()
for area_parent_file in area_parent_files:
    with open(area_parent_file, mode='r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            parent_dict[str(row[0])] = row[1]

# loop over all areas and append parent area:
for datapoint in area_data:
    model = datapoint['model']
    if model == 'studyarea.area':
        area_id = datapoint['pk']
        parent_id = parent_dict[str(area_id)]
        if parent_id == '':
            parent_id = None
        datapoint['fields']['_parent_area'] = parent_id

with open('./../../fixtures/sandbox_data_new.json', 'w') as fp:
    simplejson.dump(area_data, fp)