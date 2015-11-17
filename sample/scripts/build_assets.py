#!/usr/bin/python
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Builds all assets under src/rawassets/, writing the results to assets/.

Finds the flatbuffer compiler and cwebp tool and then uses them to convert the
JSON files to flatbuffer binary files and the png files to webp files so that
they can be loaded by the game. This script also includes various 'make' style
rules. If you just want to build the flatbuffer binaries you can pass
'flatbuffer' as an argument, or if you want to just build the webp files you can
pass 'cwebp' as an argument. Additionally, if you would like to clean all
generated files, you can call this script with the argument 'clean'.
"""

import argparse
import distutils.spawn
import glob
import json
import math
import os
import platform
import shutil
import subprocess
import sys

# Windows uses the .exe extension on executables.
EXECUTABLE_EXTENSION = '.exe' if platform.system() == 'Windows' else ''

# The project root directory, which is one level up from this script's
# directory.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            os.path.pardir))

PREBUILTS_ROOT = os.path.abspath(os.path.join(os.path.join(PROJECT_ROOT),
                                              os.path.pardir,
                                              os.path.pardir,
                                              os.path.pardir,
                                              os.path.pardir,
                                              os.path.pardir,
                                              'prebuilts'))

PINDROP_ROOT = os.path.abspath(os.path.join(os.path.join(PROJECT_ROOT),
                                            os.path.pardir,
                                            os.path.pardir,
                                            os.path.pardir,
                                            'libs', 'pindrop'))

FPLBASE_ROOT = os.path.abspath(os.path.join(os.path.join(PROJECT_ROOT),
                                            os.path.pardir,
                                            os.path.pardir,
                                            os.path.pardir,
                                            'libs', 'fplbase'))

CORGI_ROOT = os.path.abspath(os.path.join(os.path.join(PROJECT_ROOT),
                                           os.path.pardir,
                                           os.path.pardir,
                                           os.path.pardir,
                                           'libs', 'corgi'))

SCENE_LAB_ROOT = os.path.abspath(os.path.join(os.path.join(PROJECT_ROOT),
                                                 os.path.pardir,
                                                 os.path.pardir,
                                                 os.path.pardir,
                                                 'libs', 'scene_lab'))

MOTIVE_ROOT = os.path.abspath(os.path.join(os.path.join(PROJECT_ROOT),
                                           os.path.pardir,
                                           os.path.pardir,
                                           os.path.pardir,
                                           'libs', 'motive'))

FLATBUFFERS_ROOT = os.path.abspath(os.path.join(os.path.join(PROJECT_ROOT),
                                                os.path.pardir,
                                                os.path.pardir,
                                                os.path.pardir,
                                                'libs', 'flatbuffers'))

# Directories that may contains the FlatBuffers compiler.
FLATBUFFERS_PATHS = [
    os.path.join(PROJECT_ROOT, 'bin'),
    os.path.join(PROJECT_ROOT, 'bin', 'Release'),
    os.path.join(PROJECT_ROOT, 'bin', 'Debug'),
    os.path.join(FLATBUFFERS_ROOT, 'Debug'),
    os.path.join(FLATBUFFERS_ROOT, 'Release')
]

# Directory that contains the cwebp tool.
CWEBP_BINARY_IN_PATH = distutils.spawn.find_executable('cwebp')
CWEBP_PATHS = [
    os.path.join(PROJECT_ROOT, 'bin'),
    os.path.join(PROJECT_ROOT, 'bin', 'Release'),
    os.path.join(PROJECT_ROOT, 'bin', 'Debug'),
    os.path.join(PREBUILTS_ROOT, 'libwebp',
                 '%s-x86' % platform.system().lower(),
                 'libwebp-0.4.1-%s-x86-32' % platform.system().lower(), 'bin'),
    os.path.dirname(CWEBP_BINARY_IN_PATH) if CWEBP_BINARY_IN_PATH else '',
]

# Directories that may contains the mesh_pipeline.
MESH_PIPELINE_BINARY_IN_PATH = distutils.spawn.find_executable('mesh_pipeline')
MESH_PIPELINE_PATHS = [
    os.path.join(FPLBASE_ROOT, 'bin', platform.system()),
    os.path.join(PROJECT_ROOT, 'bin', platform.system(), 'Release'),
    os.path.join(PROJECT_ROOT, 'bin', platform.system(), 'Debug'),
    (os.path.dirname(MESH_PIPELINE_BINARY_IN_PATH)
     if MESH_PIPELINE_BINARY_IN_PATH else '')
]

IMAGEMAGICK_IDENTIFY = distutils.spawn.find_executable('identify')
IMAGEMAGICK_CONVERT = distutils.spawn.find_executable('convert')
GRAPHICSMAGICK = distutils.spawn.find_executable('gm')

# Search for the set of ImageMagick binaries in the prebuilts directory.
IMAGEMAGICK_PREBUILTS = [root for root, _, filenames in os.walk(
    os.path.join(PREBUILTS_ROOT, 'imagemagick', '%s-x86_64' %
                 platform.system().lower()),
    followlinks=True) if 'convert' + EXECUTABLE_EXTENSION in filenames]
IMAGEMAGICK_PATHS = [
    IMAGEMAGICK_PREBUILTS[0] if IMAGEMAGICK_PREBUILTS else '',
    os.path.dirname(IMAGEMAGICK_IDENTIFY) if IMAGEMAGICK_IDENTIFY else '',
]

# Directory that contains the anim_pipeline tool.
ANIM_PIPELINE_BINARY_IN_PATH = distutils.spawn.find_executable('anim_pipeline')
ANIM_PIPELINE_PATHS = [
    os.path.join(MOTIVE_ROOT, 'bin', platform.system()),
    os.path.join(MOTIVE_ROOT, 'bin', 'Release', platform.system()),
    os.path.join(MOTIVE_ROOT, 'bin', 'Debug', platform.system()),
    (os.path.dirname(ANIM_PIPELINE_BINARY_IN_PATH)
     if ANIM_PIPELINE_BINARY_IN_PATH else ''),
]

# Directory to place processed assets.
ASSETS_PATH = os.path.join(PROJECT_ROOT, 'assets')

# Directory where unprocessed assets can be found.
RAW_ASSETS_PATH = os.path.join(PROJECT_ROOT, 'src', 'rawassets')

# Metadata file for assets. Store extra file-specific information here.
ASSET_META = os.path.join(RAW_ASSETS_PATH, 'asset_meta.json')

# Directory where unprocessed material flatbuffer data can be found.
RAW_MATERIAL_PATH = os.path.join(RAW_ASSETS_PATH, 'materials')

# Directory where unprocessed textures can be found.
TEXTURE_REL_DIR = 'textures'
RAW_TEXTURE_PATH = os.path.join(RAW_ASSETS_PATH, TEXTURE_REL_DIR)

# Directory where unprocessed FBX files can be found.
MESH_REL_DIR = 'meshes'
RAW_MESH_PATH = os.path.join(RAW_ASSETS_PATH, MESH_REL_DIR)

# Directory where png files are written to before they are converted to webp.
INTERMEDIATE_ASSETS_PATH = os.path.join(PROJECT_ROOT, 'obj', 'assets')

# Directory where png files are written to before they are converted to webp.
INTERMEDIATE_TEXTURE_PATH = os.path.join(INTERMEDIATE_ASSETS_PATH,
                                         TEXTURE_REL_DIR)

# Directory where png files are written to before they are converted to webp.
INTERMEDIATE_MESH_PATH = os.path.join(INTERMEDIATE_ASSETS_PATH, MESH_REL_DIR)

# Directories for animations.
RAW_ANIM_PATH = os.path.join(RAW_ASSETS_PATH, 'anims')

# Directory where unprocessed assets can be found.
SCHEMA_PATHS = [
    os.path.join(PROJECT_ROOT, 'schemas'),
    os.path.join(FPLBASE_ROOT, 'schemas'),
    os.path.join(CORGI_ROOT, 'component_library', 'schemas'),
    os.path.join(SCENE_LAB_ROOT, 'schemas'),
    os.path.join(SCENE_LAB_ROOT, 'sample/schemas'),
    os.path.join(PINDROP_ROOT, 'schemas'),
    os.path.join(MOTIVE_ROOT, 'schemas')
]

# Directory inside the assets directory where flatbuffer schemas are copied.
SCHEMA_OUTPUT_PATH = 'flatbufferschemas'

# Name of the flatbuffer executable.
FLATC_EXECUTABLE_NAME = 'flatc' + EXECUTABLE_EXTENSION

# Name of the cwebp executable.
CWEBP_EXECUTABLE_NAME = 'cwebp' + EXECUTABLE_EXTENSION

# Name of the mesh_pipeline executable.
MESH_PIPELINE_EXECUTABLE_NAME = 'mesh_pipeline' + EXECUTABLE_EXTENSION

# Name of the anim_pipeline executable.
ANIM_PIPELINE_EXECUTABLE_NAME = 'anim_pipeline' + EXECUTABLE_EXTENSION

# What level of quality we want to apply to the webp files.
# Ranges from 0 to 100.
WEBP_QUALITY = 90

# Maximum width or height of a tga image
MAX_TGA_SIZE = 1024

# Display commands executed by run_subprocess().
VERBOSE = False


class FlatbuffersConversionData(object):
  """Holds data needed to convert a set of json files to flatbuffer binaries.

  Attributes:
    schema: The path to the flatbuffer schema file.
    input_files: A list of input files to convert.
  """

  def __init__(self, schema, extension, input_files):
    """Initializes this object's schema and input_files."""
    self.schema = schema
    self.extension = extension
    self.input_files = input_files


def find_in_paths(name, paths):
  """Searches for a file with named `name` in the given paths and returns it."""
  for path in paths:
    full_path = os.path.join(path, name)
    if os.path.isfile(full_path):
      return full_path
  # If not found, just assume it's in the PATH.
  return name


# A list of json files and their schemas that will be converted to binary files
# by the flatbuffer compiler.
FLATBUFFERS_CONVERSION_DATA = [
    FlatbuffersConversionData(
        schema=find_in_paths('scene_lab_config.fbs', SCHEMA_PATHS),
        extension='.bin',
        input_files=[
            os.path.join(RAW_ASSETS_PATH, 'scene_lab_config.json')]),
    FlatbuffersConversionData(
        schema=find_in_paths('components.fbs', SCHEMA_PATHS),
        extension='.bin',
        input_files=[os.path.join(RAW_ASSETS_PATH, 'entity_prototypes.json')]),
    FlatbuffersConversionData(
        schema=find_in_paths('components.fbs', SCHEMA_PATHS),
        extension='.bin',
        input_files=[os.path.join(RAW_ASSETS_PATH, 'entity_list.json')]),
    FlatbuffersConversionData(
        schema=find_in_paths('mesh.fbs', SCHEMA_PATHS),
        extension='.fplmesh',
        input_files=glob.glob(os.path.join(RAW_MESH_PATH, '*.json'))),
    FlatbuffersConversionData(
        schema=find_in_paths('materials.fbs', SCHEMA_PATHS),
        extension='.fplmat',
        input_files=glob.glob(os.path.join(RAW_MATERIAL_PATH, '*.json'))),
]


# Location of FlatBuffers compiler.
FLATC = find_in_paths(FLATC_EXECUTABLE_NAME, FLATBUFFERS_PATHS)

# Location of webp compression tool.
CWEBP = find_in_paths(CWEBP_EXECUTABLE_NAME, CWEBP_PATHS)

# Location of mesh_pipeline conversion tool.
MESH_PIPELINE = find_in_paths(MESH_PIPELINE_EXECUTABLE_NAME,
                              MESH_PIPELINE_PATHS)

# Location of mesh_pipeline conversion tool.
ANIM_PIPELINE = find_in_paths(ANIM_PIPELINE_EXECUTABLE_NAME,
                              ANIM_PIPELINE_PATHS)

# Location of required ImageMagick tools.
IMAGEMAGICK_IDENTIFY = find_in_paths('identify' + EXECUTABLE_EXTENSION,
                                     IMAGEMAGICK_PATHS)
IMAGEMAGICK_CONVERT = find_in_paths('convert' + EXECUTABLE_EXTENSION,
                                    IMAGEMAGICK_PATHS)


def target_file_name(path, target_directory, target_extension):
  """Take the path to a raw png asset and convert it to target webp path.

  Args:
    path: Source file path.
    target_directory: Path to put the target assets.
    target_extension: Extension of target assets.

  Returns:
    Path to the webp file generated from the png file.
  """
  no_path = path.replace(RAW_ASSETS_PATH, '').replace(INTERMEDIATE_ASSETS_PATH, '')
  no_ext = os.path.splitext(no_path)[0]
  target = target_directory + no_ext + '.' + target_extension
  return target


def intermediate_texture_path(path):
  """Take the path to an image and convert it to an intermediate png path.

  Args:
    path: Path to the target assets directory.

  Returns:
    Path to intermediate png file generated from an image path.
  """
  return target_file_name(path, INTERMEDIATE_ASSETS_PATH, 'png')


def processed_texture_path(path, target_directory):
  """Take the path to a raw png asset and convert it to target webp path.

  Args:
    path: Path to the source image file.
    target_directory: Path to the target assets directory.

  Returns:
    Path to processed webp.
  """
  return target_file_name(path, target_directory, 'webp')


def processed_anim_path(path, target_directory):
  """Take the path to a raw anim asset and convert it to target anim path.

  Args:
    path: Path to the source animation file.
    target_directory: Path to the target assets directory.

  Returns:
    Path to output animation file.
  """
  return target_file_name(path, target_directory, 'fplanim')


class BuildError(Exception):
  """Error indicating there was a problem building assets."""

  def __init__(self, argv, error_code, message=None):
    Exception.__init__(self)
    self.argv = argv
    self.error_code = error_code
    self.message = message if message else ''


def run_subprocess(argv, capture=False):
  """Run a command line application.

  Args:
    argv: The command line application path and arguments to pass to it.
    capture: Whether to capture the standard output stream of the application
      and return it from this method.

  Returns:
    Standard output of the command line application if capture=True, None
    otherwise.

  Raises:
    BuildError: If the command fails.
  """
  if VERBOSE:
    print >>sys.stderr, argv
  try:
    if capture:
      process = subprocess.Popen(args=argv, bufsize=-1, stdout=subprocess.PIPE)
    else:
      process = subprocess.Popen(argv)
  except OSError as e:
    raise BuildError(argv, 1, message=str(e))
  stdout, _ = process.communicate()
  if process.returncode:
    raise BuildError(argv, process.returncode)
  return stdout


def convert_json_to_flatbuffer_binary(flatc, json_path, schema, out_dir):
  """Run the flatbuffer compiler on the given json file and schema.

  Args:
    flatc: Path to the flatc binary.
    json_path: The path to the json file to convert to a flatbuffer binary.
    schema: The path to the schema to use in the conversion process.
    out_dir: The directory to write the flatbuffer binary.

  Raises:
    BuildError: Process return code was nonzero.
  """
  command = [flatc, '-o', out_dir]
  for path in SCHEMA_PATHS:
    command.extend(['-I', path])
  command.extend(['-b', schema, json_path])
  run_subprocess(command)


def closest_power_of_two(n):
  """Returns the closest power of two (linearly) to n.

  See: http://mccormick.cx/news/entries/nearest-power-of-two

  Args:
    n: Value to find the closest power of two of.

  Returns:
    Closest power of two to "n".
  """
  return pow(2, int(math.log(n, 2) + 0.5))


def next_highest_power_of_two(n):
  """Returns the next highest power of two to n.

  See: http://mccormick.cx/news/entries/nearest-power-of-two

  Args:
    n: Value to finde the next highest power of two of.

  Returns:
    Next highest power of two to "n".
  """
  return int(pow(2, math.ceil(math.log(n, 2))))


class Image(object):
  """Image attributes.

  Attributes:
    filename: Name of the file the image attributes were retrieved from.
    size: (width, height) tuple of the image in pixels.

  Class Attributes:
    CONVERT: Image conversion tool.
    IDENTIFY: Image identification tool.
  """
  USE_GRAPHICSMAGICK = True
  # Select imagemagick or graphicsmagick convert and identify tools.
  CONVERT = ([GRAPHICSMAGICK, 'convert']
             if USE_GRAPHICSMAGICK and GRAPHICSMAGICK
             else [IMAGEMAGICK_CONVERT])
  IDENTIFY = ([GRAPHICSMAGICK, 'identify']
              if USE_GRAPHICSMAGICK and GRAPHICSMAGICK
              else [IMAGEMAGICK_IDENTIFY])

  def __init__(self, filename, size):
    """Initialize this instance.

    Args:
      filename: Name of the file the image attributes were retrieved from.
      size: (width, height) tuple of the image in pixels.
    """
    self.filename = filename
    self.size = size

  @staticmethod
  def set_environment():
    """Initialize the environment to execute ImageMagick."""
    # If we're using imagemagick tools.
    if IMAGEMAGICK_IDENTIFY in Image.IDENTIFY:
      platform_name = platform.system().lower()
      if platform_name == 'darwin':
        # Need to set DYLD_LIBRARY_PATH for ImageMagick on OSX so it can find
        # shared libraries.
        os.environ['DYLD_LIBRARY_PATH'] = os.path.normpath(os.path.join(
            os.path.dirname(IMAGEMAGICK_IDENTIFY), os.path.pardir, 'lib'))
      elif platform_name == 'linux':
        # Configure shared library, module, filter and configuration paths.
        libs = os.path.normpath(
            os.path.join(os.path.dirname(IMAGEMAGICK_IDENTIFY),
                         os.path.pardir, 'lib', 'x86_64-linux-gnu'))
        config_home = glob.glob(os.path.join(libs, 'ImageMagick*'))
        modules_home = (glob.glob(os.path.join(config_home[0], 'modules-*'))
                        if config_home else '')
        os.environ['LD_LIBRARY_PATH'] = libs
        os.environ['MAGICK_CODER_MODULE_PATH'] = (
            os.path.join(modules_home[0], 'coders') if modules_home else '')
        os.environ['MAGICK_CODER_FILTER_PATH'] = (
            os.path.join(modules_home[0], 'filters') if modules_home else '')
        os.environ['MAGICK_CONFIGURE_PATH'] = (
            os.path.join(config_home[0], 'config') if config_home else '')

  @staticmethod
  def read_attributes(filename):
    """Read attributes of the image.

    Args:
      filename: Path to the image to query.

    Returns:
      Image instance containing attributes read from the image.

    Raises:
      BuildError if it's not possible to read the image.
    """
    identify_args = list(Image.IDENTIFY)
    identify_args.extend(['-format', '%w %h', filename])
    Image.set_environment()
    return Image(filename, [int(value) for value in run_subprocess(
        identify_args, capture=True).split()])

  def calculate_power_of_two_size(self):
    """Calculate the power of two size of this image.

    Returns:
      (width, height) tuple containing the size of the image rounded to the
      next highest power of 2.
    """
    max_dimension_size = max(self.size)
    if max_dimension_size < MAX_TGA_SIZE:
      return [next_highest_power_of_two(d) for d in self.size]
    scale = float(MAX_TGA_SIZE) / max_dimension_size
    return [closest_power_of_two(d * scale) for d in self.size]

  def convert_resize_image(self, target_image, target_image_size=None):
    """Run the image converter to convert this image.

    The source and target formats are identified by the image extension for
    example if this image references "image.tga" and target_image name is
    "image.png" the image will be converted from a tga format image to png
    format.

    Args:
      target_image: The path to the output image file.
      target_image_size: Size of the output image.  If this isn't specified the
        input image size is used.

    Raises:
      BuildError if the conversion process fails.
    """
    convert_args = list(Image.CONVERT)
    convert_args.append(self.filename)
    if self.size != target_image_size:
      convert_args.extend(['-resize', '%dx%d!' % (target_image_size[0],
                                                  target_image_size[1])])
    convert_args.append(target_image)

    # Output status message.
    source_file = os.path.basename(self.filename)
    target_file = os.path.basename(target_image)
    if self.size != target_image_size:
      source_file += ' (%d, %d)' % (self.size[0], self.size[1])
      target_file += ' (%d, %d)' % (target_image_size[0], target_image_size[1])
    print 'Converting %s to %s' % (source_file, target_file)
    Image.set_environment()
    run_subprocess(convert_args)


def convert_png_image_to_webp(cwebp, png, out, quality=80):
  """Run the webp converter on the given png file.

  Args:
    cwebp: Path to the cwebp binary.
    png: The path to the png file to convert into a webp file.
    out: The path of the webp to write to.
    quality: The quality of the processed image, where quality is between 0
        (poor) to 100 (very good). Typical value is around 80.

  Raises:
    BuildError: Process return code was nonzero.
  """
  image = Image.read_attributes(png)
  target_image_size = image.calculate_power_of_two_size()
  if target_image_size != image.size:
    print'Resizing %s from (%d, %d) to (%d, %d)' % (
        png, image.size[0], image.size[1], target_image_size[0],
        target_image_size[1])

  command = [cwebp, '-resize', str(target_image_size[0]),
             str(target_image_size[1]), '-q', str(quality), png, '-o', out]
  run_subprocess(command)


def convert_fbx_mesh_to_flatbuffer_binary(fbx, target_directory,
                                          texture_formats, recenter, hierarchy):
  """Run the mesh_pipeline on the given fbx file.

  Args:
    fbx: The path to the fbx file to convert into a flatbuffer binary.
    target_directory: The path of the flatbuffer binary to write to.
    texture_formats: String containing of texture formats to pass to the
      mesh_pipeline tool.
    recenter: Whether to recenter the exported mesh at the origin.

  Raises:
    BuildError: Process return code was nonzero.
  """
  command = [MESH_PIPELINE, '-d', '-e', 'webp', '-b', target_directory, '-r',
             MESH_REL_DIR, '-f',
             '' if texture_formats is None else texture_formats,
             '' if recenter is None else '-c',
             '' if hierarchy is None else '-h', fbx]
  run_subprocess(command)


def convert_fbx_anim_to_flatbuffer_binary(fbx, target):
  """Run the anim_pipeline on the given fbx file.

  Args:
    fbx: The path to the fbx file to convert into a flatbuffer binary.
    target: The path of the flatbuffer binary to write to.

  Raises:
    BuildError: Process return code was nonzero.
  """
  command = [ANIM_PIPELINE, '-v', '-o', target, fbx]
  run_subprocess(command)


def needs_rebuild(source, target):
  """Checks if the source file needs to be rebuilt.

  Args:
    source: The source file to be compared.
    target: The target file which we may need to rebuild.

  Returns:
    True if the source file is newer than the target, or if the target file
    does not exist.
  """
  return not os.path.isfile(target) or (
      os.path.getmtime(source) > os.path.getmtime(target))


def processed_mesh_path(path, target_directory):
  """Take the path to an fbx asset and convert it to target mesh path.

  Args:
    path: Path to the source mesh file.
    target_directory: Path to the target assets directory.

  Returns:
    Path to the target mesh.
  """
  return path.replace(RAW_ASSETS_PATH, target_directory).replace(
      '.fbx', '.fplmesh')


def processed_json_path(path, target_directory, target_extension):
  """Take the path to a raw json asset and convert it to target bin path.

  Args:
    path: Path to the source JSON file.
    target_directory: Path to the target assets directory.
    target_extension: Extension of the target file.

  Returns:
    Path to the target file from the source JSON.
  """
  return path.replace(RAW_ASSETS_PATH, target_directory).replace(
      '.json', target_extension)


def fbx_files_to_convert():
  """FBX files to convert to fplmesh."""
  return (glob.glob(os.path.join(RAW_MESH_PATH, '*.fbx')))


def texture_files(extension):
  """List of files with `extension` in the texture paths."""
  return (glob.glob(os.path.join(RAW_TEXTURE_PATH, extension)) +
          glob.glob(os.path.join(RAW_MESH_PATH, extension)) +
          glob.glob(os.path.join(INTERMEDIATE_TEXTURE_PATH, extension)) +
          glob.glob(os.path.join(INTERMEDIATE_MESH_PATH, extension)))


def png_files_to_convert():
  """PNG files to convert to webp."""
  return texture_files('*.png')


def tga_files_to_convert():
  """TGA files to convert to png."""
  return texture_files('*.tga')


def anim_files_to_convert():
  """FBX files to convert to fplanim."""
  return (glob.glob(os.path.join(RAW_ANIM_PATH, '*.fbx')))


def mesh_meta_value(fbx, meta, key):
  """Get metadata value from an FBX metadata object.

  Args:
    fbx: File to query within the metadata object.
    meta: Metadata object to query.
    key: Key to query.

  Returns:
    Value associate with the specified key if found, None otherwise.
  """
  mesh_meta = meta['mesh_meta']
  for entry in mesh_meta:
    if entry['name'] in fbx and key in entry:
      return entry[key]
  return None


def generate_mesh_binaries(target_directory, meta):
  """Run the mesh pipeline on the all of the FBX files.

  Args:
    target_directory: Path to the target assets directory.
    meta: Metadata object.
  """
  input_files = fbx_files_to_convert()
  for fbx in input_files:
    target = processed_mesh_path(fbx, target_directory)
    texture_formats = mesh_meta_value(fbx, meta, 'texture_format')
    recenter = mesh_meta_value(fbx, meta, 'recenter')
    hierarchy = mesh_meta_value(fbx, meta, 'hierarchy')
    if needs_rebuild(fbx, target) or needs_rebuild(MESH_PIPELINE, target):
      convert_fbx_mesh_to_flatbuffer_binary(fbx, target_directory,
                                            texture_formats, recenter,
                                            hierarchy)


def generate_anim_binaries(target_directory):
  """Run the mesh pipeline on the all of the FBX files.

  Args:
    target_directory: Path to the target assets directory.
  """
  input_files = anim_files_to_convert()
  for fbx in input_files:
    target = processed_anim_path(fbx, target_directory)
    if needs_rebuild(fbx, target) or needs_rebuild(ANIM_PIPELINE, target):
      convert_fbx_anim_to_flatbuffer_binary(fbx, target)


def generate_flatbuffer_binaries(flatc, target_directory):
  """Run the flatbuffer compiler on the all of the flatbuffer json files.

  Args:
    flatc: Path to the flatc binary.
    target_directory: Path to the target assets directory.
  """
  for element in FLATBUFFERS_CONVERSION_DATA:
    schema = element.schema
    target_schema = os.path.join(target_directory, SCHEMA_OUTPUT_PATH,
                                 os.path.basename(schema))
    if needs_rebuild(schema, target_schema):
      if not os.path.exists(os.path.dirname(target_schema)):
        os.makedirs(os.path.dirname(target_schema))
      shutil.copy2(schema, target_schema)
    for json_file in element.input_files:
      target = processed_json_path(json_file, target_directory,
                                   element.extension)
      target_file_dir = os.path.dirname(target)
      if not os.path.exists(target_file_dir):
        os.makedirs(target_file_dir)
      if needs_rebuild(json_file, target) or needs_rebuild(schema, target):
        convert_json_to_flatbuffer_binary(flatc, json_file, schema,
                                          target_file_dir)


def generate_png_textures():
  """Run the imange converter to convert tga to png files and resize."""
  input_files = tga_files_to_convert()
  for tga in input_files:
    out = intermediate_texture_path(tga)
    out_dir = os.path.dirname(out)
    if not os.path.exists(out_dir):
      os.makedirs(out_dir)
    if needs_rebuild(tga, out):
      image = Image.read_attributes(tga)
      image.convert_resize_image(
          out, image.calculate_power_of_two_size())


def generate_webp_textures(cwebp, target_directory):
  """Run the webp converter on off of the png files.

  Search for the PNG files lazily, since the mesh pipeline may
  create PNG files that need to be processed.

  Args:
    cwebp: Path to the cwebp binary.
    target_directory: Path to the target assets directory.
  """
  input_files = png_files_to_convert()
  for png in input_files:
    out = processed_texture_path(png, target_directory)
    out_dir = os.path.dirname(out)
    if not os.path.exists(out_dir):
      os.makedirs(out_dir)
    if needs_rebuild(png, out):
      convert_png_image_to_webp(cwebp, png, out, WEBP_QUALITY)


def copy_assets(target_directory):
  """Copy modified assets to the target assets directory.

  All files are copied from ASSETS_PATH to the specified target_directory if
  they're newer than the destination files.

  Args:
    target_directory: Directory to copy assets to.
  """
  assets_dir = target_directory
  source_dir = os.path.realpath(ASSETS_PATH)
  if source_dir != os.path.realpath(assets_dir):
    for dirpath, _, files in os.walk(source_dir):
      for name in files:
        source_filename = os.path.join(dirpath, name)
        relative_source_dir = os.path.relpath(source_filename, source_dir)
        target_dir = os.path.dirname(os.path.join(assets_dir,
                                                  relative_source_dir))
        target_filename = os.path.join(target_dir, name)
        if not os.path.exists(target_dir):
          os.makedirs(target_dir)
        if (not os.path.exists(target_filename) or
            (os.path.getmtime(target_filename) <
             os.path.getmtime(source_filename))):
          shutil.copy2(source_filename, target_filename)


def clean_webp_textures(target_directory):
  """Delete all the processed webp textures.

  Args:
    target_directory: Path to the target assets directory.
  """
  input_files = png_files_to_convert()
  for png in input_files:
    webp = processed_texture_path(png, target_directory)
    if os.path.isfile(webp):
      os.remove(webp)


def clean_flatbuffer_binaries(target_directory):
  """Delete all the processed flatbuffer binaries.

  Args:
    target_directory: Path to the target assets directory.
  """
  for element in FLATBUFFERS_CONVERSION_DATA:
    for json_file in element.input_files:
      path = processed_json_path(json_file, target_directory, element.extension)
      if os.path.isfile(path):
        os.remove(path)


def clean(target_directory):
  """Delete all the processed files."""
  clean_flatbuffer_binaries(target_directory)
  clean_webp_textures(target_directory)


def handle_build_error(error):
  """Prints an error message to stderr for BuildErrors."""
  sys.stderr.write('Error running command `%s`. Returned %s.\n%s\n' % (
      ' '.join(error.argv), str(error.error_code), str(error.message)))


def main():
  """Builds or cleans the assets needed for the game.

  To build all assets, either call this script without any arguments. Or
  alternatively, call it with the argument 'all'. To just convert the
  flatbuffer json files, call it with 'flatbuffers'. Likewise to convert the
  png files to webp files, call it with 'webp'. To clean all converted files,
  call it with 'clean'.

  Returns:
    Returns 0 on success.
  """
  parser = argparse.ArgumentParser()
  parser.add_argument('--flatc', default=FLATC,
                      help='Location of the flatbuffers compiler.')
  parser.add_argument('--cwebp', default=CWEBP,
                      help='Location of the webp compressor.')
  parser.add_argument('--output', default=ASSETS_PATH,
                      help='Assets output directory.')
  parser.add_argument('--meta', default=ASSET_META,
                      help='File holding metadata for assets.')
  parser.add_argument('args', nargs=argparse.REMAINDER)
  args = parser.parse_args()
  target = args.args[1] if len(args.args) >= 2 else 'all'
  if target not in ('all', 'png', 'mesh', 'anim', 'flatbuffers', 'webp',
                    'clean'):
    sys.stderr.write('No rule to build target %s.\n' % target)

  # Load the json file that holds asset metadata.
  meta_file = open(args.meta, 'r')
  meta = json.load(meta_file)

  if target != 'clean':
    copy_assets(args.output)
  # The mesh pipeline must run before the webp texture converter,
  # since the mesh pipeline might create textures that need to be
  # converted.
  if target in ('all', 'png'):
    try:
      generate_png_textures()
    except BuildError as error:
      handle_build_error(error)
      return 1
  if target in ('all', 'mesh'):
    try:
      generate_mesh_binaries(args.output, meta)
    except BuildError as error:
      handle_build_error(error)
      return 1
  if target in ('all', 'anim'):
    try:
      generate_anim_binaries(args.output)
    except BuildError as error:
      handle_build_error(error)
      return 1
  if target in ('all', 'flatbuffers'):
    try:
      generate_flatbuffer_binaries(args.flatc, args.output)
    except BuildError as error:
      handle_build_error(error)
      return 1
  if target in ('all', 'webp'):
    try:
      generate_webp_textures(args.cwebp, args.output)
    except BuildError as error:
      handle_build_error(error)
      return 1
  if target == 'clean':
    try:
      clean(args.output)
    except OSError as error:
      sys.stderr.write('Error cleaning: %s' % str(error))
      return 1

  return 0


if __name__ == '__main__':
  sys.exit(main())
