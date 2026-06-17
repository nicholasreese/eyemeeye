import os
import sys

project = "Phone Management Application"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
master_doc = "index"

# Ensure the package source is importable for autodoc
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../src"))

autodoc_default_options = {
	"members": True,
	"undoc-members": True,
	"show-inheritance": True,
}
