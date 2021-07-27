def v1(*args):
    from cbm.foi import foi_v1
    return foi_v1.main(*args)


def v2(*args):
    from cbm.foi import foi_v2
    return foi_v2.main(*args)


def import_db_functions():
    from os.path import dirname, abspath, join, normpath, basename
    from cbm.datas import db
    from cbm.utils import config
    import glob

    path_foi_func = normpath(join(dirname(abspath(__file__)), 'foi_db_func'))
    functions = glob.glob(f"{path_foi_func}/*.func")
    db_conn = config.get_value(['set', 'db_conn'])
    schema = config.get_value(['db', db_conn, 'schema'])
    user = config.get_value(['db', db_conn, 'user'])
    for f in functions:
        db.insert_function(open(f).read().format(schema=schema, owner=user))
        if db.db_func_exist(basename(f).split('.')[0]):
            print(f"The '{basename(f)}' Was imported to the database.")
        else:
            print(f"Could not add function '{basename(f)}' to dattabase.")
