.. _internals:

Internals for plugins
=====================

Many :ref:`plugin_hooks` are passed objects that provide access to internal Datasette functionality. The interface to these objects should not be considered stable (at least until Datasette 1.0) with the exception of methods that are documented on this page.

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

``conttext`` - None or a Python dictionary
    The context variables to pass to the template.

``request`` - request object or None
    If you pass a Datasette request object here it will be made available to the template.

Renders a `Jinja template <https://jinja.palletsprojects.com/en/2.11.x/>`__ using Datasette's preconfigured instance of Jinja and returns the resulting string. The template will have access to Datasette's default template functions and any functions that have been made available by other plugins.

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

.. _internals_database:

Database class
~~~~~~~~~~~~~~

Instances of the ``Database`` class can be used to execute queries against attached SQLite databases, and to run introspection against their schemas.

SQLite only allows one databasae connection to write at a time. Datasette handles this for you by maintaining a queue of writes to be executed against a given database. Plugins can submit write operations to this queue and they will be executed in the order in which they are received.

.. _database_execute_write:

await db.execute_write(sql, params=None, block=False)
-----------------------------------------------------

This method can be used to queue up a non-SELECT SQL query to be executed against a single write connection to the database.

You can pass additional SQL parametercs as a tuple or list.

By default queries are considered to be "fire and forget" - they will be added to the queue and executed in a separate thread while your code can continue to do other things. The method will return a UUID representing the queued task.

If you pass ``block=True`` this behaviour changes: the method will block until the write operation has completed, and the return value will be the return from calling ``conn.execute(...)`` using the underlying ``sqlite3`` Python library.

.. _database_execute_write:

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
