.. _pages:

=========================
 Pages and API endpoints
=========================

The Datasette web application offers a number of different pages that can be accessed to explore the data in question, each of which is accompanied by an equivalent JSON API.

.. _IndexView:

Top-level index
===============

The root page of any Datasette installation is an index page that lists all of the currently attached databases. Some examples:

* `fivethirtyeight.datasettes.com <https://fivethirtyeight.datasettes.com/>`_
* `global-power-plants.datasettes.com <https://global-power-plants.datasettes.com/>`_
* `register-of-members-interests.datasettes.com <https://register-of-members-interests.datasettes.com/>`_

Add ``/.json`` to the end of the URL for the JSON version of the underlying data:

* `fivethirtyeight.datasettes.com/.json <https://fivethirtyeight.datasettes.com/.json>`_
* `global-power-plants.datasettes.com/.json <https://global-power-plants.datasettes.com/.json>`_
* `register-of-members-interests.datasettes.com/.json <https://register-of-members-interests.datasettes.com/.json>`_

.. _DatabaseView:

Database
========

Each database has a page listing the tables, views and canned queries
available for that database. If the :ref:`config_allow_sql` config option is enabled (it's turned on by default) there will also be an interface for executing arbitrary SQL select queries against the data.

Examples:

* `fivethirtyeight.datasettes.com/fivethirtyeight-ac35616 <https://fivethirtyeight.datasettes.com/fivethirtyeight-ac35616>`_
* `global-power-plants.datasettes.com/global-power-plants-9e55be2 <https://global-power-plants.datasettes.com/global-power-plants-9e55be2>`_

The JSON version of this page provides programmatic access to the underlying data:

* `fivethirtyeight.datasettes.com/fivethirtyeight-ac35616.json <https://fivethirtyeight.datasettes.com/fivethirtyeight-ac35616.json>`_
* `global-power-plants.datasettes.com/global-power-plants-9e55be2.json <https://global-power-plants.datasettes.com/global-power-plants-9e55be2.json>`_

Note that these URLs end in a 7 character hash. This hash is derived from the contents of the database, and ensures that each URL is immutable: the data returned from a URL containing the hash will always be the same, since if the contents of the database file changes by even a single byte a new hash will be generated.

If you access one of these URLs with an incorrect hash (say because a new version of the underlying database has been published) Datasette will 302 redirect you to the correct URL. This happens for all URLs below the database page as well.

Thanks to this hashing scheme, Datasette URLs can all be returned with far-future cache expiry headers. This means browsers will cache the data (including data from the JSON APIs) for a long time, and CDNs such as `Cloudflare <https://www.cloudflare.com/>`_ or `Fastly <https://www.cloudflare.com/>`_ can be used to dramatically improve the performance of a Datasette hosted API.

.. _TableView:

Table
=====

The table page is the heart of Datasette: it allows users to interactively explore the contents of a database table, including sorting, filtering, :ref:`full_text_search` and applying :ref:`facets`.

The HTML interface is worth spending some time exploring. As with other pages, you can return the JSON data by appending ``.json`` to the URL path, before any `?` querystring arguments.

The querystring arguments are described in more detail here: :ref:`table_arguments`

You can also use the table page to interactively construct a SQL query - by applying different filters and a sort order for example - and then click the "View and edit SQL" link to see the SQL query that was used for the page and edit and re-submit it.

Some examples:

* `../items <https://register-of-members-interests.datasettes.com/regmem-d22c12c/items>`_ lists all of the line-items registered by UK MPs as potential conflicts of interest. It demonstrates Datasette's support for :ref:`full_text_search`.
* `../antiquities-act%2Factions_under_antiquities_act <https://fivethirtyeight.datasettes.com/fivethirtyeight-ac35616/antiquities-act%2Factions_under_antiquities_act>`_ is an interface for exploring the "actions under the antiquities act" data table published by FiveThirtyEight.
* `../global-power-plants?country_long=United+Kingdom&fuel1=Gas <https://global-power-plants.datasettes.com/global-power-plants-9e55be2/global-power-plants?country_long=United+Kingdom&fuel1=Gas>`_ is a filtered table page showing every Gas power plant in the United Kingdom. It includes some default facets (configured using `its metadata.json <https://global-power-plants.datasettes.com/-/metadata>`_) and uses the `datasette-cluster-map <https://github.com/simonw/datasette-cluster-map>`_ plugin to show a map of the results.

.. _RowView:

Row
===

Every row in every Datasette table has its own URL. This means individual records can be linked to directly.

Table cells with extremely long text contents are truncated on the table view according to the :ref:`config_truncate_cells_html` setting. If a cell has been truncated the full length version of that cell will be available on the row page.

Rows which are the targets of foreign key references from other tables will show a link to a filtered search for all records that reference that row. Here's an example from the Registers of Members Interests database:

`../people/uk.org.publicwhip%2Fperson%2F10001 <https://register-of-members-interests.datasettes.com/regmem-d22c12c/people/uk.org.publicwhip%2Fperson%2F10001>`_

Note that this URL includes the encoded primary key of the record.

Here's that same page as JSON:

`../people/uk.org.publicwhip%2Fperson%2F10001.json <https://register-of-members-interests.datasettes.com/regmem-d22c12c/people/uk.org.publicwhip%2Fperson%2F10001.json>`_
