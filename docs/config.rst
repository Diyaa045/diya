.. _config:

Configuration
=============

Using \-\-config
----------------

Datasette provides a number of configuration options. These can be set using the ``--config name:value`` option to ``datasette serve``.

You can set multiple configuration options at once like this::

    datasette mydatabase.db \
        --config default_page_size:50 \
        --config sql_time_limit_ms:3500 \
        --config max_returned_rows:2000


.. _config_dir:

Configuration directory mode
----------------------------

Normally you configure Datasette using command-line options. For a Datasette instance with custom templates, custom plugins, a static directory and several databases this can get quite verbose::

    $ datasette one.db two.db \
        --metadata.json \
        --template-dir=templates/ \
        --plugins-dir=plugins \
        --static css:css

As an alternative to this, you can run Datasette in *configuration directory* mode. Create a directory with the following structure::

    # In a directory called my-app:
    my-app/one.db
    my-app/two.db
    my-app/metadata.json
    my-app/templates/index.html
    my-app/plugins/my_plugin.py
    my-app/static/my.css

Now start Datasette by providing the path to that directory::

    $ datasette my-app/

Datasette will detect the files in that directory and automatically configure itself using them. It will serve all ``*.db`` files that it finds, will load ``metadata.json`` if it exists, and will load the ``templates``, ``plugins`` and ``static`` folders if they are present.

The files that can be included in this directory are as follows. All are optional.

* ``*.db`` - SQLite database files that will be served by Datasette
* ``metadata.json`` - :ref:`metadata` for those databases - ``metadata.yaml`` or ``metadata.yml`` can be used as well
* ``inspect-data.json`` - the result of running ``datasette inspect`` - any database files listed here will be treated as immutable, so they should not be changed while Datasette is running
* ``config.json`` - settings that would normally be passed using ``--config`` - here they should be stored as a JSON object of key/value pairs
* ``templates/`` - a directory containing :ref:`customization_custom_templates`
* ``plugins/`` - a directory containing plugins, see :ref:`plugins_writing_one_off`
* ``static/`` - a directory containing static files - these will be served from ``/static/filename.txt``, see :ref:`customization_static_files`

Configuration options
---------------------

The followig options can be set using ``--config name:value``, or by storing them in the ``config.json`` file for use with :ref:`config_dir`.

default_page_size
~~~~~~~~~~~~~~~~~

The default number of rows returned by the table page. You can over-ride this on a per-page basis using the ``?_size=80`` querystring parameter, provided you do not specify a value higher than the ``max_returned_rows`` setting. You can set this default using ``--config`` like so::

    datasette mydatabase.db --config default_page_size:50

sql_time_limit_ms
~~~~~~~~~~~~~~~~~

By default, queries have a time limit of one second. If a query takes longer than this to run Datasette will terminate the query and return an error.

If this time limit is too short for you, you can customize it using the ``sql_time_limit_ms`` limit - for example, to increase it to 3.5 seconds::

    datasette mydatabase.db --config sql_time_limit_ms:3500

You can optionally set a lower time limit for an individual query using the ``?_timelimit=100`` querystring argument::

    /my-database/my-table?qSpecies=44&_timelimit=100

This would set the time limit to 100ms for that specific query. This feature is useful if you are working with databases of unknown size and complexity - a query that might make perfect sense for a smaller table could take too long to execute on a table with millions of rows. By setting custom time limits you can execute queries "optimistically" - e.g. give me an exact count of rows matching this query but only if it takes less than 100ms to calculate.

.. _config_max_returned_rows:

max_returned_rows
~~~~~~~~~~~~~~~~~

Datasette returns a maximum of 1,000 rows of data at a time. If you execute a query that returns more than 1,000 rows, Datasette will return the first 1,000 and include a warning that the result set has been truncated. You can use OFFSET/LIMIT or other methods in your SQL to implement pagination if you need to return more than 1,000 rows.

You can increase or decrease this limit like so::

    datasette mydatabase.db --config max_returned_rows:2000

num_sql_threads
~~~~~~~~~~~~~~~

Maximum number of threads in the thread pool Datasette uses to execute SQLite queries. Defaults to 3.

::

    datasette mydatabase.db --config num_sql_threads:10

allow_facet
~~~~~~~~~~~

Allow users to specify columns they would like to facet on using the ``?_facet=COLNAME`` URL parameter to the table view.

This is enabled by default. If disabled, facets will still be displayed if they have been specifically enabled in ``metadata.json`` configuration for the table.

Here's how to disable this feature::

    datasette mydatabase.db --config allow_facet:off

default_facet_size
~~~~~~~~~~~~~~~~~~

The default number of unique rows returned by :ref:`facets` is 30. You can customize it like this::

    datasette mydatabase.db --config default_facet_size:50

facet_time_limit_ms
~~~~~~~~~~~~~~~~~~~

This is the time limit Datasette allows for calculating a facet, which defaults to 200ms::

    datasette mydatabase.db --config facet_time_limit_ms:1000

facet_suggest_time_limit_ms
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When Datasette calculates suggested facets it needs to run a SQL query for every column in your table. The default for this time limit is 50ms to account for the fact that it needs to run once for every column. If the time limit is exceeded the column will not be suggested as a facet.

You can increase this time limit like so::

    datasette mydatabase.db --config facet_suggest_time_limit_ms:500

suggest_facets
~~~~~~~~~~~~~~

Should Datasette calculate suggested facets? On by default, turn this off like so::

    datasette mydatabase.db --config suggest_facets:off

allow_download
~~~~~~~~~~~~~~

Should users be able to download the original SQLite database using a link on the database index page? This is turned on by default - to disable database downloads, use the following::

    datasette mydatabase.db --config allow_download:off

.. _config_default_cache_ttl:

default_cache_ttl
~~~~~~~~~~~~~~~~~

Default HTTP caching max-age header in seconds, used for ``Cache-Control: max-age=X``. Can be over-ridden on a per-request basis using the ``?_ttl=`` querystring parameter. Set this to ``0`` to disable HTTP caching entirely. Defaults to 5 seconds.

::

    datasette mydatabase.db --config default_cache_ttl:60

.. _config_default_cache_ttl_hashed:

default_cache_ttl_hashed
~~~~~~~~~~~~~~~~~~~~~~~~

Default HTTP caching max-age for responses served using using the :ref:`hashed-urls mechanism <config_hash_urls>`. Defaults to 365 days (31536000 seconds).

::

    datasette mydatabase.db --config default_cache_ttl_hashed:10000


cache_size_kb
~~~~~~~~~~~~~

Sets the amount of memory SQLite uses for its `per-connection cache <https://www.sqlite.org/pragma.html#pragma_cache_size>`_, in KB.

::

    datasette mydatabase.db --config cache_size_kb:5000

.. _config_allow_csv_stream:

allow_csv_stream
~~~~~~~~~~~~~~~~

Enables :ref:`the CSV export feature <csv_export>` where an entire table
(potentially hundreds of thousands of rows) can be exported as a single CSV
file. This is turned on by default - you can turn it off like this:

::

    datasette mydatabase.db --config allow_csv_stream:off

.. _config_max_csv_mb:

max_csv_mb
~~~~~~~~~~

The maximum size of CSV that can be exported, in megabytes. Defaults to 100MB.
You can disable the limit entirely by settings this to 0:

::

    datasette mydatabase.db --config max_csv_mb:0

.. _config_truncate_cells_html:

truncate_cells_html
~~~~~~~~~~~~~~~~~~~

In the HTML table view, truncate any strings that are longer than this value.
The full value will still be available in CSV, JSON and on the individual row
HTML page. Set this to 0 to disable truncation.

::

    datasette mydatabase.db --config truncate_cells_html:0


force_https_urls
~~~~~~~~~~~~~~~~

Forces self-referential URLs in the JSON output to always use the ``https://``
protocol. This is useful for cases where the application itself is hosted using
HTTP but is served to the outside world via a proxy that enables HTTPS.

::

    datasette mydatabase.db --config force_https_urls:1

.. _config_hash_urls:

hash_urls
~~~~~~~~~

When enabled, this setting causes Datasette to append a content hash of the
database file to the URL path for every table and query within that database.

When combined with far-future expire headers this ensures that queries can be
cached forever, safe in the knowledge that any modifications to the database
itself will result in new, uncachcacheed URL paths.

::

    datasette mydatabase.db --config hash_urls:1

.. _config_template_debug:

template_debug
~~~~~~~~~~~~~~

This setting enables template context debug mode, which is useful to help understand what variables are available to custom templates when you are writing them.

Enable it like this::

    datasette mydatabase.db --config template_debug:1

Now you can add ``?_context=1`` or ``&_context=1`` to any Datasette page to see the context that was passed to that template.

Some examples:

* https://latest.datasette.io/?_context=1
* https://latest.datasette.io/fixtures?_context=1
* https://latest.datasette.io/fixtures/roadside_attractions?_context=1

.. _config_base_url:

base_url
~~~~~~~~

If you are running Datasette behind a proxy, it may be useful to change the root URL used for the Datasette instance.

For example, if you are sending traffic from ``https://www.example.com/tools/datasette/`` through to a proxied Datasette instance you may wish Datasette to use ``/tools/datasette/`` as its root URL.

You can do that like so::

    datasette mydatabase.db --config base_url:/tools/datasette/

.. _config_secret:

Configuring the secret
----------------------

Datasette uses a secret string to sign secure values such as cookies.

If you do not provide a secret, Datasette will create one when it starts up. This secret will reset every time the Datasette server restarts though, so things like authentication cookies will not stay valid between restarts.

You can pass a secret to Datasette in two ways: with the ``--secret`` command-line option or by setting a ``DATASETTE_SECRET`` environment variable.

::

    $ datasette mydb.db --secret=SECRET_VALUE_HERE

Or::

    $ export DATASETTE_SECRET=SECRET_VALUE_HERE
    $ datasette mydb.db

One way to generate a secure random secret is to use Python like this::

    $ python3 -c 'import secrets; print(secrets.token_hex(32))'
    cdb19e94283a20f9d42cca50c5a4871c0aa07392db308755d60a1a5b9bb0fa52

Plugin authors make use of this signing mechanism in their plugins using :ref:`datasette_sign` and :ref:`datasette_unsign`.
