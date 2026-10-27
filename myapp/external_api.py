"""Third-party external API integration: PyPI Developer Documentation & Library API.

Provides real-time official documentation links, package summaries, and release
versions for software packages relevant to Python and Django developer error codes.

Guaranteed safeguards:
- 3.0 second timeout to prevent blocking views.
- Handles connection timeouts, HTTP 404/500 errors, rate limits, and offline mode.
- Curated local fallback dictionary so the website never breaks if external network is unavailable.
"""

import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger('devhelp.external_api')

# Curated offline fallback library links
LOCAL_FALLBACK_DOCS = {
    'django': {
        'name': 'Django',
        'version': '6.0+',
        'summary': 'The web framework for perfectionists with deadlines.',
        'docs_url': 'https://docs.djangoproject.com/en/stable/',
        'home_page': 'https://www.djangoproject.com/',
    },
    'python': {
        'name': 'Python Standard Library',
        'version': '3.12+',
        'summary': 'Official Python programming language documentation and tutorials.',
        'docs_url': 'https://docs.python.org/3/',
        'home_page': 'https://www.python.org/',
    },
    'requests': {
        'name': 'Requests',
        'version': '2.32+',
        'summary': 'HTTP for Humans: Elegant and simple HTTP library for Python.',
        'docs_url': 'https://requests.readthedocs.io/',
        'home_page': 'https://requests.readthedocs.io/',
    },
    'gunicorn': {
        'name': 'Gunicorn',
        'version': '23.0+',
        'summary': 'Python WSGI HTTP Server for UNIX / Linux production deployments.',
        'docs_url': 'https://docs.gunicorn.org/',
        'home_page': 'https://gunicorn.org/',
    },
    'whitenoise': {
        'name': 'WhiteNoise',
        'version': '6.8+',
        'summary': 'Radically simplified static file serving for Python web applications.',
        'docs_url': 'https://whitenoise.readthedocs.io/',
        'home_page': 'https://whitenoise.readthedocs.io/',
    },
    'pymongo': {
        'name': 'PyMongo',
        'version': '4.10+',
        'summary': 'Official MongoDB driver for Python applications.',
        'docs_url': 'https://pymongo.readthedocs.io/',
        'home_page': 'https://github.com/mongodb/mongo-python-driver',
    },
}


def lookup_package_docs(package_name: str) -> dict:
    """Look up live package metadata and documentation links from the official PyPI JSON API.

    Args:
        package_name: Name of the Python library (e.g. 'django', 'requests')

    Returns:
        dict with metadata, documentation URL, and status.
    """
    clean_name = (package_name or '').strip().lower()
    if not clean_name:
        return {
            'available': False,
            'source': 'none',
            'error': 'No package name specified.',
        }

    # Restrict package name to safe characters
    safe_name = "".join(c for c in clean_name if c.isalnum() or c in ['-', '_'])
    api_url = f"https://pypi.org/pypi/{safe_name}/json"

    req = urllib.request.Request(
        api_url,
        headers={'User-Agent': 'DevHelpAI-SupportAssistant/1.0 (Educational Assessment)'}
    )

    try:
        # Strict 3.0 second timeout
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                info = data.get('info', {})
                urls = info.get('project_urls') or {}

                # Determine best documentation link
                docs_url = (
                    urls.get('Documentation')
                    or urls.get('Docs')
                    or urls.get('Homepage')
                    or info.get('home_page')
                    or info.get('package_url')
                )

                return {
                    'available': True,
                    'source': 'pypi_api_live',
                    'name': info.get('name', safe_name),
                    'version': info.get('version', 'latest'),
                    'summary': info.get('summary', 'Developer library documentation available.'),
                    'docs_url': docs_url,
                    'home_page': info.get('home_page') or f"https://pypi.org/project/{safe_name}/",
                }
    except Exception as exc:
        logger.warning(f"PyPI API lookup failed for '{safe_name}': {type(exc).__name__}. Falling back to local catalog.")

    # Graceful fallback: Check local curated catalog
    if safe_name in LOCAL_FALLBACK_DOCS:
        item = LOCAL_FALLBACK_DOCS[safe_name].copy()
        item['available'] = True
        item['source'] = 'local_fallback_catalog'
        item['note'] = 'Loaded from local verified developer documentation index.'
        return item

    # Generic friendly fallback for unknown packages when offline
    return {
        'available': False,
        'source': 'fallback',
        'name': safe_name,
        'error': f"External live documentation lookup for '{safe_name}' is currently offline. Refer to official Python docs.",
        'docs_url': 'https://docs.python.org/3/',
        'home_page': 'https://pypi.org/',
    }
