# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here.
import pathlib
import sys

sys.path.insert(0, pathlib.Path(__file__).parents[2].resolve().as_posix())

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

today_date = __import__('datetime').datetime.now().strftime('%Y-%m-%d')
today_year = __import__('datetime').datetime.now().year

project = 'BendersLib'
copyright = f'2025-{today_year} Peng-Hui Guo (latest update: {today_date})'
author = 'Peng-Hui Guo'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',  # Add links to source code
    'sphinx.ext.napoleon',  # Support for NumPy and Google style docstrings
    'sphinx_copybutton',  # Add copy button to code blocks
    'sphinx_gallery.gen_gallery',  # Generate a gallery of examples
    'sphinxcontrib.mermaid',  # Mermaid diagrams
    # 'sphinx_tabs.tabs',  # Tabbed content, works with Shibuya theme
    'sphinx_inline_tabs',
    'sphinx_tags',
    'sphinx_contributors',
]

# sphinx_tags configuration
tags_create_tags = True

autodoc_default_options = {
    'members': True,  # Document members (methods, attributes, etc.)
    'undoc-members': False,  # Document members that don't have a docstring
    'private-members': False,  # Document private members (like _member)
}

autosummary_generate = True
master_doc = 'index'
templates_path = ['_templates']
html_static_path = ['_static']
exclude_patterns = ['sg_execution_times.rst']
autodoc_member_order = 'bysource'
napoleon_numpy_docstring = True
napoleon_google_docstring = True
add_module_names = False  # Prepend module name to functions/classes
add_function_parentheses = True  # Show parentheses for functions

html_css_files = [
    'custom.css',
]

from sphinx_gallery.sorting import ExplicitOrder

sphinx_gallery_conf = {
    'examples_dirs': ['../../examples'],
    'gallery_dirs': ['examples'],
    # 'download_all_examples': False,
    'capture_repr': ('__repr__', '__str__', '_repr_html_'),
    'filename_pattern': r'\.py',
    'subsection_order': ExplicitOrder([
        '../../examples/basic',
        '../../examples/advanced',
        '../../examples/expert',
        '../../examples/applications',

        '*',

        '../../examples/api'
    ])
}

# from pygments.styles import get_all_styles
# print(list(get_all_styles()))
# Theme and code highlighting
# pygments_style = 'default'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
# html_theme_options = {
#     'description': 'A Benders Decomposition Library in Python',
#     'github_user': 'phguo',
#     'github_repo': 'BendersLib',
#     'github_type': 'star',
#     'link': '#2980b9',
#     'link_hover': '#3498db',
#     'fixed_sidebar': True,
#     # 'show_related': True,
# }
# html_sidebars = {
#     '**': [
#         'about.html',
#         'navigation.html',
#         # 'relations.html',
#         'searchbox.html',
#     ]
# }

# html_theme = 'sphinx_rtd_theme'
# html_theme_options = {
#     'collapse_navigation': True,
#     'sticky_navigation': True,
#     'navigation_depth': -1,
#     'titles_only': False,
#     'includehidden': True,
# }

# html_theme = "pydata_sphinx_theme"
# html_theme_options = {
#     "logo": {
#         # "image_light": "icon.png",
#         "text": "BendersLib",
#     },
#     # "navbar_start": ["navbar-logo"],
#     # "navbar_center": ["navbar-nav"],
#     "icon_links": [
#         {
#             "name": "GitHub",
#             "url": "https://github.com/phguo/BendersLib",
#             "icon": "fab fa-github",
#         },
#         {
#             "name": "PyPI",
#             "url": "https://pypi.org/project/BendersLib/",
#             "icon": "fas fa-box",
#         },
#         {
#             "name": "ReadTheDocs",
#             "url": "https://benderslib.readthedocs.io/",
#             "icon": "fas fa-book",
#         },
#     ],
#     "show_toc_level": -1,
#     "navigation_with_keys": True,
#     # "announcement": "✨ We've just released v1.0.0dev ✨",
#     # "secondary_sidebar_items": ["page-toc", "sg_download_links", "sg_launcher_links"],
#
# }

html_theme = "furo"
html_title = "BendersLib"
html_favicon = '_static/icon.ico'
html_logo = "_static/benderslib_v.png"
navy_blue = "#0066CC"
# nuaa_blue = "#0000ff"
another_blue = "#0769CF"
html_theme_options = {
    "light_css_variables": {
        "color-sidebar-link-text--top-level": navy_blue,
        "color-toc-item-text--active": navy_blue,
        "color-link": navy_blue,
        "color-link--visited": "var(--color-link)",
        "color-link--hover": "var(--color-link)",
        "color-brand-primary": navy_blue,
        "color-brand-content": navy_blue,
        "color-api-name": another_blue,
        "color-highlighted-background": "yellow",
    },
    "dark_css_variables": {
        "color-sidebar-link-text--top-level": navy_blue,
        "color-toc-item-text--active": navy_blue,
        "color-link": navy_blue,
        "color-link--visited": "var(--color-link)",
        "color-link--hover": "var(--color-link)",
        "color-brand-primary": navy_blue,
        "color-brand-content": navy_blue,
        "color-api-name": another_blue,
        "color-highlighted-background": "yellow",
    },
    # "announcement": "This is an Alpha release, the API may change in future and there might be bugs."
    "sidebar_hide_name": True,
}


# html_theme = "shibuya"
# html_baseurl = "https://benders.dev/en/latest/"
# # html_logo = '_static/benderslib.png'
# html_favicon = '_static/icon.ico'
# html_copy_source = True
# html_theme_options = {
#     "accent_color": "indigo",
#     # "accent_color": "blue",
#     # "announcement": "This is a Beta release, the API may change in future and there might be bugs.",
#     "github_url": "https://github.com/phguo/BendersLib",
#     # "discussion_url": "https://github.com/phguo/BendersLib/discussions",
#
#     "show_ai_links": True,
#     "open_in_chatgpt": True,
#     "open_in_claude": True,
#     "open_in_perplexity": True,
# }
# html_context = {
#     "source_type": "github",
#     "source_user": "phguo",
#     "source_repo": "BendersLib",
# }

# html_permalinks_icon = '<span>#</span>'
# html_theme = 'sphinxawesome_theme'

# html_theme = 'insipid'

# html_theme = 'sphinx_book_theme'
# html_title = 'BendersLib'
# html_logo = '_static/benderslib.png'
# html_favicon = '_static/icon.ico'
# html_theme_options = {
#     # "github_url": "https://github.com/phguo/BendersLib",
#     # "repository_url": "https://github.com/phguo/BendersLib",
#     # "repository_branch": "main",
#     # "use_repository_button": False,
#     # "use_issues_button": True,
#     # "use_edit_page_button": False,
#     # "path_to_docs": "docs/",
#     "show_toc_level": 5,
# }


def skip_mangled_private_members(app, what, name, obj, skip, options):
    exclude_list = ['_abc_impl']
    if name in exclude_list:
        return True  # Skip specific members
    if name.startswith('__') and not name.endswith('__'):
        return True  # Skip mangled private members
    return None  # Use default logic for others


def prepend_caution(app, docname, source):
    caution_text = """
.. attention::
    This is an `Alpha version <https://en.wikipedia.org/wiki/Software_release_life_cycle#Alpha>`_, 
    the API may change in future and there might be bugs.
    `Bug and feature reports <https://github.com/phguo/BendersLib/issues>`_ are welcome!
   
"""
    source[0] = caution_text + source[0]


def setup(app):
    # app.connect('source-read', prepend_caution)
    app.connect('autodoc-skip-member', skip_mangled_private_members)
