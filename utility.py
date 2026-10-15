def download_fromStorage(bucket_name, file_key, sub_path):
    file_key = str(file_key)
    client = storage.Client()
    try:
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(sub_path)
        blob.download_to_filename("/tmp/" + file_key)
        print(True)
    except:
        print(False)

def grep(pattern, collection, values=False, regex=False):
    import re
    if regex:
        regex_pattern = re.compile(pattern)
        if values:
            reduce_r = reduce(lambda acc, x: acc + [x[0]] if x[1] else acc, enumerate(map(regex_pattern.findall, collection)), [])
            return reduce_r
        return list(filter(regex_pattern.findall, collection))
    else:
        if values:
            map_r = map(lambda x: pattern in x, collection)
            reduce_r = reduce(lambda acc, x: acc + [x[0]] if x[1] else acc, enumerate(map_r), [])
            return reduce_r
        return list(filter(lambda x: pattern in x, collection))

def chop(ls, notation):
    if len(notation) == 1:
        return [ls[int(notation)]]
    start = None
    end = None
    if ':' in notation:
        start_str, end_str = notation.split(':')
        start = int(start_str) if start_str else None
        end = int(end_str) if end_str else None
    return ls[start:end]

def get_last_iteration(x, delimiter):
    splitted = x.split(delimiter)
    last_string = next((s for s in reversed(splitted) if s), None)
    return(last_string)

def indices(indices, collection):
    map_r = map(lambda i: [collection[i]], indices)
    reduce_r = reduce(lambda x, y: x + y, map_r)
    return reduce_r

def read_json(file_path):
    with open(file_path) as json_file:
        r = json.load(json_file)
    return(r)

def clean_columns(df):
    columns = df.columns
    new_columns = [col.replace(' ', '_') for col in columns]
    new_columns = [col.replace(r'[^a-zA-Z0-9_]+', '_') for col in new_columns]
    for i in range(len(columns)):
        df = df.withColumnRenamed(columns[i], new_columns[i])
    return df

def drop_repeatingColumns(df, colName):
    return df.select([col for col in df.columns if col != colName])

def remove_trailing_slash(string):
    if string.endswith('/'):
        string = string[:-1]
    return string


def delete_bucket_objs(bucket, key, client):
    client = client
    blob = bucket.blob(key)
    blob.delete()

def readUserDataRTDB(user_id):
    ref = db.reference('/' + user_id)
    user_snapshot = ref.get()
    return user_snapshot

def readWorkspaceDataRTDB():
    ref = db.reference('/workspaces')
    workspace_info = ref.get()
    return workspace_info

def readTokenDataRTDB():
    ref = db.reference('/workspace_tokens')
    token_info = ref.get()
    return token_info

def getUserAccess(user_id):
    keys = ['access', 'cluster', 'warehouse', 'workspace']
    user_access = dict.fromkeys(keys)
    user_snapshot = readUserDataRTDB(user_id)
    user_snapshot = {key: user_snapshot[key] for key in keys}
    for i in range(len(keys)):
        access = []
        for key, value in user_snapshot[keys[i]].items():
            if value:
                access.append(key)
        user_access[keys[i]] = access
    print(user_access)
    return user_access

def getInstanceByWorkspaceName(workspace_names):
    instances = dict.fromkeys(workspace_names)
    workspace_snapshot = readWorkspaceDataRTDB()
    workspace_info = {key: workspace_snapshot[key] for key in workspace_names}
    for name in workspace_info:
        instance = workspace_info[name]['id'] + '.' + workspace_info[name]['subId']
        instances[name] = instance
    print(instances)
    return instances

def getTokenByWorkspaceName(workspace_names):
    token_snapshot = readTokenDataRTDB()
    tokens = {key: token_snapshot[key] for key in workspace_names}
    print(tokens)
    return tokens

def listClustersByWorkspace(user_id, workspace_names, api_urls):
    cluster_list = []
    tokens = getTokenByWorkspaceName(workspace_names)
    tokens = list(tokens.values())
    instances = getInstanceByWorkspaceName(workspace_names)
    instances = list(instances.values())

    for i in range(len(instances)):
        url = api_urls['clusters']['LIST'].replace('{INSTANCE}', instances[i])
        response = requests.get(url, headers = {'Authorization': 'Bearer %s' % tokens[i]}).json()
        if len(response) > 0:
            response_modified = [dict(item, **{'instance':instances[i]}) for item in response['clusters']]
            response_modified = [dict(item, **{'token':tokens[i]}) for item in response_modified]
            cluster_list.extend(response_modified)
        else:
            print("No clusters listed under %s workspace" % workspace_names[i])

    print(cluster_list)
    return cluster_list

def main_startStopClusterByName(action, user_id, workspace_name, cluster_name, api_urls):
    user_access = getUserAccess(user_id)
    cluster_access = user_access['cluster']
    
    cluster_list = listClustersByWorkspace(user_id, [workspace_name], api_urls)
    cluster_df = pd.DataFrame(cluster_list)
    cluster_index = cluster_df.loc[cluster_df['name'] == cluster_name].index[0]
    cluster_id = cluster_df.loc[cluster_index, 'id']

    if cluster_id in cluster_access:
        url = api_urls['clusters'][action.upper()].replace('{INSTANCE}', cluster_df.loc[cluster_index, 'instance'])
        post_data = {"cluster_id": cluster_id}
        response = requests.post(url, headers = {'Authorization': 'Bearer %s' % cluster_df.loc[cluster_index, 'token']}, json = post_data)
        if len(response.json()) == 0:
            print('Successfully completed action on the following cluster: %s' % cluster_name)
    else:
        print('User does not have access to the following cluster: %s' % cluster_name)

    return 'main_startStopClusterByName()'

def listSqlWarehousesByWorkspace(workspace_names, api_urls):
    warehouse_list = []
    tokens = getTokenByWorkspaceName(workspace_names)
    tokens = list(tokens.values())
    instances = getInstanceByWorkspaceName(workspace_names)
    instances = list(instances.values())

    for i in range(len(instances)):
        url = api_urls['warehouses']['LIST'].replace('{INSTANCE}', instances[i])
        response = requests.get(url, headers = {'Authorization': 'Bearer %s' % tokens[i]}).json()
        if len(response) > 0:
            response_modified = [dict(item, **{'instance':instances[i]}) for item in response['warehouses']]
            response_modified = [dict(item, **{'token':tokens[i]}) for item in response_modified]
            warehouse_list.extend(response_modified)
        else:
            print("No warehouses listed under %s workspace" % workspace_names[i])

    print(warehouse_list)
    return warehouse_list

def getSqlWarehouseByName(workspace_name, warehouse_name, api_urls):
    warehouse_list = listSqlWarehousesByWorkspace([workspace_name], api_urls)
    warehouse_df = pd.DataFrame(warehouse_list)
    warehouse_index = warehouse_df.loc[warehouse_df['name'] == warehouse_name].index[0]

    url = api_urls['warehouses']['GET'].replace('{INSTANCE}', warehouse_df.loc[warehouse_index, 'instance'])
    url = url.replace('{ID}', warehouse_df.loc[warehouse_index, 'id'])
    response = requests.get(url, headers = {'Authorization': 'Bearer %s' % warehouse_df.loc[warehouse_index, 'token']})

    return response.json()

def main_createSqlWarehouse(user_id, workspace_name, warehouse_name, cluster_size, max_num_clusters, api_urls, min_num_clusters = None, auto_stop_mins = None,
                            spot_instance_policy = None, enable_photon = None, enable_serverless_compute = None, warehouse_type = None, channel = None):
    instance = getInstanceByWorkspaceName([workspace_name])
    token = getTokenByWorkspaceName([workspace_name])
    warehouse_create = {
        "name": warehouse_name,
        "cluster_size": cluster_size,
        "min_num_clusters": min_num_clusters,
        "max_num_clusters": max_num_clusters,
        "auto_stop_mins": auto_stop_mins,
        "spot_instance_policy": spot_instance_policy,
        "enable_photon": enable_photon,
        "enable_serverless_compute": enable_serverless_compute,
        "warehouse_type": warehouse_type,
        "channel": channel
    }
    warehouse_create = {key:value for key, value in warehouse_create.items() if value != None}
    url = api_urls['warehouses']['CREATE'].replace('{INSTANCE}', instance[workspace_name])
    response = requests.post(url, headers = {'Authorization': 'Bearer %s' % token[workspace_name]}, json = warehouse_create)
    return response.json()

# SQL Warehouses: start, stop, edit, delete
def main_actionSqlWarehouseByName(action, user_id, workspace_name, warehouse_name, api_urls, update_fields = None, update_values = None):
    user_access = getUserAccess(user_id)
    warehouse_access = user_access['warehouse']
    post_data = None

    warehouse_list = listSqlWarehousesByWorkspace([workspace_name], api_urls)
    warehouse_df = pd.DataFrame(warehouse_list)
    warehouse_index = warehouse_df.loc[warehouse_df['name'] == warehouse_name].index[0]
    warehouse_id = warehouse_df.loc[warehouse_index, 'id']

    if action == 'edit':
        post_data = {key: value for key, value in zip(update_fields, update_values)}

    if warehouse_id in warehouse_access:
        url = api_urls['warehouses'][action.upper()].replace('{INSTANCE}', warehouse_df.loc[warehouse_index, 'instance'])
        url = url.replace('{ID}', warehouse_id)
        response = requests.post(url, headers = {'Authorization': 'Bearer %s' % warehouse_df.loc[warehouse_index, 'token']}, json = post_data)
        if len(response.json()) == 0:
            print('Successfully completed action on the following warehouse: %s' % warehouse_name)
    else:
        print('User does not have access to the following warehouse: %s' % warehouse_name)

    return 'main_actionSqlWarehouse()'