import sys
import pathlib
import configparser

# Run the configuration script when the user runs
# python3 -m asilib [init, initialize, config, or configure]

here = pathlib.Path(__file__).parent.resolve()


if (len(sys.argv) > 1) and (sys.argv[1] in ['init', 'initialize', 'config', 'configure']):
    print('Running the configuration script.')
    # ASI Data dir
    s = (
        f'What is the aurora data directory? Press enter for the default '
        f'directory at ~/asilib-data folder will be created. '
    )
    ASI_DATA_DIR = input(s)

    s = (
        f'Raise IRBEM import warnings? Default yes: '
    )
    IRBEM_WARNING = input(s)

    # If the user specified the directory, check that the ASI directory already exists
    # and make that directory if it does not.
    if ASI_DATA_DIR != '':
        if not pathlib.Path(ASI_DATA_DIR).exists():
            pathlib.Path(ASI_DATA_DIR).mkdir(parents=True)
            print(f'Made aurora_asi data directory at {pathlib.Path(ASI_DATA_DIR)}.')
        else:
            print(f'aurora_asi data directory at {pathlib.Path(ASI_DATA_DIR)} already exists.')
    else:
        # If the user did not specify the directory, make one at ~/asilib-data
        # and don't save ASI_DATA_DIR. Then configparser in __init__.py will 
        # try to load ASI_DATA_DIR and default to pathlib.Path.home() / 'asilib-data'
        # if it doesn't exist.
        DEFAULT_ASI_DATA_DIR = pathlib.Path.home() / 'asilib-data'
        if not DEFAULT_ASI_DATA_DIR.exists():
            DEFAULT_ASI_DATA_DIR.mkdir()
            print(f'asilib directory at {DEFAULT_ASI_DATA_DIR} created.')
        else:
            print(f'asilib directory at {DEFAULT_ASI_DATA_DIR} already exists.')


    # Check that the IRBEM_WARNING input is correct.
    if ('y' in IRBEM_WARNING.lower()) or ('true' in IRBEM_WARNING.lower()):
        IRBEM_WARNING = True
    elif IRBEM_WARNING == '':
        IRBEM_WARNING = True
    elif ('n' in IRBEM_WARNING.lower()) or ('false' in IRBEM_WARNING.lower()):
        IRBEM_WARNING = False
    else:
        raise ValueError(f'Unknown input to IRBEM_WARNING = {IRBEM_WARNING}. It must be'
                        f' one of the following: [y, n, yes, no, True, False]')


    # Create a configparser object and add the user configuration. 
    config = configparser.ConfigParser()

    if ASI_DATA_DIR != '':
        config['Paths'] = {'ASI_DATA_DIR':ASI_DATA_DIR, 'HERE':here} 
    else:
        config['Paths'] = {'HERE':here}
    config['Warnings'] = {'IRBEM':IRBEM_WARNING}

    with open(here / 'config.ini', 'w') as f:
       config.write(f)

else:
    print(
        'This is a configuration script to set up config.ini file. The config '
        'file contains the aurora data directory, and is in ~/asilib-data by '
        'default. To configure this package, run python3 -m asilib config'
    )
