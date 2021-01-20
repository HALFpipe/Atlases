# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from .buckner2011 import from_buckner2011

from .brainnetome import from_brainnetome


def build():
    from .merge import AtlasMerge

    merge = AtlasMerge()

    from_brainnetome(merge)

    from_buckner2011(merge)

    merge.write(f"tpl-{merge.template}_atlas-BrainnetomeCombined_dseg")
