.. _internals:

Internals for plugins
=====================

Many :ref:`plugin_hooks` are passed objects that provide access to internal Datasette functionality. The interface to these objects should not be considered stable with the exception of methods that are documented here.

.. _internals_request:

Request object
~~~~~~~~~~~~~~

The request object is passed to various plugin hooks. It represents an incoming HTTP request. It has the following properties:

``.scope`` - dictionary
    The ASGI scope that was used to construct this request, described in the `ASGI HTTP connection scope <https://asgi.readthedocs.io/en/latest/specs/www.html#connection-scope>`__ specification.

``.method`` - string
    The HTTP method for this request, usually ``GET`` or ``POST``.

``.url`` - string
    The full URL for this request, e.g. ``https://latest.datasette.io/fixtures``.

``.scheme`` - string
    The request scheme - usually ``https`` or ``http``.

``.headers`` - dictionary (str -> str)
    A dictionary of incoming HTTP request headers.

``.host`` - string
    The host header from the incoming request, e.g. ``latest.datasette.io`` or ``localhost``.

``.path`` - string
    The path of the request, e.g. ``/fixtures``.

``.query_string`` - string
    The querystring component of the request, without the ``?`` - e.g. ``name__contains=sam&age__gt=10``.

``.args`` - RequestParameters
    An object representing the parsed querystring parameters, see below.

The object also has one awaitable method:

``await request.post_vars()`` - dictionary
    Returns a dictionary of form variables that were submitted in the request body via ``POST``.

The RequestParameters class
---------------------------

``request.args`` is a ``RequestParameters`` object - a dictionary-like object which provides access to querystring parameters that may have multiple values.

Consider the querystring ``?foo=1&foo=2&bar=3`` - with two values for ``foo`` and one value for ``bar``.

``request.args[key]`` - string
    Returns the first value for that key, or raises a ``KeyError`` if the key is missing. For the above example ``request.args["foo"]`` would return ``"1"``.

``request.args.get(key)`` - string or None
    Returns the first value for that key, or ``None`` if the key is missing. Pass a second argument to specify a different default, e.g. ``q = request.args.get("q", "")``.

``request.args.getlist(key)`` - list of strings
    Returns the list of strings for that key. ``request.args.getlist("foo")`` would return ``["1", "2"]`` in the above example. ``request.args.getlist("bar")`` would return ``["3"]``. If the key is missing an empty list will be returned.

``request.args.keys()`` - list of strings
    Returns the list of available keys - for the example this would be ``["foo", "bar"]``.

``key in request.args`` - True or False
    You can use ``if key in request.args`` to check if a key is present.

``for key in request.args`` - iterator
    This lets you loop through every available key.

``len(request.args)`` - integer
    Returns the number of keys.

.. _internals_datasette:

Datasette class
~~~~~~~~~~~~~~~

This object is an instance of the ``Datasette`` class, passed to many plugin hooks as an argument called ``datasette``.

.. _datasette_plugin_config:

.plugin_config(plugin_name, database=None, table=None)
------------------------------------------------------

``plugin_name`` - string
    The name of the plugin to look up configuration for. Usually this is something similar to ``datasette-cluster-map``.

``database`` - None or string
    The database the user is interacting with.

``table`` - None or string
    The table the user is interacting with.

This method lets you read plugin configuration values that were set in ``metadata.json``. See :ref:`plugins_plugin_config` for full details of how this method should be used.

.. _datasette_render_template:

.render_template(template, context=None, request=None)
------------------------------------------------------

``template`` - string
    The template file to be rendered, e.g. ``my_plugin.html``. Datasette will search for this file first in the ``--template-dir=`` location, if it was specified - then in the plugin's bundled templates and finally in Datasette's set of default templates.

``context`` - None or a Python dictionary
    The context variables to pass to the template.

``request`` - request object or None
    If you pass a Datasette request object here it will be made available to the template.

Renders a `Jinja template <https://jinja.palletsprojects.com/en/2.11.x/>`__ using Datasette's preconfigured instance of Jinja and returns the resulting string. The template will have access to Datasette's default template functions and any functions that have been made available by other plugins.

await .permission_allowed(actor, action, resource_type=None, resource_identifier=None, default=False)
-----------------------------------------------------------------------------------------------------

``actor`` - dictionary
    The authenticated actor. This is usually ``request.scope.get("actor")``.

``action`` - string
    The name of the action that is being permission checked.

``resource_type`` - string, optional
    The type of resource being checked, e.g. ``"table"``.

``resource_identifier`` - string, optional
    The resource identifier, e.g. the name of the table.

Check if the given actor has permission to perform the given action on the given resource. This uses plugins that implement the :ref:`plugin_permission_allowed` plugin hook to decide if the action is allowed or not.

If none of the plugins express an opinion, the return value will be the ``default`` argument. This is deny, but you can pass ``default=True`` to default allow instead.

.. _datasette_get_database:

.get_database(name)
-------------------

``name`` - string, optional
    The name of the database - optional.

Returns the specified database object. Raises a ``KeyError`` if the database does not exist. Call this method without an argument to return the first connected database.

.. _datasette_add_database:

.add_database(name, db)
-----------------------

``name`` - string
    The unique name to use for this database. Also used in the URL.

``db`` - datasette.database.Database instance
    The database to be attached.

The ``datasette.add_database(name, db)`` method lets you add a new database to the current Datasette instance. This database will then be served at URL path that matches the ``name`` parameter, e.g. ``/mynewdb/``.

The ``db`` parameter should be an instance of the ``datasette.database.Database`` class. For example:

.. code-block:: python

    from datasette.database import Database

    datasette.add_database("my-new-database", Database(
        datasette,
        path="path/to/my-new-database.db",
        is_mutable=True
    ))

This will add a mutable database from the provided file path.

The ``Database()`` constructor takes four arguments: the first is the ``datasette`` instance you are attaching to, the second is a ``path=``, then ``is_mutable`` and ``is_memory`` are both optional arguments.

Use ``is_mutable`` if it is possible that updates will be made to that database - otherwise Datasette will open it in immutable mode and any changes could cause undesired behavior.

Use ``is_memory`` if the connection is to an in-memory SQLite database.

.. _datasette_remove_database:

.remove_database(name)
----------------------

``name`` - string
    The name of the database to be removed.

This removes a database that has been previously added. ``name=`` is the unique name of that database, also used in the URL for it.

.. _datasette_sign:

.sign(value, namespace="default")
---------------------------------

``value`` - any serializable type
    The value to be signed.

``namespace`` - string, optional
    An alternative namespace, see the `itsdangerous salt documentation <https://itsdangerous.palletsprojects.com/en/1.1.x/serializer/#the-salt>`__.

Utility method for signing values, such that you can safely pass data to and from an untrusted environment. This is a wrapper around the `itsdangerous <https://itsdangerous.palletsprojects.com/>`__ library.

This method returns a signed string, which can be decoded and verified using :ref:`datasette_unsign`.

.. _datasette_unsign:

.unsign(value, namespace="default")
-----------------------------------

``signed`` - any serializable type
    The signed string that was created using :ref:`datasette_sign`.

``namespace`` - string, optional
    The alternative namespace, if one was used.

Returns the original, decoded object that was passed to :ref:`datasette_sign`. If the signature is not valid this raises a ``itsdangerous.BadSignature`` exception.

.. _internals_database:

Database class
~~~~~~~~~~~~~~

Instances of the ``Database`` class can be used to execute queries against attached SQLite databases, and to run introspection against their schemas.

.. _database_execute:

await db.execute(sql, ...)
--------------------------

Executes a SQL query against the database and returns the resulting rows (see :ref:`database_results`).

``sql`` - string (required)
    The SQL query to execute. This can include ``?`` or ``:named`` parameters.

``params`` - list or dict
    A list or dictionary of values to use for the parameters. List for ``?``, dictionary for ``:named``.

``truncate`` - boolean
    Should the rows returned by the query be truncated at the maximum page size? Defaults to ``True``, set this to ``False`` to disable truncation.

``custom_time_limit`` - integer ms
    A custom time limit for this query. This can be set to a lower value than the Datasette configured default. If a query takes longer than this it will be terminated early and raise a ``dataette.database.QueryInterrupted`` exception.

``page_size`` - integer
    Set a custom page size for truncation, over-riding the configured Datasette default.

``log_sql_errors`` - boolean
    Should any SQL errors be logged to the console in addition to being raised as an error? Defaults to ``True``.

.. _database_results:

Results
-------

The ``db.execute()`` method returns a single ``Results`` object. This can be used to access the rows returned by the query.

Iterating over a ``Results`` object will yield SQLite `Row objects <https://docs.python.org/3/library/sqlite3.html#row-objects>`__. Each of these can be treated as a tuple or can be accessed using ``row["column"]`` syntax:

.. code-block:: python

    info = []
    results = await db.execute("select name from sqlite_master")
    for row in results:
        info.append(row["name"])

The ``Results`` object also has the following properties and methods:

``.truncated`` - boolean
    Indicates if this query was truncated - if it returned more results than the specified ``page_size``. If this is true then the results object will only provide access to the first ``page_size`` rows in the query result. You can disable truncation by passing ``truncate=False`` to the ``db.query()`` method.

``.columns`` - list of strings
    A list of column names returned by the query.

``.rows`` - list of sqlite3.Row
    This property provides direct access to the list of rows returned by the database. You can access specific rows by index using ``results.rows[0]``.

``.first()`` - row or None
    Returns the first row in the results, or ``None`` if no rows were returned.

``.single_value()``
    Returns the value of the first column of the first row of results - but only if the query returned a single row with a single column. Raises a ``datasette.database.MultipleValues`` exception otherwise.

``.__len__()``
    Calling ``len(results)`` returns the (truncated) number of returned results.

.. _database_execute_fn:

await db.execute_fn(fn)
-----------------------

Executes a given callback function against a read-only database connection running in a thread. The function will be passed a SQLite connection, and the return value from the function will be returned by the ``await``.

Example usage:

.. code-block:: python

    def get_version(conn):
        return conn.execute(
            "select sqlite_version()"
        ).fetchall()[0][0]

    version = await db.execute_fn(get_version)

.. _database_execute_write:

await db.execute_write(sql, params=None, block=False)
-----------------------------------------------------

SQLite only allows one database connection to write at a time. Datasette handles this for you by maintaining a queue of writes to be executed against a given database. Plugins can submit write operations to this queue and they will be executed in the order in which they are received.

This method can be used to queue up a non-SELECT SQL query to be executed against a single write connection to the database.

You can pass additional SQL parameters as a tuple or dictionary.

By default queries are considered to be "fire and forget" - they will be added to the queue and executed in a separate thread while your code can continue to do other things. The method will return a UUID representing the queued task.

If you pass ``block=True`` this behaviour changes: the method will block until the write operation has completed, and the return value will be the return from calling ``conn.execute(...)`` using the underlying ``sqlite3`` Python library.

.. _database_execute_write_fn:

await db.execute_write_fn(fn, block=False)
------------------------------------------

This method works like ``.execute_write()``, but instead of a SQL statement you give it a callable Python function. This function will be queued up and then called when the write connection is available, passing that connection as the argument to the function.

The function can then perform multiple actions, safe in the knowledge that it has exclusive access to the single writable connection as long as it is executing.

For example:

.. code-block:: python

    def my_action(conn):
        conn.execute("delete from some_table")
        conn.execute("delete from other_table")

    await database.execute_write_fn(my_action)

This method is fire-and-forget, queueing your function to be executed and then allowing your code after the call to ``.execute_write_fn()`` to continue running while the underlying thread waits for an opportunity to run your function. A UUID representing the queued task will be returned.

If you pass ``block=True`` your calling code will block until the function has been executed. The return value to the ``await`` will be the return value of your function.

If your function raises an exception and you specified ``block=True``, that exception will be propagated up to the ``await`` line. With ``block=False`` any exceptions will be silently ignored.

Here's an example of ``block=True`` in action:

.. code-block:: python

    def my_action(conn):
        conn.execute("delete from some_table where id > 5")
        return conn.execute("select count(*) from some_table").fetchone()[0]

    try:
        num_rows_left = await database.execute_write_fn(my_action, block=True)
    except Exception as e:
        print("An error occurred:", e)

Database introspection
----------------------

The ``Database`` class also provides properties and methods for introspecting the database.

``db.name`` - string
    The name of the database - usually the filename without the ``.db`` prefix.

``db.size`` - integer
    The size of the database file in bytes. 0 for ``:memory:`` databases.

``db.mtime_ns`` - integer or None
    The last modification time of the database file in nanoseconds since the epoch. ``None`` for ``:memory:`` databases.

``await db.table_exists(table)`` - boolean
    Check if a table called ``table`` exists.

``await db.table_names()`` - list of strings
    List of names of tables in the database.

``await db.view_names()`` - list of strings
    List of names of views in tha database.

``await db.table_columns(table)`` - list of strings
    Names of columns in a specific table.

``await db.primary_keys(table)`` - list of strings
    Names of the columns that are part of the primary key for this table.

``await db.fts_table(table)`` - string or None
    The name of the FTS table associated with this table, if one exists.

``await db.label_column_for_table(table)`` - string or None
    The label column that is associated with this table - either automatically detected or using the ``"label_column"`` key from :ref:`metadata`, see :ref:`label_columns`.

``await db.foreign_keys_for_table(table)`` - list of dictionaries
    Details of columns in this table which are foreign keys to other tables. A list of dictionaries where each dictionary is shaped like this: ``{"column": string, "other_table": string, "other_column": string}``.

``await db.hidden_table_names()`` - list of strings
    List of tables which Datasette "hides" by default - usually these are tables associated with SQLite's full-text search feature, the SpatiaLite extension or tables hidden using the :ref:`metadata_hiding_tables` feature.

``await db.get_table_definition(table)`` - string
    Returns the SQL definition for the table - the ``CREATE TABLE`` statement and any associated ``CREATE INDEX`` statements.

``await db.get_view_definition(view)`` - string
    Returns the SQL definition of the named view.

``await db.get_all_foreign_keys()`` - dictionary
    Dictionary representing both incoming and outgoing foreign keys for this table. It has two keys, ``"incoming"`` and ``"outgoing"``, each of which is a list of dictionaries with keys ``"column"``, ``"other_table"`` and ``"other_column"``. For example:

    .. code-block:: json

        {
            "incoming": [],
            "outgoing": [
                {
                    "other_table": "attraction_characteristic",
                    "column": "characteristic_id",
                    "other_column": "pk",
                },
                {
                    "other_table": "roadside_attractions",
                    "column": "attraction_id",
                    "other_column": "pk",
                }
            ]
        }
