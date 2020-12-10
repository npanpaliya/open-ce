"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import os
import re

import yaml
import utils

#pylint: disable=too-few-public-methods
class CondaEnvFileGenerator():
    """
    The CondaEnvData class holds all of the information needed to generate a conda
    environment file that can be used to create a conda environment from the built packages.
    """

    def __init__(self,
                 build_commands,
                 external_dependencies,
                 ):
        self._dependency_set = set()
        self._external_dependencies = external_dependencies

        for build_command in build_commands:
            if build_command.runtime_package:
                self._update_conda_env_file_content(build_command)

        self._remove_duplicates()

    def _remove_duplicates(self):
        new_dep_set = set()
        print("Length of original deps set: ", len(self._dependency_set))
        for dep in self._dependency_set:
            py_matched = re.match(r'([\w-]+)([\s=<>]*)(\d[.\d*]*)(.*)', dep)
            if py_matched:
                name = py_matched.group(1)
                if name in new_dep_set:
                    new_dep_set.remove(name)
            new_dep_set.add(dep)
        print("Length of original deps set: ", len(new_dep_set))
        print("Original list: ", self._dependency_set)
        print("New list: ", new_dep_set)
        self._dependency_set = new_dep_set

    #pylint: disable=too-many-arguments
    def write_conda_env_file(self,
                             variant_string,
                             channels=None,
                             output_folder=None,
                             env_file_prefix=utils.CONDA_ENV_FILENAME_PREFIX,
                             path=utils.DEFAULT_OUTPUT_FOLDER ):
        """
        This function writes conda environment files using the dependency dictionary
        created from all the buildcommands.

        It returns the path to the file that was written.
        """

        if not os.path.exists(path):
            os.mkdir(path)

        conda_env_name = env_file_prefix + variant_string
        conda_env_file = conda_env_name + ".yaml"
        conda_env_file = os.path.join(path, conda_env_file)

        channels = _create_channels(channels, output_folder)

        data = dict(
            name = conda_env_name,
            channels = channels,
            dependencies = self._dependency_set,
        )
        with open(conda_env_file, 'w') as outfile:
            outfile.write("#" + utils.OPEN_CE_VARIANT + ":" + variant_string + "\n")
            yaml.dump(data, outfile, default_flow_style=False)
            file_name = conda_env_file

        return file_name

    def _update_deps_lists(self, dependencies):
        if not dependencies is None:
            for dep in dependencies:
                self._dependency_set.add(utils.generalize_version(dep))

    def _update_conda_env_file_content(self, build_command):
        """
        This function updates dependency dictionary for each build command with
        its dependencies both internal and external.
        """
        self._update_deps_lists(build_command.run_dependencies)
        self._update_deps_lists(build_command.packages)

        self._update_deps_lists(self._external_dependencies)

def get_variant_string(conda_env_file):
    """
    Return the variant string from a conda environment file that was added by CondaEnvFileGenerator.
    If a variant string was not added to the conda environment file, None will be returned.
    """
    with open(conda_env_file, 'r') as stream:
        first_line = stream.readline().strip()[1:]
        values = first_line.split(':')
        if values[0] == utils.OPEN_CE_VARIANT:
            return values[1]

    return None


def _create_channels(channels, output_folder):
    result = []

    result.append("file:/" + output_folder)
    if channels:
        result += channels
    result.append("defaults")

    return result
