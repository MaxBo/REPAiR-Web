import os
import simplejson

def walk_up_folder(path, depth=1):
    """
    Create the basedirectory for a path
    """
    _cur_depth = 1
    while _cur_depth < depth:
        path = os.path.dirname(path)
        _cur_depth += 1
    return path

def get_json(csv_file, app, model, columns, join_cols=None):
    """
    Convert a csv file to a json fixture file that can be uploaded to the
    database.

    Parameters
    ----------
    csv_file: string
        path to the csv file
    app: string
        app name
    model: string
        model name
    columns: list of strings
        model attributes sorted by the occurance in the csv file
        if element is 'drop', it will not be included in the fixture file
    join_cols: list of tuples of int
        is the table contains values that include a ',' (for example floats)
        the two columns that are definded with the tuples are joined

    Return
    ------
    list of dicts in the shape of a fixture file
    """
    n_cols = len(columns)
    id_index = columns.index('id')
    model_name = '.'.join((app, model))
    with open(csv_file) as f:
        content = f.readlines()
    content = [line.strip('\n').split(',') for line in content]
    if join_cols:
        shift = 0
        for join in join_cols:
            first, secend = join
            secend += 1
            first -= shift
            secend -= shift
            for i in range(len(content)):
                if len(content[i]) > n_cols:
                    content[i][first:secend] = \
                        ['.'.join(content[i][first:secend])]
            shift += 1
    content_json = [dict(pk=line[id_index], model=model_name,
                         fields=dict(zip(*remove_id_drop(columns, line))))
                    for line in content]
    return content_json

def remove_id_drop(keys, values):
    """
    Remove the value for column and value list if the column name is id or drop
    """
    drop_ids = [keys.index('id')]
    for i, key in enumerate(keys):
        if key == 'drop':
            drop_ids.append(i)
    keys = keys.copy()
    keys = [keys[i] for i in range(len(keys)) if i not in drop_ids]
    values = [values[i] for i in range(len(values)) if i not in drop_ids]
    return [keys, values]



if __name__ == '__main__':
    # convert aims challenges and targets
    # base paths
    file_path = os.path.dirname(os.path.realpath(__file__))
    base_path = walk_up_folder(file_path, 3)  # ..../repair

    # get jsons from csvs:
    # targetvalues
    csv_args = ['apps', 'statusquo', 'fixtures', 'targetvalues']
    csv_file = os.path.join(base_path, *csv_args)
    targetvalues_json = get_json(csv_file, app='statusquo',
                                 columns=['id', 'text', 'number', 'factor'],
                                 model='targetvalue',
                                 join_cols=[(2, 3), (4, 5)])
    # target
    csv_args = ['apps', 'statusquo', 'fixtures', 'targets']
    csv_file = os.path.join(base_path, *csv_args)
    target_json = get_json(csv_file, app='statusquo',
                                 columns=['drop', 'user', 'id', 'aim',
                                          'impact_category', 'target_value',
                                          'spatial_reference'],
                                 model='target')
    # targetspatialreference
    csv_args = ['apps', 'statusquo', 'fixtures', 'targetspatialreference']
    csv_file = os.path.join(base_path, *csv_args)
    targetspatialreference_json = get_json(csv_file, app='statusquo',
                                           columns=['id', 'name', 'text'],
                                           model='targetspatialreference')
    # aims
    csv_args = ['apps', 'statusquo', 'fixtures', 'aims']
    csv_file = os.path.join(base_path, *csv_args)
    aims_json = get_json(csv_file, app='statusquo',
                                 columns=['casestudy', 'id', 'text', 'drop'],
                                 model='aim')
    # challenges
    csv_args = ['apps', 'statusquo', 'fixtures', 'challenges']
    csv_file = os.path.join(base_path, *csv_args)
    challenges_json = get_json(csv_file, app='statusquo',
                                 columns=['casestudy', 'id', 'text', 'drop'],
                                 model='challenge')
    # areasofprotection
    csv_args = ['apps', 'statusquo', 'fixtures', 'areasofprotection']
    csv_file = os.path.join(base_path, *csv_args)
    areasofprotection_json = get_json(csv_file, app='statusquo',
                                 columns=['id', 'name', 'sustainability_field'],
                                 model='areaofprotection')
    # sustainabilityfields
    csv_args = ['apps', 'statusquo', 'fixtures', 'sustainabilityfields']
    csv_file = os.path.join(base_path, *csv_args)
    sustainabilityfields_json = get_json(csv_file, app='statusquo',
                                 columns=['id', 'name'],
                                 model='sustainabilityfield')
    # impactcategroies
    csv_args = ['apps', 'statusquo', 'fixtures', 'impactcategories']
    csv_file = os.path.join(base_path, *csv_args)
    impactcategories_json = get_json(csv_file, app='statusquo',
                                 columns=['id', 'name', 'area_of_protection',
                                          'spatial_differentiation'],
                                 model='impactcategory', join_cols=[(1, 2)])
    # join all lists to create one json file
    json = target_json + targetvalues_json + targetspatialreference_json + \
        aims_json + challenges_json + sustainabilityfields_json + \
        impactcategories_json + areasofprotection_json

    out_args = ['fixtures', 'sandbox_aimschallengestargets.json']
    out_file = os.path.join(base_path, *out_args)
    out_file = open(out_file, 'w')
    simplejson.dump(json, out_file)
    out_file.close()
