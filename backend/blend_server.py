#!/usr/bin/env python
# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""WebApp"""
# pylint: disable=use-dict-literal

import json
import asyncio
import os
import sys
import base64

from timeit import default_timer
from html import escape
from io import StringIO
import typing

import urllib
import urllib.parse
from urllib.parse import urlencode, urlparse, unquote

import warnings
import httpx

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter  # pylint: disable=no-name-in-module

from whitenoise import WhiteNoise
from whitenoise.base import Headers

import flask

from flask import (
    Flask,
    render_template,
    url_for,
    make_response,
    redirect,
    send_from_directory,
)
from flask.wrappers import Response
from flask.json import jsonify

from flask_babel import (
    Babel,
    gettext,
    format_decimal,
)

import blend_core
from blend_core.extended_types import blend_request
from blend_core import (
    logger,
    get_setting,
    settings,
)

from blend_core import infopage
from blend_core import limiter
from blend_core.botdetection import link_token, ProxyFix

from blend_core.data import ENGINE_DESCRIPTIONS
from blend_core.result_types import Answer
from blend_core.settings_defaults import OUTPUT_FORMATS
from blend_core.settings_loader import DEFAULT_SETTINGS_FILE
from blend_core.exceptions import BlendParameterException
from blend_core.sources import (
    DEFAULT_CATEGORY,
    categories,
    engines,
    engine_shortcuts,
)

from blend_core import webutils
from blend_core.webutils import (
    highlight_content,
    get_result_templates,
    get_themes,
    exception_classname_to_text,
    new_hmac,
    is_hmac_of,
    group_engines_in_tab,
)
from blend_core.webadapter import (
    get_blend_query_from_webapp,
    get_selected_categories,
    parse_lang,
)
from blend_core.utils import gen_useragent, dict_subset
from blend_core.version import VERSION_STRING, GIT_URL, GIT_BRANCH
from blend_core.query import RawTextQuery
from blend_core.extensions.oa_doi_rewrite import get_doi_resolver
from blend_core.preferences import (
    Preferences,
    ClientPref,
    ValidationException,
)
import blend_core.answerers
import blend_core.extensions


from blend_core.metrics import get_engines_stats, get_engine_errors, get_reliabilities, histogram, counter, openmetrics
from blend_core.flaskfix import patch_application

from blend_core.locales import (
    LOCALE_BEST_MATCH,
    LOCALE_NAMES,
    RTL_LOCALES,
    localeselector,
    locales_initialize,
    match_locale,
)

# renaming names from blend_core imports ...
from blend_core.autocomplete import search_autocomplete, backends as autocomplete_backends
from blend_core import favicons

from blend_core.valkeydb import initialize as valkey_initialize
from blend_core.blend_locales import blend_locales
import blend_core.pipeline
from blend_core.markanm_features import (
    AI_MODE_CHOICES,
    ENGINE_SCOPE_CHOICES,
    build_ai_answer,
    engine_name_for_scope,
    find_knowledge_card,
    normalize_ai_mode,
    normalize_direct_url,
    normalize_engine_scope,
    selected_category,
)
from blend_core.network import stream as http_stream, set_context_network_name
from blend_core.markanm_engine import markanm_pipeline


logger = logger.getChild('webapp')

warnings.simplefilter("always")

# about static
logger.debug('static directory is %s', settings['ui']['static_path'])

# about templates
logger.debug('templates directory is %s', settings['ui']['templates_path'])
default_theme = settings['ui']['default_theme']
templates_path = settings['ui']['templates_path']
themes = get_themes(templates_path)
result_templates = get_result_templates(templates_path)

STATS_SORT_PARAMETERS = {
    'name': (False, 'name', ''),
    'score': (True, 'score_per_result', 0),
    'result_count': (True, 'result_count', 0),
    'time': (False, 'total', 0),
    'reliability': (False, 'reliability', 100),
}

# Flask app
app = Flask(__name__, static_folder=None, template_folder=templates_path)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.jinja_env.add_extension('jinja2.ext.loopcontrols')  # pylint: disable=no-member
app.jinja_env.filters['group_engines_in_tab'] = group_engines_in_tab  # pylint: disable=no-member
app.secret_key = settings['server']['secret_key']


def get_locale():
    locale = localeselector()
    logger.debug("%s uses locale `%s`", urllib.parse.quote(blend_request.url), locale)
    return locale


babel = Babel(app, locale_selector=get_locale)


def _get_browser_language(req, lang_list):
    client = ClientPref.from_http_request(req)
    locale = match_locale(client.locale_tag, lang_list, fallback='en')
    return locale


def _get_locale_rfc5646(locale):
    """Get locale name for <html lang="...">
    Chrom* browsers don't detect the language when there is a subtag (ie a territory).
    For example "zh-TW" is detected but not "zh-Hant-TW".
    This function returns a locale without the subtag.
    """
    parts = locale.split('-')
    return parts[0].lower() + '-' + parts[-1].upper()


# code-highlighter
@app.template_filter('code_highlighter')
def code_highlighter(codelines, language=None, hl_lines=None, strip_whitespace=True, strip_new_lines=True):
    if not language:
        language = 'text'

    try:
        lexer = get_lexer_by_name(language, stripall=strip_whitespace, stripnl=strip_new_lines)

    except Exception as e:  # pylint: disable=broad-except
        logger.warning("pygments lexer: %s " % e)
        # if lexer is not found, using default one
        lexer = get_lexer_by_name('text', stripall=strip_whitespace, stripnl=strip_new_lines)

    html_code = ''
    tmp_code = ''
    last_line = None
    line_code_start = None

    def offset_hl_lines(hl_lines, start):
        """
        hl_lines in pygments are expected to be relative to the input
        """
        if hl_lines is None:
            return None

        return [line - start + 1 for line in hl_lines]

    # parse lines
    for line, code in codelines:
        if not last_line:
            line_code_start = line

        # new codeblock is detected
        if last_line is not None and last_line + 1 != line:

            # highlight last codepart
            formatter = HtmlFormatter(
                linenos='inline',
                linenostart=line_code_start,
                cssclass="code-highlight",
                hl_lines=offset_hl_lines(hl_lines, line_code_start),
            )
            html_code = html_code + highlight(tmp_code, lexer, formatter)

            # reset conditions for next codepart
            tmp_code = ''
            line_code_start = line

        # add codepart
        tmp_code += code + '\n'

        # update line
        last_line = line

    # highlight last codepart
    formatter = HtmlFormatter(
        linenos='inline',
        linenostart=line_code_start,
        cssclass="code-highlight",
        hl_lines=offset_hl_lines(hl_lines, line_code_start),
    )
    html_code = html_code + highlight(tmp_code, lexer, formatter)

    return html_code


def get_result_template(theme_name: str, template_name: str):
    themed_path = theme_name + '/result_templates/' + template_name
    if themed_path in result_templates:
        return themed_path
    return 'result_templates/' + template_name


_STATIC_FILES: list[str] = []


def custom_url_for(endpoint: str, **values):
    global _STATIC_FILES  # pylint: disable=global-statement
    if not _STATIC_FILES:
        _STATIC_FILES = webutils.get_static_file_list()

    # handled by WhiteNoise
    if endpoint == "static" and values.get("filename"):

        # We need to verify the "filename" argument: in the jinja templates
        # there could be call like:
        #     url_for('static', filename='img/favicon.png')
        # which should map to:
        #     static/themes/<theme_name>/img/favicon.png

        arg_filename = values["filename"]
        if arg_filename not in _STATIC_FILES:
            # try file in the current theme
            theme_name = blend_request.preferences.get_value("theme")
            theme_filename = f"themes/{theme_name}/{arg_filename}"
            if theme_filename in _STATIC_FILES:
                values["filename"] = theme_filename

        app_prefix = url_for("index")
        return f"{app_prefix}static/{values['filename']}"

    if endpoint == "info" and "locale" not in values:

        # We need to verify the "locale" argument: in the jinja templates there
        # could be call like:
        #     url_for('info', pagename='about')
        # which should map to:
        #     info/<locale>/about

        locale = blend_request.preferences.get_value("locale")
        if infopage.INFO_PAGES.get_page(values["pagename"], locale) is None:
            locale = infopage.INFO_PAGES.locale_default
        values["locale"] = locale

    return url_for(endpoint, **values)


def image_proxify(url: str):
    if not url:
        return url

    if url.startswith('//'):
        url = 'https:' + url

    if not blend_request.preferences.get_value('image_proxy'):
        return url

    if url.startswith('data:image/'):
        # 50 is an arbitrary number to get only the beginning of the image.
        partial_base64 = url[len('data:image/') : 50].split(';')
        if (
            len(partial_base64) == 2
            and partial_base64[0] in ['gif', 'png', 'jpeg', 'pjpeg', 'webp', 'tiff', 'bmp']
            and partial_base64[1].startswith('base64,')
        ):
            return url
        return None

    h = new_hmac(settings['server']['secret_key'], url.encode())

    return '{0}?{1}'.format(url_for('image_proxy'), urlencode(dict(url=url.encode(), h=h)))


def get_translations():
    return {
        # when there is autocompletion
        'no_item_found': gettext('No item found'),
        # /preferences: the source of the engine description (wikipedata, wikidata, website)
        'Source': gettext('Source'),
        # infinite scroll
        'error_loading_next_page': gettext('Error loading the next page'),
    }


def get_enabled_categories(category_names: typing.Iterable[str]):
    """The categories in ``category_names```for which there is no active engine
    are filtered out and a reduced list is returned."""

    enabled_engines = [item[0] for item in blend_request.preferences.engines.get_enabled()]
    enabled_categories = set()
    for engine_name in enabled_engines:
        enabled_categories.update(engines[engine_name].categories)
    return [x for x in category_names if x in enabled_categories]


def get_pretty_url(parsed_url: urllib.parse.ParseResult):
    url_formatting_pref = blend_request.preferences.get_value('url_formatting')

    if url_formatting_pref == 'full':
        return [parsed_url.geturl()]

    if url_formatting_pref == 'host':
        return [parsed_url.netloc]

    path = parsed_url.path
    path = path[:-1] if len(path) > 0 and path[-1] == '/' else path
    path = unquote(path.replace("/", " › "))

    # Keep the query argument for URLs like:
    # - 'http://example.org?/foo/bar' --> parsed_url.query is 'foo/bar'
    query_args: list[tuple[str, str]] = list(urllib.parse.parse_qsl(parsed_url.query))
    if not query_args and parsed_url.query:
        path += (" › .." if len(parsed_url.query) > 24 else " › ") + parsed_url.query[-24:]
    return [parsed_url.scheme + "://" + parsed_url.netloc, path]


def get_client_settings():
    req_pref = blend_request.preferences
    return {
        'plugins': req_pref.plugins.get_enabled(),
        'autocomplete': req_pref.get_value('autocomplete'),
        'autocomplete_min': get_setting('search.autocomplete_min'),
        'method': req_pref.get_value('method'),
        'translations': get_translations(),
        'search_on_category_select': req_pref.get_value('search_on_category_select'),
        'hotkeys': req_pref.get_value('hotkeys'),
        'url_formatting': req_pref.get_value('url_formatting'),
        'theme_static_path': custom_url_for('static', filename='themes/simple'),
        'results_on_new_tab': req_pref.get_value('results_on_new_tab'),
        'favicon_resolver': req_pref.get_value('favicon_resolver'),
        'advanced_search': req_pref.get_value('advanced_search'),
        'query_in_title': req_pref.get_value('query_in_title'),
        'safesearch': req_pref.get_value('safesearch'),
        'theme': req_pref.get_value('theme'),
        'doi_resolver': get_doi_resolver(),
    }


def render(template_name: str, **kwargs):
    # values from the preferences
    # pylint: disable=too-many-statements
    client_settings = get_client_settings()
    kwargs['client_settings'] = base64.b64encode(json.dumps(client_settings).encode('utf-8')).decode('utf-8')
    kwargs['preferences'] = blend_request.preferences
    kwargs.update(client_settings)

    # values from the HTTP requests
    kwargs['endpoint'] = 'results' if 'q' in kwargs else blend_request.endpoint
    kwargs['cookies'] = blend_request.cookies
    kwargs['errors'] = blend_request.errors
    kwargs['link_token'] = link_token.get_token()

    kwargs['categories_as_tabs'] = list(settings['categories_as_tabs'].keys())
    kwargs['categories'] = get_enabled_categories(settings['categories_as_tabs'].keys())
    kwargs['DEFAULT_CATEGORY'] = DEFAULT_CATEGORY

    # i18n
    kwargs['blend_locales'] = [l for l in blend_locales if l[0] in settings['search']['languages']]

    locale = blend_request.preferences.get_value('locale')
    kwargs['locale_rfc5646'] = _get_locale_rfc5646(locale)

    if locale in RTL_LOCALES and 'rtl' not in kwargs:
        kwargs['rtl'] = True

    if 'current_language' not in kwargs:
        kwargs['current_language'] = parse_lang(blend_request.preferences, {}, RawTextQuery('', []))

    # values from settings
    kwargs['search_formats'] = [x for x in settings['search']['formats'] if x != 'html']
    kwargs['instance_name'] = get_setting('general.instance_name')
    kwargs['markanm_version'] = VERSION_STRING
    kwargs['markanm_git_url'] = "https://github.com/markanm/markanm"
    kwargs['enable_metrics'] = get_setting('general.enable_metrics')
    kwargs['get_setting'] = get_setting
    kwargs['get_pretty_url'] = get_pretty_url

    # values from settings: donation_url
    donation_url = get_setting('general.donation_url')
    if donation_url is True:
        donation_url = custom_url_for('info', pagename='donate')
    kwargs['donation_url'] = donation_url

    # helpers to create links to other pages
    kwargs['url_for'] = custom_url_for  # override url_for function in templates
    kwargs['image_proxify'] = image_proxify
    kwargs['favicon_url'] = favicons.favicon_url
    kwargs['cache_url'] = settings['ui']['cache_url']
    kwargs['get_result_template'] = get_result_template
    kwargs['opensearch_url'] = (
        url_for('opensearch')
        + '?'
        + urlencode(
            {
                'method': blend_request.preferences.get_value('method'),
                'autocomplete': blend_request.preferences.get_value('autocomplete'),
            }
        )
    )
    kwargs['urlparse'] = urlparse

    start_time = default_timer()
    result = render_template('{}/{}'.format(kwargs['theme'], template_name), **kwargs)
    blend_request.render_time += default_timer() - start_time  # pylint: disable=assigning-non-slot

    return result


@app.before_request
def pre_request():
    blend_request.start_time = default_timer()  # pylint: disable=assigning-non-slot
    blend_request.render_time = 0  # pylint: disable=assigning-non-slot
    blend_request.timings = []  # pylint: disable=assigning-non-slot
    blend_request.errors = []  # pylint: disable=assigning-non-slot

    client_pref = ClientPref.from_http_request(blend_request)
    # pylint: disable=redefined-outer-name
    preferences = Preferences(themes, list(categories.keys()), engines, blend_core.extensions.STORAGE, client_pref)

    user_agent = blend_request.headers.get('User-Agent', '').lower()
    if 'webkit' in user_agent and 'android' in user_agent:
        preferences.key_value_settings['method'].value = 'GET'
    blend_request.preferences = preferences  # pylint: disable=assigning-non-slot

    try:
        preferences.parse_dict(blend_request.cookies)

    except Exception as e:  # pylint: disable=broad-except
        logger.exception(e, exc_info=True)
        blend_request.errors.append(gettext('Invalid settings, please edit your preferences'))

    # merge GET, POST vars
    # HINT request.form is of type werkzeug.datastructures.ImmutableMultiDict
    blend_request.form = dict(blend_request.form.items())  # type: ignore
    for k, v in blend_request.args.items():
        if k not in blend_request.form:
            blend_request.form[k] = v

    if blend_request.form.get('preferences'):
        preferences.parse_encoded_data(blend_request.form['preferences'])
    else:
        try:
            preferences.parse_dict(blend_request.form)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception(e, exc_info=True)
            blend_request.errors.append(gettext('Invalid settings'))

    # language is defined neither in settings nor in preferences
    # use browser headers
    if not preferences.get_value("language"):
        language = _get_browser_language(blend_request, settings['search']['languages'])
        preferences.parse_dict({"language": language})
        logger.debug('set language %s (from browser)', preferences.get_value("language"))

    # UI locale is defined neither in settings nor in preferences
    # use browser headers
    if not preferences.get_value("locale"):
        locale = _get_browser_language(blend_request, LOCALE_NAMES.keys())
        preferences.parse_dict({"locale": locale})
        logger.debug('set locale %s (from browser)', preferences.get_value("locale"))

    # request.user_plugins
    blend_request.user_plugins = []  # pylint: disable=assigning-non-slot
    allowed_plugins = preferences.plugins.get_enabled()
    disabled_plugins = preferences.plugins.get_disabled()
    for plugin in blend_core.extensions.STORAGE:
        if (plugin.id not in disabled_plugins) or plugin.id in allowed_plugins:
            blend_request.user_plugins.append(plugin.id)


@app.after_request
def add_default_headers(response: flask.Response):
    # set default http headers
    for header, value in settings['server']['default_http_headers'].items():
        if header in response.headers:
            continue
        response.headers[header] = value
    return response


@app.after_request
def post_request(response: flask.Response):
    total_time = default_timer() - blend_request.start_time
    timings_all = [
        'total;dur=' + str(round(total_time * 1000, 3)),
        'render;dur=' + str(round(blend_request.render_time * 1000, 3)),
    ]
    if len(blend_request.timings) > 0:
        timings = sorted(blend_request.timings, key=lambda t: t.total)
        timings_total = [
            'total_' + str(i) + '_' + t.engine + ';dur=' + str(round(t.total * 1000, 3)) for i, t in enumerate(timings)
        ]
        timings_load = [
            'load_' + str(i) + '_' + t.engine + ';dur=' + str(round(t.load * 1000, 3))
            for i, t in enumerate(timings)
            if t.load
        ]
        timings_all = timings_all + timings_total + timings_load
    response.headers.add('Server-Timing', ', '.join(timings_all))
    return response


def index_error(output_format: str, error_message: str):
    if output_format == 'json':
        return Response(json.dumps({'error': error_message}), mimetype='application/json')
    if output_format == 'csv':
        response = Response('', mimetype='application/csv')
        cont_disp = 'attachment;Filename=blend_core.csv'
        response.headers.add('Content-Disposition', cont_disp)
        return response

    if output_format == 'rss':
        response_rss = render(
            'opensearch_response_rss.xml',
            results=[],
            q=blend_request.form['q'] if 'q' in blend_request.form else '',
            number_of_results=0,
            error_message=error_message,
        )
        return Response(response_rss, mimetype='text/xml')

    # html
    blend_request.errors.append(gettext('search error'))
    return render(
        # fmt: off
        'index.html',
        selected_categories=get_selected_categories(blend_request.preferences, blend_request.form),
        # fmt: on
    )


@app.route('/', methods=['GET', 'POST'])
def index():
    """Render index page."""

    # redirect to search if there's a query in the request
    if blend_request.form.get('q'):
        query = ('?' + blend_request.query_string.decode()) if blend_request.query_string else ''
        return redirect(url_for('search') + query, 308)

    return render(
        # fmt: off
        'index.html',
        selected_categories=get_selected_categories(blend_request.preferences, blend_request.form),
        current_locale = blend_request.preferences.get_value("locale"),
        ai_mode = "fast",
        ai_mode_choices = AI_MODE_CHOICES,
        engine_scope = "markanm",
        engine_scope_choices = ENGINE_SCOPE_CHOICES,
        # fmt: on
    )


@app.route('/healthz', methods=['GET'])
def health():
    return Response('OK', mimetype='text/plain')


@app.route('/client<token>.css', methods=['GET', 'POST'])
def client_token(token=None):
    link_token.ping(blend_request, token)
    return Response('', mimetype='text/css', headers={"Cache-Control": "no-store, max-age=0"})


@app.route('/rss.xsl', methods=['GET', 'POST'])
def rss_xsl():
    return render_template(
        f"{blend_request.preferences.get_value('theme')}/rss.xsl",
        url_for=custom_url_for,
    )


@app.route('/search', methods=['GET', 'POST'])
def blend_search():
    """Search query in q and return results.

    Supported outputs: html, json, csv, rss.
    """
    # pylint: disable=too-many-locals, too-many-return-statements, too-many-branches
    # pylint: disable=too-many-statements

    # output_format
    search_form = dict(blend_request.form.items())
    ai_mode = normalize_ai_mode(search_form.get('ai_mode'))
    engine_scope = normalize_engine_scope(search_form.get('engine_scope'))
    selected_ui_category = selected_category(search_form)
    ai_mode_label = dict(AI_MODE_CHOICES).get(ai_mode, ai_mode)

    output_format = search_form.get('format', 'html')
    if output_format not in OUTPUT_FORMATS:
        output_format = 'html'

    if output_format not in settings['search']['formats']:
        flask.abort(403)

    # check if there is query (not None and not an empty string)
    if not search_form.get('q'):
        if output_format == 'html':
            return render(
                # fmt: off
                'index.html',
                selected_categories=get_selected_categories(blend_request.preferences, blend_request.form),
                ai_mode = ai_mode,
                ai_mode_choices = AI_MODE_CHOICES,
                engine_scope = engine_scope,
                engine_scope_choices = ENGINE_SCOPE_CHOICES,
                # fmt: on
            )
        return index_error(output_format, 'No query'), 400

    direct_url = normalize_direct_url(search_form['q'])
    if direct_url and ai_mode != 'ask':
        return redirect(direct_url, code=302)

    single_engine = engine_name_for_scope(engine_scope, selected_ui_category)
    if engine_scope != 'markanm' and single_engine:
        search_form['engines'] = single_engine

    # search
    blend_query = None
    raw_text_query = None
    result_pool = None
    try:
        blend_query, raw_text_query, _, _, selected_locale = get_blend_query_from_webapp(
            blend_request.preferences, search_form
        )
        search_obj = blend_core.pipeline.SearchWithPlugins(blend_query, blend_request, blend_request.user_plugins)
        result_pool = search_obj.blend_search()

    except BlendParameterException as e:
        logger.exception('search error: BlendParameterException')
        return index_error(output_format, e.message), 400
    except Exception as e:  # pylint: disable=broad-except
        logger.exception(e, exc_info=True)
        return index_error(output_format, gettext('search error')), 500

    # 1. check if the result is a redirect for an external bang
    if result_pool.redirect_url:
        return redirect(result_pool.redirect_url)

    # 2. add Server-Timing header for measuring performance characteristics of
    # web applications
    blend_request.timings = result_pool.get_timings()  # pylint: disable=assigning-non-slot

    # 3. formats without a template

    if output_format == 'json':

        response = webutils.get_json_response(blend_query, result_pool)
        return Response(response, mimetype='application/json')

    if output_format == 'csv':

        csv = webutils.CSVWriter(StringIO())
        webutils.write_csv_response(csv, result_pool)
        csv.stream.seek(0)

        response = Response(csv.stream.read(), mimetype='application/csv')
        cont_disp = 'attachment;Filename=blend_-_{0}.csv'.format(blend_query.query)
        response.headers.add('Content-Disposition', cont_disp)
        return response

    # 4. formats rendered by a template / RSS & HTML

    current_template = None
    previous_result = None

    results = result_pool.get_ordered_results()

    try:
        raw = []
        for r in results:
            if hasattr(r, '__dict__'):
                raw.append(r.__dict__)
            else:
                raw.append(r)
        loop = asyncio.new_event_loop()
        markanm_data = loop.run_until_complete(
            markanm_pipeline.search(
                query=blend_query.query,
                raw_results=raw,
                enable_ai=ai_mode in {'fast', 'deep', 'ask'},
                enable_enrich=ai_mode == 'deep'
            )
        )
        loop.close()
        flask.g.markanm_ai_summary = markanm_data.get("ai_summary", "")
        flask.g.markanm_search_time = markanm_data.get("time_ms", 0)
    except Exception:
        flask.g.markanm_ai_summary = ""
        flask.g.markanm_search_time = 0

    if blend_query.redirect_to_first_result and results:
        return redirect(results[0]['url'], 302)

    for result in results:
        if output_format == 'html':
            if 'content' in result and result['content']:
                result['content'] = highlight_content(escape(result['content'][:1024]), blend_query.query)
            if 'title' in result and result['title']:
                result['title'] = highlight_content(escape(result['title'] or ''), blend_query.query)

        # set result['open_group'] = True when the template changes from the previous result
        # set result['close_group'] = True when the template changes on the next result
        if current_template != result.template:
            result.open_group = True
            if previous_result:
                previous_result.close_group = True  # pylint: disable=unsupported-assignment-operation
        current_template = result.template
        previous_result = result

    if previous_result:
        previous_result.close_group = True

    # 4.a RSS

    if output_format == 'rss':
        response_rss = render(
            'opensearch_response_rss.xml',
            results=results,
            q=blend_request.form['q'],
            number_of_results=result_pool.number_of_results,
        )
        return Response(response_rss, mimetype='text/xml')

    # 4.b HTML

    # suggestions: use RawTextQuery to get the suggestion URLs with the same bang
    suggestion_urls = list(
        map(
            lambda suggestion: {'url': raw_text_query.changeQuery(suggestion).getFullQuery(), 'title': suggestion},
            result_pool.suggestions,
        )
    )

    correction_urls = list(
        map(
            lambda correction: {'url': raw_text_query.changeQuery(correction).getFullQuery(), 'title': correction},
            result_pool.corrections,
        )
    )

    # engine_timings: get engine response times sorted from slowest to fastest
    engine_timings = sorted(result_pool.get_timings(), reverse=True, key=lambda e: e.total)
    max_response_time = engine_timings[0].total if engine_timings else None
    engine_timings_pairs = [(timing.engine, timing.total) for timing in engine_timings]
    knowledge_card = find_knowledge_card(blend_query.query)
    custom_ai_answer = build_ai_answer(blend_query.query, knowledge_card, ai_mode)
    if custom_ai_answer:
        flask.g.markanm_ai_summary = custom_ai_answer

    # blend_query.lang contains the user choice (all, auto, en, ...)
    # when the user choice is "auto", search.blend_query.lang contains the detected language
    # otherwise it is equals to blend_query.lang
    return render(
        # fmt: off
        'results.html',
        results = results,
        q=search_form['q'],
        selected_categories = blend_query.categories,
        pageno = blend_query.pageno,
        time_range = blend_query.time_range or '',
        number_of_results = format_decimal(result_pool.number_of_results),
        suggestions = suggestion_urls,
        answers = result_pool.answers,
        corrections = correction_urls,
        infoboxes = result_pool.infoboxes,
        engine_data = result_pool.engine_data,
        paging = result_pool.paging,
        unresponsive_engines = webutils.get_translated_errors(
            result_pool.unresponsive_engines
        ),
        current_locale = blend_request.preferences.get_value("locale"),
        current_language = selected_locale,
        search_language = match_locale(
            search_obj.blend_query.lang,
            settings['search']['languages'],
            fallback=blend_request.preferences.get_value("language")
        ),
        timeout_limit = search_form.get('timeout_limit', None),
        timings = engine_timings_pairs,
        max_response_time = max_response_time,
        ai_mode = ai_mode,
        ai_mode_label = ai_mode_label,
        ai_mode_choices = AI_MODE_CHOICES,
        engine_scope = engine_scope,
        engine_scope_choices = ENGINE_SCOPE_CHOICES,
        knowledge_card = knowledge_card,
        # fmt: on
    )


@app.route('/about', methods=['GET'])
def about():
    """Redirect to about page"""
    # custom_url_for is going to add the locale
    return redirect(custom_url_for('info', pagename='about'))


@app.route('/info/<locale>/<pagename>', methods=['GET'])
def info(pagename, locale):
    """Render page of online user documentation"""
    page = infopage.INFO_PAGES.get_page(pagename, locale)
    if page is None:
        flask.abort(404)

    user_locale = blend_request.preferences.get_value('locale')
    return render(
        'info.html',
        all_pages=infopage.INFO_PAGES.iter_pages(user_locale, fallback_to_default=True),
        active_page=page,
        active_pagename=pagename,
    )


@app.route('/autocompleter', methods=['GET', 'POST'])
def autocompleter():
    """Return autocompleter results"""

    # run autocompleter
    results = []

    # set blocked engines
    disabled_engines = blend_request.preferences.engines.get_disabled()

    # parse query
    raw_text_query = RawTextQuery(blend_request.form.get('q', ''), disabled_engines)
    sug_prefix = raw_text_query.getQuery()

    for obj in blend_core.answerers.STORAGE.ask(sug_prefix):
        if isinstance(obj, Answer):
            results.append(obj.answer)

    # normal autocompletion results only appear if no inner results returned
    # and there is a query part
    if len(raw_text_query.autocomplete_list) == 0 and len(sug_prefix) > 0:

        # get Markanm's locale and autocomplete backend from cookie
        sxng_locale = blend_request.preferences.get_value('language')
        backend_name = blend_request.preferences.get_value('autocomplete')

        for result in search_autocomplete(backend_name, sug_prefix, sxng_locale):
            # attention: this loop will change raw_text_query object and this is
            # the reason why the sug_prefix was stored before (see above)
            if result != sug_prefix:
                results.append(raw_text_query.changeQuery(result).getFullQuery())

    if len(raw_text_query.autocomplete_list) > 0:
        for autocomplete_text in raw_text_query.autocomplete_list:
            results.append(raw_text_query.get_autocomplete_full_query(autocomplete_text))

    if blend_request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # the suggestion request comes from the blend search form
        suggestions = json.dumps(results)
        mimetype = 'application/json'
    else:
        # the suggestion request comes from browser's URL bar
        suggestions = json.dumps([sug_prefix, results])
        mimetype = 'application/x-suggestions+json'

    suggestions = escape(suggestions, False)
    return Response(suggestions, mimetype=mimetype)


@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    """Render preferences page && save user preferences"""

    # pylint: disable=too-many-locals, too-many-return-statements, too-many-branches
    # pylint: disable=too-many-statements

    # save preferences using the link the /preferences?preferences=...
    if blend_request.args.get('preferences') or blend_request.form.get('preferences'):
        # if preferences_preview_only is 'true', the prefs from the 'preferences' query are
        # shown in the settings page, but they're not applied unless the user presses 'save'
        if blend_request.args.get('preferences_preview_only') != 'true':
            resp = make_response(redirect(url_for('index', _external=True)))
            return blend_request.preferences.save(resp)

    # save preferences
    if blend_request.method == 'POST':
        resp = make_response(redirect(url_for('index', _external=True)))
        try:
            blend_request.preferences.parse_form(blend_request.form)
        except ValidationException:
            blend_request.errors.append(gettext('Invalid settings, please edit your preferences'))
            return resp
        return blend_request.preferences.save(resp)

    # render preferences
    image_proxy = blend_request.preferences.get_value('image_proxy')  # pylint: disable=redefined-outer-name
    disabled_engines = blend_request.preferences.engines.get_disabled()
    allowed_plugins = blend_request.preferences.plugins.get_enabled()

    # stats for preferences page
    filtered_engines = dict(filter(lambda kv: blend_request.preferences.validate_token(kv[1]), engines.items()))

    engines_by_category = {}

    for c in categories:  # pylint: disable=consider-using-dict-items
        engines_by_category[c] = [e for e in categories[c] if e.name in filtered_engines]
        # sort the engines alphabetically since the order in blend_config.yml is meaningless.
        list.sort(engines_by_category[c], key=lambda e: e.name)

    # get first element [0], the engine time,
    # and then the second element [1] : the time (the first one is the label)
    stats = {}  # pylint: disable=redefined-outer-name
    max_rate95 = 0
    for _, e in filtered_engines.items():
        h = histogram('engine', e.name, 'time', 'total')
        median = round(h.percentage(50), 1) if h.count > 0 else None
        rate80 = round(h.percentage(80), 1) if h.count > 0 else None
        rate95 = round(h.percentage(95), 1) if h.count > 0 else None

        max_rate95 = max(max_rate95, rate95 or 0)

        result_count_sum = histogram('engine', e.name, 'result', 'count').sum
        successful_count = counter('engine', e.name, 'search', 'count', 'successful')
        result_count = int(result_count_sum / float(successful_count)) if successful_count else 0

        stats[e.name] = {
            'time': median,
            'rate80': rate80,
            'rate95': rate95,
            'warn_timeout': e.timeout > settings['outgoing']['request_timeout'],
            'supports_selected_language': e.traits.is_locale_supported(
                str(blend_request.preferences.get_value('language') or 'all')
            ),
            'result_count': result_count,
        }
    # end of stats

    # reliabilities
    reliabilities = {}
    engine_errors = get_engine_errors(filtered_engines)
    for _, e in filtered_engines.items():
        errors = engine_errors.get(e.name) or []
        if counter('engine', e.name, 'search', 'count', 'sent') == 0:
            # no request
            reliability = None
        else:
            # pylint: disable=consider-using-generator
            reliability = 100 - sum([error['percentage'] for error in errors if not error.get('secondary')])

        reliabilities[e.name] = {
            'reliability': reliability,
            'errors': [],
        }
        reliabilities_errors = []
        for error in errors:
            error_user_text = None
            if error.get('secondary') or 'exception_classname' not in error:
                continue
            error_user_text = exception_classname_to_text.get(error.get('exception_classname'))
            if not error:
                error_user_text = exception_classname_to_text[None]
            if error_user_text not in reliabilities_errors:
                reliabilities_errors.append(error_user_text)
        reliabilities[e.name]['errors'] = reliabilities_errors

    # supports
    supports = {}
    for _, e in filtered_engines.items():
        supports_selected_language = e.traits.is_locale_supported(
            str(blend_request.preferences.get_value('language') or 'all')
        )
        safesearch = e.safesearch
        time_range_support = e.time_range_support
        supports[e.name] = {
            'supports_selected_language': supports_selected_language,
            'safesearch': safesearch,
            'time_range_support': time_range_support,
        }

    return render(
        # fmt: off
        'preferences.html',
        preferences = True,
        selected_categories = get_selected_categories(blend_request.preferences, blend_request.form),
        locales = LOCALE_NAMES,
        current_locale = blend_request.preferences.get_value("locale"),
        image_proxy = image_proxy,
        engines_by_category = engines_by_category,
        stats = stats,
        max_rate95 = max_rate95,
        reliabilities = reliabilities,
        supports = supports,
        answer_storage = blend_core.answerers.STORAGE.info,
        disabled_engines = disabled_engines,
        autocomplete_backends = autocomplete_backends,
        favicon_resolver_names = favicons.proxy.CFG.resolver_map.keys(),
        shortcuts = {y: x for x, y in engine_shortcuts.items()},
        themes = themes,
        plugins_storage = blend_core.extensions.STORAGE.info,
        current_doi_resolver = get_doi_resolver(),
        allowed_plugins = allowed_plugins,
        preferences_url_params = blend_request.preferences.get_as_url_params(),
        locked_preferences = get_setting("preferences.lock", []),
        doi_resolvers = get_setting("doi_resolvers", {}),
        # fmt: on
    )


app.add_url_rule('/favicon_proxy', methods=['GET'], endpoint="favicon_proxy", view_func=favicons.favicon_proxy)


@app.route('/image_proxy', methods=['GET'])
def image_proxy():
    # pylint: disable=too-many-return-statements, too-many-branches

    url = blend_request.args.get('url')
    if not url:
        return '', 400

    if not is_hmac_of(settings['server']['secret_key'], url.encode(), blend_request.args.get('h', '')):
        return '', 400

    maximum_size = 5 * 1024 * 1024
    forward_resp = False
    resp = None
    try:
        request_headers = {
            'User-Agent': gen_useragent(),
            'Accept': 'image/webp,*/*',
            'Sec-GPC': '1',
            'DNT': '1',
        }
        set_context_network_name('image_proxy')
        resp, stream = http_stream(method='GET', url=url, headers=request_headers, allow_redirects=True)
        content_length = resp.headers.get('Content-Length')
        if content_length and content_length.isdigit() and int(content_length) > maximum_size:
            return 'Max size', 400

        if resp.status_code != 200:
            logger.debug('image-proxy: wrong response code: %i', resp.status_code)
            if resp.status_code >= 400:
                return '', resp.status_code
            return '', 400

        if not resp.headers.get('Content-Type', '').startswith('image/') and not resp.headers.get(
            'Content-Type', ''
        ).startswith('binary/octet-stream'):
            logger.debug('image-proxy: wrong content-type: %s', resp.headers.get('Content-Type', ''))
            return '', 400

        forward_resp = True
    except httpx.HTTPError:
        logger.exception('HTTP error')
        return '', 400
    finally:
        if resp and not forward_resp:
            # the code is about to return an HTTP 400 error to the browser
            # we make sure to close the response between markanm and the HTTP server
            try:
                resp.close()
            except httpx.HTTPError:
                logger.exception('HTTP error on closing')

    def close_stream():
        nonlocal resp, stream
        try:
            if resp:
                resp.close()
            del resp
            del stream
        except httpx.HTTPError as e:
            logger.debug('Exception while closing response', e)

    try:
        headers = dict_subset(resp.headers, {'Content-Type', 'Content-Encoding', 'Content-Length', 'Length'})
        response = Response(stream, mimetype=resp.headers['Content-Type'], headers=headers, direct_passthrough=True)
        response.call_on_close(close_stream)
        return response
    except httpx.HTTPError:
        close_stream()
        return '', 400


@app.route('/engine_descriptions.json', methods=['GET'])
def engine_descriptions():
    sxng_ui_lang_tag = get_locale().replace("_", "-")
    sxng_ui_lang_tag = LOCALE_BEST_MATCH.get(sxng_ui_lang_tag, sxng_ui_lang_tag)

    result = ENGINE_DESCRIPTIONS['en'].copy()
    if sxng_ui_lang_tag != 'en':
        for engine, description in ENGINE_DESCRIPTIONS.get(sxng_ui_lang_tag, {}).items():
            result[engine] = description
    for engine, description in result.items():
        if len(description) == 2 and description[1] == 'ref':
            ref_engine, ref_lang = description[0].split(':')
            description = ENGINE_DESCRIPTIONS[ref_lang][ref_engine]
        if isinstance(description, str):
            description = [description, 'wikipedia']
        result[engine] = description

    # overwrite by about:description (from settings)
    for engine_name, engine_mod in engines.items():
        descr = getattr(engine_mod, 'about', {}).get('description', None)
        if descr is not None:
            result[engine_name] = [descr, "Markanm config"]

    return jsonify(result)


@app.route('/stats', methods=['GET'])
def stats():
    """Render engine statistics page."""
    sort_order = blend_request.args.get('sort', default='name', type=str)
    selected_engine_name = blend_request.args.get('engine', default=None, type=str)

    filtered_engines = dict(filter(lambda kv: blend_request.preferences.validate_token(kv[1]), engines.items()))
    if selected_engine_name:
        if selected_engine_name not in filtered_engines:
            selected_engine_name = None
        else:
            filtered_engines = [selected_engine_name]

    engine_stats = get_engines_stats(filtered_engines)
    engine_reliabilities = get_reliabilities(filtered_engines)

    if sort_order not in STATS_SORT_PARAMETERS:
        sort_order = 'name'

    reverse, key_name, default_value = STATS_SORT_PARAMETERS[sort_order]

    def get_key(engine_stat):
        reliability = engine_reliabilities.get(engine_stat['name'], {}).get('reliability', 0)
        reliability_order = 0 if reliability else 1
        if key_name == 'reliability':
            key = reliability
            reliability_order = 0
        else:
            key = engine_stat.get(key_name) or default_value
            if reverse:
                reliability_order = 1 - reliability_order
        return (reliability_order, key, engine_stat['name'])

    technical_report = []
    for error in engine_reliabilities.get(selected_engine_name, {}).get('errors', []):
        technical_report.append(
            f"\
            Error: {error['exception_classname'] or error['log_message']} \
            Parameters: {error['log_parameters']} \
            File name: {error['filename'] }:{ error['line_no'] } \
            Error Function: {error['function']} \
            Code: {error['code']} \
            ".replace(
                ' ' * 12, ''
            ).strip()
        )
    technical_report = ' '.join(technical_report)

    engine_stats['time'] = sorted(engine_stats['time'], reverse=reverse, key=get_key)
    return render(
        # fmt: off
        'stats.html',
        sort_order = sort_order,
        engine_stats = engine_stats,
        engine_reliabilities = engine_reliabilities,
        selected_engine_name = selected_engine_name,
        technical_report = technical_report,
        # fmt: on
    )


@app.route('/stats/errors', methods=['GET'])
def stats_errors():
    filtered_engines = dict(filter(lambda kv: blend_request.preferences.validate_token(kv[1]), engines.items()))
    result = get_engine_errors(filtered_engines)
    return jsonify(result)


@app.route('/metrics')
def stats_open_metrics():
    password = settings['general'].get("open_metrics")

    if not (settings['general'].get("enable_metrics") and password):
        return Response('open metrics is disabled', status=404, mimetype='text/plain')

    if not blend_request.authorization or blend_request.authorization.password != password:
        return Response('access forbidden', status=401, mimetype='text/plain')

    filtered_engines = dict(filter(lambda kv: blend_request.preferences.validate_token(kv[1]), engines.items()))

    engine_stats = get_engines_stats(filtered_engines)
    engine_reliabilities = get_reliabilities(filtered_engines)
    metrics_text = openmetrics(engine_stats, engine_reliabilities)

    return Response(metrics_text, mimetype='text/plain')


@app.route('/robots.txt', methods=['GET'])
def robots():
    return Response(
        """User-agent: *
Allow: /info/en/about
Disallow: /stats
Disallow: /image_proxy
Disallow: /preferences
Disallow: /*?*q=*
""",
        mimetype='text/plain',
    )


@app.route('/opensearch.xml', methods=['GET'])
def opensearch():
    method = blend_request.preferences.get_value('method')
    autocomplete = blend_request.preferences.get_value('autocomplete')

    # chrome/chromium only supports HTTP GET....
    if blend_request.headers.get('User-Agent', '').lower().find('webkit') >= 0:
        method = 'GET'

    if method not in ('POST', 'GET'):
        method = 'POST'

    ret = render('opensearch.xml', opensearch_method=method, autocomplete=autocomplete)
    resp = Response(response=ret, status=200, mimetype="application/opensearchdescription+xml")
    return resp


@app.route('/manifest.json', methods=['GET'])
def manifest():
    theme = blend_request.preferences.get_value('simple_style')
    if theme not in ("light", "dark", "black"):
        theme = "light"

    theme_color = get_setting(f'brand.pwa_colors.theme_color_{theme}')
    background_color = get_setting(f'brand.pwa_colors.background_color_{theme}')
    ret = render('manifest.json', theme_color=theme_color, background_color=background_color)
    resp = Response(response=ret, status=200, mimetype="application/json")
    return resp


@app.route('/logo/<resolution>')
def manifest_logo(resolution=0):
    theme = blend_request.preferences.get_value("theme")
    return send_from_directory(
        os.path.join(app.root_path, settings['ui']['static_path'], 'themes', theme, 'img', 'logos'),  # type: ignore
        resolution,
        mimetype='image/vnd.microsoft.icon',
    )


@app.route('/favicon.ico')
def favicon():
    theme = blend_request.preferences.get_value("theme")
    return send_from_directory(
        os.path.join(app.root_path, settings['ui']['static_path'], 'themes', theme, 'img'),  # type: ignore
        'favicon.png',
        mimetype='image/vnd.microsoft.icon',
    )


@app.route('/clear_cookies')
def clear_cookies():
    resp = make_response(redirect(url_for('index', _external=True)))
    for cookie_name in blend_request.cookies:
        resp.delete_cookie(cookie_name)
    return resp


@app.route('/config')
def config():
    """Return configuration in JSON format."""
    _engines = []
    for name, engine in engines.items():
        if not blend_request.preferences.validate_token(engine):
            continue

        _languages = engine.traits.languages.keys()
        _engines.append(
            {
                'name': name,
                'categories': engine.categories,
                'shortcut': engine.shortcut,
                'enabled': not engine.disabled,
                'paging': engine.paging,
                'language_support': engine.language_support,
                'languages': list(_languages),
                'regions': list(engine.traits.regions.keys()),
                'safesearch': engine.safesearch,
                'time_range_support': engine.time_range_support,
                'timeout': engine.timeout,
            }
        )

    _plugins = []
    for _ in blend_core.extensions.STORAGE:
        _plugins.append({'name': _.id, 'enabled': _.active})

    _limiter_cfg = limiter.get_cfg()

    return jsonify(
        {
            'categories': list(categories.keys()),
            'engines': _engines,
            'plugins': _plugins,
            'instance_name': settings['general']['instance_name'],
            'locales': LOCALE_NAMES,
            'default_locale': settings['ui']['default_locale'],
            'autocomplete': settings['search']['autocomplete'],
            'safe_search': settings['search']['safe_search'],
            'default_theme': settings['ui']['default_theme'],
            'version': VERSION_STRING,
            'brand': {
                'PRIVACYPOLICY_URL': get_setting('general.privacypolicy_url'),
                'CONTACT_URL': get_setting('general.contact_url'),
                'GIT_URL': GIT_URL,
                'GIT_BRANCH': GIT_BRANCH,
                'DOCS_URL': get_setting('brand.docs_url'),
            },
            'limiter': {
                'enabled': limiter.is_installed(),
                'botdetection.ip_limit.link_token': _limiter_cfg.get('botdetection.ip_limit.link_token'),
                'botdetection.ip_lists.pass_markanm_org': _limiter_cfg.get('botdetection.ip_lists.pass_markanm_org'),
            },
            'doi_resolvers': list(settings['doi_resolvers'].keys()),
            'default_doi_resolver': settings['default_doi_resolver'],
            'public_instance': settings['server']['public_instance'],
        }
    )


@app.errorhandler(404)
def page_not_found(_e):
    return render('404.html'), 404


def run():
    """Runs the application on a local development server.

    This run method is only called when Markanm is started via ``__main__``::

        python -m blend_core.webapp

    Do not use :ref:`run() <flask.Flask.run>` in a production setting.  It is
    not intended to meet security and performance requirements for a production
    server.

    It is not recommended to use this function for development with automatic
    reloading as this is badly supported.  Instead you should be using the flask
    command line script’s run support::

        flask --app blend_core.webapp run --debug --reload --host 127.0.0.1 --port 8888

    .. _Flask.run: https://flask.palletsprojects.com/en/stable/api/#flask.Flask.run
    """

    host: str = get_setting("server.bind_address")  # type: ignore
    port: int = get_setting("server.port")  # type: ignore

    if blend_core.blend_debug:
        logger.debug("run local development server (DEBUG) on %s:%s", host, port)
        app.run(
            debug=True,
            port=port,
            host=host,
            threaded=True,
            extra_files=[DEFAULT_SETTINGS_FILE],
        )
    else:
        logger.debug("run local development server on %s:%s", host, port)
        app.run(port=port, host=host, threaded=True)


def init():

    if blend_core.blend_debug or app.debug:
        app.debug = True
        blend_core.blend_debug = True

    # check secret_key in production

    if not app.debug and get_setting("server.secret_key") == 'ultrasecretkey':
        logger.error("server.secret_key is not changed. Please use something else instead of ultrasecretkey.")
        sys.exit(1)

    locales_initialize()
    valkey_initialize()
    blend_core.extensions.initialize(app)

    metrics: bool = get_setting("general.enable_metrics")  # type: ignore
    embedded_backend = os.environ.get("BLEND_EMBEDDED_BACKEND", "").lower() in ("1", "true")
    blend_core.pipeline.initialize(check_network=not embedded_backend, enable_metrics=metrics)

    limiter.initialize(app, settings)
    favicons.init()


def static_headers(headers: Headers, _path: str, _url: str) -> None:
    headers['Cache-Control'] = 'public, max-age=30, stale-while-revalidate=60'

    for header, value in settings['server']['default_http_headers'].items():
        # cast value to string, as WhiteNoise requires header values to be strings
        headers[header] = str(value)


app.wsgi_app = ProxyFix(app.wsgi_app)
app.wsgi_app = WhiteNoise(
    app.wsgi_app,
    root=settings['ui']['static_path'],
    prefix="static",
    max_age=None,
    allow_all_origins=False,
    add_headers_function=static_headers,
)

patch_application(app)

# remove when we drop support for uwsgi
application = app

init()

if __name__ == "__main__":
    run()
