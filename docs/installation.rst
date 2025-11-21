Installation
============

QakeAPI can be installed via pip:

.. code-block:: bash

   pip install qakeapi

Requirements
-----------

QakeAPI requires Python 3.8 or higher and the following dependencies:

* uvicorn>=0.15.0
* pydantic>=2.0.0
* python-multipart>=0.0.5
* aiofiles>=0.8.0

Optional Dependencies
------------------

For authentication and security features:

* python-jose[cryptography]>=3.3.0
* passlib[bcrypt]>=1.7.4
* PyJWT>=2.0.0

Development Installation
----------------------

For development, you can install QakeAPI from source:

.. code-block:: bash

   git clone https://github.com/craxti/qakeapi.git
   cd qakeapi
   pip install -e . 