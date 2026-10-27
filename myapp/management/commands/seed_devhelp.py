from django.core.management.base import BaseCommand
from myapp.models import FAQ, ErrorCode


class Command(BaseCommand):
    help = "Seed realistic software-development FAQs and standard Error Codes for DevHelp AI."

    def handle(self, *args, **options):
        self.stdout.write("Seeding DevHelp AI FAQs and Error Codes...")

        faqs = [
            {
                "question": "What is Django?",
                "answer": "Django is a high-level Python web framework designed for rapid development and pragmatic, clean design. It follows the 'batteries-included' philosophy, offering a built-in Object-Relational Mapper (ORM), admin interface, user authentication, form handling, and robust security protections against CSRF, SQL injection, and XSS.",
                "category": FAQ.Category.DJANGO,
                "keywords": "django, framework, python, mvt, orm, batteries included",
            },
            {
                "question": "What is the difference between a project and an app in Django?",
                "answer": "A Django 'project' represents the entire web application and its overall configuration (settings, root URL routing, and database config). An 'app' is a self-contained, modular Python package within the project that serves a specific business function (such as users, blog, or store). A single project can compose multiple apps, and apps can be reused across different projects.",
                "category": FAQ.Category.DJANGO,
                "keywords": "project, app, architecture, settings, modularity",
            },
            {
                "question": "What is a database migration?",
                "answer": "A database migration is Django's mechanism for propagating Python model changes (such as adding fields, modifying constraints, or creating tables) into your SQL database schema. Running 'python manage.py makemigrations' packages your model modifications into version-controlled migration files, and 'python manage.py migrate' applies them to the database safely without manual SQL scripts.",
                "category": FAQ.Category.DATABASE,
                "keywords": "migration, makemigrations, migrate, schema, sql, orm",
            },
            {
                "question": "What does an environment variable do?",
                "answer": "An environment variable is a dynamic key-value pair maintained outside your codebase by the operating system or runtime environment. In web development, environment variables decouple sensitive secrets (API keys, SECRET_KEY, database passwords) and environment-specific settings (DEBUG=True/False, ALLOWED_HOSTS) from source code, complying with the Twelve-Factor App methodology.",
                "category": FAQ.Category.SECURITY,
                "keywords": "env, environment variable, dotenv, secrets, 12factor, security",
            },
            {
                "question": "How do I create a virtual environment?",
                "answer": "A virtual environment isolates Python dependencies per project to avoid package version conflicts. On Windows/Linux/macOS, run:\n1. 'python -m venv venv' to create the environment folder.\n2. Activate it on Windows: '.\\venv\\Scripts\\activate' (or 'source venv/bin/activate' on macOS/Linux).\n3. Install project dependencies: 'pip install -r requirements.txt'.",
                "category": FAQ.Category.PYTHON,
                "keywords": "venv, virtual environment, pip, dependencies, isolation",
            },
            {
                "question": "What causes a 404 error?",
                "answer": "An HTTP 404 Not Found error indicates that the server is operational but cannot locate the resource requested by the URL path. In Django, this occurs when the incoming URL pattern does not match any route defined in 'urlpatterns', or when an ORM lookup like 'get_object_or_404()' receives a primary key that does not exist in the database.",
                "category": FAQ.Category.WEB_HTTP,
                "keywords": "404, not found, url, routing, get_object_or_404, http",
            },
            {
                "question": "What causes a 500 error?",
                "answer": "An HTTP 500 Internal Server Error is a generic server-side failure indicating that the web application encountered an unhandled exception while processing the request. Common causes include unhandled Python exceptions (e.g., AttributeError, KeyError), database connection drops, syntax errors in templates, or missing third-party API error handling.",
                "category": FAQ.Category.WEB_HTTP,
                "keywords": "500, internal server error, exception, crash, traceback, bug",
            },
            {
                "question": "What does HTTP 429 mean?",
                "answer": "HTTP 429 Too Many Requests signifies that the client has exceeded the server's rate limits or API quota within a given timeframe. To resolve it, inspect the 'Retry-After' response header, implement exponential backoff retry algorithms, utilize client-side caching, or upgrade API quota limits.",
                "category": FAQ.Category.WEB_HTTP,
                "keywords": "429, rate limit, quota, too many requests, retry-after, throttle",
            },
            {
                "question": "How do I debug a Python error?",
                "answer": "Effective Python debugging involves:\n1. Reading the traceback from the bottom up to identify the exact file, line number, and exception type.\n2. Reproducing the issue with a minimal reproducible example.\n3. Using Python's built-in breakpoint() or pdb to step through variables interactively.\n4. Adding structured logging with Python's logging module rather than bare print statements.\n5. Writing automated unit tests with Django's TestCase to verify edge conditions.",
                "category": FAQ.Category.PYTHON,
                "keywords": "debugging, traceback, pdb, breakpoint, logging, unit tests",
            },
            {
                "question": "How do I keep API keys secure?",
                "answer": "To protect API keys and sensitive credentials:\n1. Never hardcode credentials into source code, templates, or client-side JavaScript.\n2. Store keys in a local '.env' file during development and in environment variables on your production host.\n3. Add '.env' to your '.gitignore' file immediately before committing any code.\n4. Use placeholder templates like '.env.example' for team documentation.\n5. If a key is accidentally committed, revoke and rotate it immediately.",
                "category": FAQ.Category.SECURITY,
                "keywords": "api keys, security, credentials, gitignore, env, secret key",
            },
            {
                "question": "What is CSRF and why does Django require CSRF tokens?",
                "answer": "Cross-Site Request Forgery (CSRF) is an attack where an untrusted site trick a victim's browser into executing unwanted actions on a trusted site where the user is currently authenticated. Django protects against this by issuing a unique cryptographic CSRF token for each session via the '{% csrf_token %}' template tag and validating it on all incoming POST, PUT, and DELETE requests.",
                "category": FAQ.Category.SECURITY,
                "keywords": "csrf, security, post, csrfmiddlewaretoken, protection",
            },
            {
                "question": "What is the difference between SQLite and PostgreSQL in production?",
                "answer": "SQLite is a lightweight, serverless file-based SQL database ideal for local development, testing, and smaller workloads. PostgreSQL is a full client-server database capable of handling high concurrency, row-level locking, complex JSON querying, and horizontal connection pooling. Django's ORM allows you to develop with SQLite locally and switch to PostgreSQL in production simply by updating 'DATABASES['default']'.",
                "category": FAQ.Category.DATABASE,
                "keywords": "sqlite, postgresql, database, production, concurrency, orm",
            },
        ]

        faq_count = 0
        for data in faqs:
            _, created = FAQ.objects.update_or_create(
                question=data["question"],
                defaults=data,
            )
            if created:
                faq_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully processed {len(faqs)} FAQs (created {faq_count} new)."))

        error_codes = [
            {
                "code": "400",
                "title": "Bad Request",
                "status_code": 400,
                "description": "The server could not understand or process the request due to invalid client syntax, malformed request routing, or deceptive request routing.",
                "common_causes": "• Malformed JSON payload in POST/PUT request\n• Missing required form fields or parameter validation failure\n• Corrupted cookies or oversized request headers\n• Invalid query parameters or malformed characters in URL",
                "troubleshooting_steps": "1. Inspect browser Network tab to view the exact payload sent in the request body.\n2. Check server-side logs to see which form field or JSON parser rejected the request.\n3. Verify Content-Type headers match the body format (e.g. application/json).\n4. Clear browser cookies and cache for the domain.",
                "suggested_fixes": "• Validate user input with Django forms or serializers before submission.\n• Ensure frontend fetch/axios calls set 'Content-Type: application/json' and serialize with JSON.stringify().\n• Implement clean error messages pinpointing exactly which field failed validation.",
            },
            {
                "code": "401",
                "title": "Unauthorized",
                "status_code": 401,
                "description": "The client request lacks valid authentication credentials for the requested target resource.",
                "common_causes": "• Missing Authorization header in API requests\n• Expired, revoked, or invalid JWT or OAuth token\n• Session cookie expired or cleared\n• Incorrect username or password on login endpoints",
                "troubleshooting_steps": "1. Check if the Authorization header is present (e.g. 'Bearer <token>').\n2. Verify session expiration time in Django settings (SESSION_COOKIE_AGE).\n3. Test authentication credentials directly via curl or Postman.",
                "suggested_fixes": "• Refresh expired access tokens using a refresh token workflow.\n• Redirect unauthenticated users to the login view with a 'next' redirect URL parameter.\n• Ensure the frontend includes credentials in fetch requests ('credentials: same-origin').",
            },
            {
                "code": "403",
                "title": "Forbidden",
                "status_code": 403,
                "description": "The server understood the client's identity, but refuses to authorize access. Unlike 401, re-authenticating will not grant permission.",
                "common_causes": "• Missing or invalid CSRF token on POST/PUT requests in Django\n• Insufficient permissions or role privileges (e.g. non-staff accessing /admin/)\n• File system permission restrictions on the web server\n• IP address whitelisting or firewall blocks",
                "troubleshooting_steps": "1. For Django web forms, confirm '{% csrf_token %}' is present inside the <form> tags.\n2. For AJAX/fetch requests, confirm 'X-CSRFToken' header is passed.\n3. Check user permissions using 'request.user.is_staff' or permission decorators.",
                "suggested_fixes": "• Add '{% csrf_token %}' to all POST templates.\n• Use Django's '@login_required' and '@permission_required' decorators appropriately.\n• Verify server directory permissions allow the web server user (www-data) to read static files.",
            },
            {
                "code": "404",
                "title": "Not Found",
                "status_code": 404,
                "description": "The server cannot find the requested URL path. It either does not exist, was moved, or was mistyped.",
                "common_causes": "• Typo in the URL address bar or frontend link\n• Missing URL pattern in 'urls.py' routing configuration\n• Database lookup failed (e.g. 'get_object_or_404' looking up a deleted or non-existent ID)\n• Trailing slash mismatch (e.g. requesting /about when route expects /about/)",
                "troubleshooting_steps": "1. Check the exact URL requested against 'myproject/urls.py' and 'myapp/urls.py'.\n2. Verify whether Django's APPEND_SLASH setting is affecting the request.\n3. Verify if the database ID exists in SQLite/PostgreSQL.",
                "suggested_fixes": "• Add missing path patterns in 'urls.py'.\n• Use Django's '{% url \"route_name\" %}' template tag instead of hardcoded link strings.\n• Provide a helpful custom 404 page with search links and a link back to homepage.",
            },
            {
                "code": "429",
                "title": "Too Many Requests",
                "status_code": 429,
                "description": "The user or client has sent too many requests in a given amount of time ('rate limiting').",
                "common_causes": "• Aggressive polling or infinite loops in frontend JavaScript\n• Third-party AI API quota limits exceeded (e.g. Google Gemini free tier quota)\n• Brute-force protection or anti-scraping middleware triggered",
                "troubleshooting_steps": "1. Check the 'Retry-After' response header to see how many seconds to wait.\n2. Review external API dashboard (e.g. Google AI Studio) to inspect quota usage.\n3. Check browser network tab for rapid repeated requests.",
                "suggested_fixes": "• Implement exponential backoff in retry logic.\n• Cache responses locally or in Redis to avoid redundant API calls.\n• Debounce user input on search bars and autocomplete fields (300ms–500ms).",
            },
            {
                "code": "500",
                "title": "Internal Server Error",
                "status_code": 500,
                "description": "The server encountered an unhandled exception or critical error that prevented it from fulfilling the request.",
                "common_causes": "• Unhandled Python exception (e.g. KeyError, TypeError, DatabaseError)\n• Database connection failure or unapplied migrations\n• Missing environment variable (e.g. GEMINI_API_KEY, SECRET_KEY)\n• Template syntax error or missing context variable",
                "troubleshooting_steps": "1. Check server terminal or log files for full Python tracebacks.\n2. In local development with DEBUG=True, inspect Django's interactive debug screen.\n3. Run 'python manage.py check' and 'python manage.py migrate'.",
                "suggested_fixes": "• Wrap risky operations (external API calls, file I/O) in try-except blocks with clean fallback handling.\n• Ensure all required environment variables are set in .env.\n• Provide a friendly, branded custom 500.html page in production so users are not stranded.",
            },
            {
                "code": "503",
                "title": "Service Unavailable",
                "status_code": 503,
                "description": "The server is currently unable to handle the request due to temporary maintenance or capacity overload.",
                "common_causes": "• Upstream service or external API is down or undergoing maintenance\n• Server CPU/memory exhaustion\n• Web application daemon (e.g. gunicorn) crashed and is restarting",
                "troubleshooting_steps": "1. Verify whether upstream services (Gemini API, database) are reachable.\n2. Check server resource consumption (CPU, RAM, disk space).\n3. Inspect deployment hosting status page.",
                "suggested_fixes": "• Set up health check endpoints (/health/) to monitor server readiness.\n• Implement graceful fallbacks so the app operates in offline mode when AI services are temporarily down.\n• Use a load balancer or process manager with automatic restart capabilities.",
            },
            {
                "code": "DEV001",
                "title": "AI Assistant Unavailable",
                "status_code": None,
                "description": "DevHelp AI custom site error: The Gemini AI Support Assistant service could not process the request.",
                "common_causes": "• GEMINI_API_KEY is missing or invalid in .env / environment\n• Google GenAI service connection timeout or network outage\n• AI quota limit reached for the current day/minute",
                "troubleshooting_steps": "1. Verify GEMINI_API_KEY is configured in your project .env file.\n2. Test outgoing internet connectivity from the server.\n3. Check server logs for GeminiServiceError details.",
                "suggested_fixes": "• The DevHelp AI site continues to function normally using the database FAQ and Error Guide.\n• Visitors can use the manual 'Ask a Question / Submit Ticket' form to submit their query to support.\n• Configure a valid GEMINI_API_KEY in the hosting environment variables.",
            },
        ]

        err_count = 0
        for data in error_codes:
            _, created = ErrorCode.objects.update_or_create(
                code=data["code"],
                defaults=data,
            )
            if created:
                err_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully processed {len(error_codes)} Error Codes (created {err_count} new)."))
        self.stdout.write(self.style.SUCCESS("DevHelp AI seed complete!"))
