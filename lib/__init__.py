import os
import sys

current_dir=os.path.dirname(__file__)
libdir_env=os.environ.get("NEGWM_LIBDIR", '')
cfgdir_env=os.environ.get("NEGWM_CFGDIR", '')

if libdir_env:
    libdir=libdir_env
else:
    libdir=current_dir

if cfgdir_env:
    cfgdir=cfgdir_env
else:
    cfgdir=f'{current_dir}/../cfg/'

sys.path.append(libdir)
sys.path.append(cfgdir)
