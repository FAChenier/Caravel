# This file contains the settings the script uses. Change them manually as needed. Refer to comments for details.
# NEVER change the structure of this file other than where prescribed.

# Which tablet model to export for. This is passed to KCC, so it depends on it supporting it. Currently, I am not using the
# a setup that allows custom resolutions, so for now this is limited to the following:
# VALID_TABLET_PROFILES = ["K1", "K2", "K34", "K578", "KDX", "KPW", "KPW5", "KV", "KO", "K11", "KS", "KoMT", "KoG", "KoGHD", "KoA", "KoAHD", "KoAH2O", "KoAO", "KoN", "KoC", "KoL", "KoF", "KoS", "KoE"]
# See https://github.com/darodi/kcc#profiles
# Default: 'KoL'
ereader_profile = 'KoL'

# Whether to enable the final step to send to Calibre. Requires Calibre is installed and set up: https://calibre-ebook.com/
# Turning this off will disable metadata features, meaning this entire script becomes useless. Default: True
use_calibre = True

# Settings below are not implemented yet
# ================================================================================================

# Whether to delete files when done or not. Unsafe as the script has limited testing, use at your own risk.
# Some files will always clean up. Default: False
# TODO Not implemented yet, does not do anything
destructive = False

# Calibre Path
# TODO Not implemented yet, does not do anything
calibre_path = ''

# kcc-c2e Path
# TODO Not implemented yet, does not do anything
kcc_path = ''

# Working directory path. Where to store the files the script is working with. Default: current directory (leave empty)
# TODO Not implemented yet, does not do anything.
working_dir = ''