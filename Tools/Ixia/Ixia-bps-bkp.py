# python: rest:export bpt files

import os, sys
libpath = r"/Users/sursubramani/PycharmProjects/cpt-eng-test/BreakingPoint-master/RestApi/Python/RestApi_v2/Modules"
sys.path.insert(0, libpath)
from bps_restpy.bps import BPS

# BPS system information

BPS_SYSTEM = '10.0.1.10'
# BPS_SYSTEM = 'merpil1d.lbj.is.keysight.com'
BPS_USER = 'admin'
BPS_PASSWORD = '!'

# Configurator Bot Configuration

EXPORT_DIRECTORY = os.path.join(os.path.dirname(__file__), 'BPS-BKP')

EXPORT_FILE_PREFIX = 'exported_'

def export_test_bpt_files():
    # Login to BPS box

    pyBps = BPS(BPS_SYSTEM, BPS_USER, BPS_PASSWORD)

    pyBps.login()

    print("just before collecting bpt")

    # Search test name matching the string given

    searchString = ''

    # The limit of rows to return

    limit = '10000'

    # Parameter to sort by: 'lastrunby'

    sort = 'createdBy'

    # The sort order: ascending

    sortorder = 'ascending'

    # Exec 'search' to get the list of BPT files

    bpt_files = pyBps.testmodel.search(searchString, limit, sort, sortorder)

    print(bpt_files)

    try:

        # Export only the BPT files starting with 'REG_'

        for bpt_file in bpt_files:

            if bpt_file['name']:
                name = bpt_file['name']

                attachments = True

                filename = f"{name}.bpt"

                filepath = os.path.join(EXPORT_DIRECTORY, filename)

                runid = bpt_file.get('runid')  # Check if 'runid' is available

                print(f"exporting file {name}.bpt")
                try:
                    pyBps.testmodel.exportModel(name, attachments, filepath, runid)
                except Exception as e:
                    print(e)
                    print(name)

    except Exception as e:

        print(f"An error occurred: {e}")

    # Logout from BPS box

    pyBps.logout()


# Entry point

if __name__ == '__main__':
    export_test_bpt_files()