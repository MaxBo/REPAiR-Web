import csv
import json

csvfile = open('links.csv', 'r')
jsonfile = open('links.json', 'w')
model = "studyarea.links"
fieldnames = ("id_from","id_to","weight")
reader = csv.DictReader( csvfile, fieldnames)
jsonfile.write("[\n")
i = 0
next(reader)
for fields in reader:
    row = {"model" : model, "pk" : i,"fields" : fields}
    json.dump(row, jsonfile)
    jsonfile.write(',\n')
    i += 1
jsonfile.write("]")