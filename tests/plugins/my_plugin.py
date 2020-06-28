from datasette import hookimpl
from datasette.facets import Facet
from datasette.utils import path_with_added_args
from datasette.utils.asgi import asgi_send_json, Response
import base64
import pint
import json

ureg = pint.UnitRegistry()


@hookimpl
def prepare_connection(conn, database, datasette):
    def convert_units(amount, from_, to_):
        "select convert_units(100, 'm', 'ft');"
        return (amount * ureg(from_)).to(to_).to_tuple()[0]

    conn.create_function("convert_units", 3, convert_units)

    def prepare_connection_args():
        return 'database={}, datasette.plugin_config("name-of-plugin")={}'.format(
            database, datasette.plugin_config("name-of-plugin")
        )

    conn.create_function("prepare_connection_args", 0, prepare_connection_args)


@hookimpl
def extra_css_urls(template, database, table, datasette):
    return [
        "https://plugin-example.com/{}/extra-css-urls-demo.css".format(
            base64.b64encode(
                json.dumps(
                    {"template": template, "database": database, "table": table,}
                ).encode("utf8")
            ).decode("utf8")
        )
    ]


@hookimpl
def extra_js_urls():
    return [
        {"url": "https://plugin-example.com/jquery.js", "sri": "SRIHASH",},
        "https://plugin-example.com/plugin1.js",
    ]


@hookimpl
def extra_body_script(template, database, table, datasette):
    return "var extra_body_script = {};".format(
        json.dumps(
            {
                "template": template,
                "database": database,
                "table": table,
                "config": datasette.plugin_config(
                    "name-of-plugin", database=database, table=table,
                ),
            }
        )
    )


@hookimpl
def render_cell(value, column, table, database, datasette):
    # Render some debug output in cell with value RENDER_CELL_DEMO
    if value != "RENDER_CELL_DEMO":
        return None
    return json.dumps(
        {
            "column": column,
            "table": table,
            "database": database,
            "config": datasette.plugin_config(
                "name-of-plugin", database=database, table=table,
            ),
        }
    )


@hookimpl
def extra_template_vars(template, database, table, view_name, request, datasette):
    return {
        "extra_template_vars": json.dumps(
            {
                "template": template,
                "scope_path": request.scope["path"] if request else None,
            },
            default=lambda b: b.decode("utf8"),
        )
    }


@hookimpl
def prepare_jinja2_environment(env):
    env.filters["format_numeric"] = lambda s: "{:,.0f}".format(float(s))


@hookimpl
def register_facet_classes():
    return [DummyFacet]


class DummyFacet(Facet):
    type = "dummy"

    async def suggest(self):
        columns = await self.get_columns(self.sql, self.params)
        return (
            [
                {
                    "name": column,
                    "toggle_url": self.ds.absolute_url(
                        self.request,
                        path_with_added_args(self.request, {"_facet_dummy": column}),
                    ),
                    "type": "dummy",
                }
                for column in columns
            ]
            if self.request.args.get("_dummy_facet")
            else []
        )

    async def facet_results(self):
        facet_results = {}
        facets_timed_out = []
        return facet_results, facets_timed_out


@hookimpl
def actor_from_request(datasette, request):
    if request.args.get("_bot"):
        return {"id": "bot"}
    else:
        return None


@hookimpl
def asgi_wrapper():
    def wrap(app):
        async def maybe_set_actor_in_scope(scope, recieve, send):
            if b"_actor_in_scope" in scope["query_string"]:
                scope = dict(scope, actor={"id": "from-scope"})
                print(scope)
            await app(scope, recieve, send)

        return maybe_set_actor_in_scope

    return wrap


@hookimpl
def permission_allowed(actor, action):
    if action == "this_is_allowed":
        return True
    elif action == "this_is_denied":
        return False


@hookimpl
def register_routes():
    async def one(datasette):
        return Response.text(
            (await datasette.get_database().execute("select 1 + 1")).first()[0]
        )

    async def two(request):
        name = request.url_vars["name"]
        greeting = request.args.get("greeting")
        return Response.text("{} {}".format(greeting, name))

    async def three(scope, send):
        await asgi_send_json(
            send, {"hello": "world"}, status=200, headers={"x-three": "1"}
        )

    async def post(request):
        if request.method == "GET":
            return Response.html(request.scope["csrftoken"]())
        else:
            return Response.json(await request.post_vars())

    async def csrftoken_form(request, datasette):
        return Response.html(
            await datasette.render_template("csrftoken_form.html", request=request)
        )

    def not_async():
        return Response.html("This was not async")

    return [
        (r"/one/$", one),
        (r"/two/(?P<name>.*)$", two),
        (r"/three/$", three),
        (r"/post/$", post),
        (r"/csrftoken-form/$", csrftoken_form),
        (r"/not-async/$", not_async),
    ]


@hookimpl
def startup(datasette):
    datasette._startup_hook_fired = True


@hookimpl
def canned_queries(datasette, database, actor):
    return {
        "from_hook": "select 1, '{}' as actor_id".format(
            actor["id"] if actor else "null"
        )
    }


@hookimpl
def register_magic_parameters():
    from uuid import uuid4

    def uuid(key, request):
        if key == "new":
            return str(uuid4())
        else:
            raise KeyError

    def request(key, request):
        if key == "http_version":
            return request.scope["http_version"]
        else:
            raise KeyError

    return [
        ("request", request),
        ("uuid", uuid),
    ]
