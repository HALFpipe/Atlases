# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:


def build() -> None:
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            "%(asctime)s [%(levelname)8s] %(funcName)s: "
            "%(message)s (%(filename)s:%(lineno)s)"
        ),
    )

    from nipype import config

    config.enable_debug_mode()

    from .brainnetome import build as brainnetome_build
    from .brainnetome_combined import build as brainnetome_combined_build
    from .buckner2011 import build as buckner2011_build
    from .difumo import build as difumo_build
    from .enigma_task_based import build as enigma_task_based_build
    from .freesurfer_cortical import build as freesurfer_cortical_build
    from .freesurfer_subcortical import build as freesurfer_subcortical_build
    from .hcpmmp1 import build as hcpmmp1_build
    from .hcpmmp1_combined import build as hcpmmp1_combined_build
    from .power2011 import build as power2011_build
    from .schaefer2018_combined import build as schaefer2018_combined_build
    from .ukbiobank import build as ukbiobank_build

    build_fns = [
        difumo_build,
        brainnetome_build,
        brainnetome_combined_build,
        buckner2011_build,
        enigma_task_based_build,
        freesurfer_cortical_build,
        freesurfer_subcortical_build,
        hcpmmp1_build,
        hcpmmp1_combined_build,
        power2011_build,
        schaefer2018_combined_build,
        ukbiobank_build,
    ]

    for build_fn in build_fns:
        build_fn()


if __name__ == "__main__":
    from halfpipe_atlases.build_all import build as build_ext

    build_ext()
