WSGI_TEMPLATE = """

%(relative_paths_setup)s
import sys
sys.path[0:0] = [
  %(path)s,
  ]
%(initialization)s
import %(module_name)s

application = %(module_name)s.%(attrs)s(%(arguments)s)
"""
