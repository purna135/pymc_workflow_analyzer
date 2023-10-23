import ast

#TODO: fix these to include all functions name
from pymc.distributions import __all__ as pymc_distributions
from pymc.math import __all__ as pymc_math
from pymc.model.core import __all__ as core_models
from pymc.model.transform.conditioning import __all__ as conditioning_models
from pymc.model.fgraph import __all__ as fgraph_models

from arviz.plots import __all__ as arviz_plots

pymc_models = list(core_models) + list(conditioning_models) + list(fgraph_models)

pymc_samplers = [
    "sample", "sample_prior_predictive", "sample_posterior_predictive", "sample_posterior_predictive_w",
    "sample_blackjax_nuts", "sample_numpyro_nuts", "init_nuts", "draw", "NUTS", "HamiltonianMC", 
    "BinaryGibbsMetropolis", "BinaryMetropolis", "CategoricalGibbsMetropolis", "CauchyProposal", 
    "DEMetropolis", "DEMetropolisZ", "LaplaceProposal", "Metropolis", "MultivariateNormalProposal", 
    "NormalProposal", "PoissonProposal", "UniformProposal", "CompoundStep", "Slice",
]

class StaticParser(ast.NodeVisitor):
    """
    A class to parse a Python script and extract information about PyMC usage.
    """
    def __init__(self):
        self.imported_names = {}  # Maps imported names to their original module (e.g., {"Normal": "pymc"})
        self.alias_name = []
        self.report = {
            "number_of_import_statements": 0,
            "imports": [],
            "model": [],
            "distributions": [],
            "samplers": [],
            "math": [],
            "arviz": [],
        }
        
    def visit_Import(self, node):
        """
        Visit an Import node and extract information about the imported library.

        :param node: The Import node to visit.
        """
        for alias in node.names:
            name = alias.name
            if name not in self.report["imports"]:
                self.report["number_of_import_statements"] += 1
                self.report["imports"].append(name)  # Storing the imported library name
            if 'pymc' in name or 'arviz' in name:
                self.alias_name.append(alias.asname or name)
                
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """
        Visit an ImportFrom node and extract information about the imported library.

        :param node: The ImportFrom node to visit.
        """
        module_name = node.module
        if module_name not in self.report["imports"]:
            self.report["number_of_import_statements"] += 1
            self.report["imports"].append(module_name)  # Storing the base module name of the import
        if module_name and ('pymc' in module_name or 'arviz' in module_name):
            for alias in node.names:
                imported_as = alias.asname or alias.name
                self.imported_names[imported_as] = module_name
        self.generic_visit(node)
        
    def get_arg_value(self, arg):
        """
        Get the value of an argument.

        :param arg: The argument to get the value of.
        :return: The value of the argument.
        """
        if isinstance(arg, ast.Constant):
            return arg.value
        elif isinstance(arg, ast.Name):
            return arg.id
        else:
            return ast.dump(arg)

    def visit_Call(self, node):
        """
        Visit a Call node and extract information about the PyMC function being called.

        :param node: The Call node to visit.
        """
        function_name = None

        # Extracting the function name
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in self.alias_name:
                    function_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            function_id = node.func.id
            if function_id in self.imported_names:
                if 'pymc' in self.imported_names[function_id] or 'arviz' in self.imported_names[function_id]:
                    function_name = function_id  # It's a PyMC function
        
        if function_name:
            args = [self.get_arg_value(arg) for arg in node.args]
            kwargs = [keyword.arg for keyword in node.keywords]
            function_info = {"name": function_name, "args": args, "kwargs": kwargs}
            
            if function_name in pymc_models:
                self.report["model"].append(function_info)
            elif function_name in pymc_distributions:
                self.report["distributions"].append(function_info)
            elif function_name in pymc_samplers:
                self.report["samplers"].append(function_info)
            elif function_name in pymc_math:
                self.report["math"].append(function_info)
            elif function_name in arviz_plots:
                self.report["arviz"].append(function_info)

        # continue the visit to other nodes in the syntax tree
        self.generic_visit(node)

    def get_report(self):
        """
        Get the report generated by the parser.

        :return: The report generated by the parser.
        """
        return self.report
