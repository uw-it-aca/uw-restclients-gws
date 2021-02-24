# REST client for the UW Groups Web Service

[![Build Status](https://github.com/uw-it-aca/uw-restclients-gws/workflows/tests/badge.svg?branch=master)](https://github.com/uw-it-aca/uw-restclients-gws/actions)
[![Coverage Status](https://coveralls.io/repos/github/uw-it-aca/uw-restclients-gws/badge.svg?branch=master)](https://coveralls.io/github/uw-it-aca/uw-restclients-gws?branch=master)
[![PyPi Version](https://img.shields.io/pypi/v/uw-restclients-gws.svg)](https://pypi.python.org/pypi/uw-restclients-gws)
![Python versions](https://img.shields.io/pypi/pyversions/uw-restclients-gws.svg)

Installation:

    pip install UW-RestClients-GWS

To use this client, you'll need these settings in your application or script:

    # Specifies whether requests should use live or mocked resources,
    # acceptable values are 'Live' or 'Mock' (default)
    RESTCLIENTS_GWS_DAO_CLASS='Live'

    # Paths to UWCA cert and key files
    RESTCLIENTS_GWS_CERT_FILE='/path/to/cert'
    RESTCLIENTS_GWS_KEY_FILE='/path/to/key'

    # Groups Web Service hostname (eval or production)
    RESTCLIENTS_GWS_HOST='https://iam-ws.u.washington.edu'

Optional settings:

    # Customizable parameters for urllib3
    RESTCLIENTS_GWS_TIMEOUT=5
    RESTCLIENTS_GWS_POOL_SIZE=10

See examples for usage.  Pull requests welcome.
