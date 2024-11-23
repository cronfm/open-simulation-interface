#!/usr/local/env python3
# -*- coding: UTF-8 -*-

import os
import subprocess
import sys
import re
from setuptools import setup
from setuptools.command.sdist import sdist
from setuptools.command.build_py import build_py

# Configure the version number
VERSION_MAJOR = None
VERSION_MINOR = None
VERSION_PATCH = None
VERSION_SUFFIX = None

try:
    with open("VERSION", "rt") as version_file:
        for line in version_file:
            if line.startswith("VERSION_MAJOR"):
                VERSION_MAJOR = int(line.split("=")[1].strip())
            elif line.startswith("VERSION_MINOR"):
                VERSION_MINOR = int(line.split("=")[1].strip())
            elif line.startswith("VERSION_PATCH"):
                VERSION_PATCH = int(line.split("=")[1].strip())
            elif line.startswith("VERSION_SUFFIX"):
                VERSION_SUFFIX = line.split("=")[1].strip()
except FileNotFoundError:
    sys.stderr.write("Error: VERSION file not found.\n")
    sys.exit(1)

# Package details
package_name = "osi3"
package_path = os.path.join(os.getcwd(), package_name)

class ProtobufGenerator:
    """
    A class to handle Protobuf file generation.
    """
    PROTOC = os.getenv("PROTOC", "/usr/bin/protoc")

    osi_files = (
        "osi_common.proto",
        "osi_datarecording.proto",
        "osi_detectedlane.proto",
        "osi_detectedobject.proto",
        "osi_detectedoccupant.proto",
        "osi_detectedroadmarking.proto",
        "osi_detectedtrafficlight.proto",
        "osi_detectedtrafficsign.proto",
        "osi_environment.proto",
        "osi_featuredata.proto",
        "osi_groundtruth.proto",
        "osi_hostvehicledata.proto",
        "osi_lane.proto",
        "osi_logicaldetectiondata.proto",
        "osi_logicallane.proto",
        "osi_motionrequest.proto",
        "osi_object.proto",
        "osi_occupant.proto",
        "osi_referenceline.proto",
        "osi_roadmarking.proto",
        "osi_route.proto",
        "osi_sensordata.proto",
        "osi_sensorspecific.proto",
        "osi_sensorview.proto",
        "osi_sensorviewconfiguration.proto",
        "osi_streamingupdate.proto",
        "osi_trafficcommand.proto",
        "osi_trafficcommandupdate.proto",
        "osi_trafficlight.proto",
        "osi_trafficsign.proto",
        "osi_trafficupdate.proto",
        "osi_version.proto",
    )

    @staticmethod
    def find_protoc():
        """Locates the protoc executable."""
        if os.path.exists(ProtobufGenerator.PROTOC):
            return ProtobufGenerator.PROTOC
        else:
            sys.stderr.write(
                "Error: protoc not found at specified location: /usr/bin/protoc.\n"
            )
            sys.exit(1)

    def generate(self):
        """Generates Protobuf messages."""
        sys.stdout.write("Generating Protobuf Version Message\n")
        try:
            with open("osi_version.proto.in", "rt") as fin:
                with open("osi_version.proto", "wt") as fout:
                    for line in fin:
                        fout.write(
                            line.replace("@VERSION_MAJOR@", str(VERSION_MAJOR))
                                .replace("@VERSION_MINOR@", str(VERSION_MINOR))
                                .replace("@VERSION_PATCH@", str(VERSION_PATCH))
                        )
        except FileNotFoundError:
            sys.stderr.write("Error: osi_version.proto.in file not found.\n")
            sys.exit(1)

        pattern = re.compile('^import "osi_')
        for source in self.osi_files:
            source_path = os.path.join(package_path, source)
            try:
                with open(source) as src_file:
                    with open(source_path, "w") as dst_file:
                        for line in src_file:
                            dst_file.write(pattern.sub(f'import "{package_name}/osi_', line))
            except FileNotFoundError:
                sys.stderr.write(f"Error: {source} file not found.\n")
                sys.exit(1)

        for source in self.osi_files:
            sys.stdout.write(f"Protobuf-compiling {source}\n")
            source_path = os.path.join(package_name, source)
            try:
                subprocess.check_call([
                    self.find_protoc(), "--python_out=.", "--pyi_out=.", source_path
                ])
            except subprocess.CalledProcessError as e:
                sys.stderr.write(f"Error: Failed to compile {source}.\n{e}\n")
                sys.exit(1)

    def maybe_generate(self):
        """Generates Protobuf messages only if required files exist."""
        if os.path.exists("osi_version.proto.in"):
            self.generate()


class CustomBuildPyCommand(build_py):
    """Custom build_py command to include Protobuf generation."""
    def run(self):
        ProtobufGenerator().maybe_generate()
        super().run()


class CustomSDistCommand(sdist):
    """Custom sdist command to include Protobuf generation."""
    def run(self):
        ProtobufGenerator().generate()
        super().run()

# Ensure the package directory exists
os.makedirs(package_path, exist_ok=True)

# Create __init__.py with version information
init_file_path = os.path.join(package_path, "__init__.py")
try:
    with open(init_file_path, "wt") as init_file:
        init_file.write(
            f"__version__ = '{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}{VERSION_SUFFIX or ''}'\n"
        )
except OSError as e:
    sys.stderr.write(f"Error: Unable to write to {init_file_path}.\n{e}\n")
    sys.exit(1)

# Setup configuration
setup(
    name=package_name,
    version=f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}{VERSION_SUFFIX or ''}",
    packages=[package_name, "osi3trace"],
    cmdclass={
        "sdist": CustomSDistCommand,
        "build_py": CustomBuildPyCommand,
    },
)
