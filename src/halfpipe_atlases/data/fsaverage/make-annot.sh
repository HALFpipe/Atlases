#!/bin/bash

verbose=1
run_cmd() {
    cmd="$*"

    printf '%s\n' --------------------

    if [ "${verbose}" = "1" ]; then
        printf "%s\n" "${cmd}"
    fi

    # shellcheck disable=SC2294
    eval "$@"

    exit_code=$?

    if [[ ${exit_code} -gt 0 ]]; then
        echo "ERROR: command exited with nonzero status ${exit_code}"
    fi

    printf '%s\n' --------------------

    return ${exit_code}
}

if [ -z "${FREESURFER_HOME}" ]; then
    echo "ERROR: FREESURFER_HOME is not set"
    exit 1
fi
if [ -z "${CBIG_PATH}" ]; then
    echo "ERROR: CBIG_PATH is not set"
    exit 1
fi

for atlas in aparc aparc.a2009s; do
    for hemi in lh rh; do
        annot="${FREESURFER_HOME}/subjects/fsaverage/label/${hemi}.${atlas}.annot"
        gifti="$(pwd)/${hemi}.${atlas}.gii"
        run_cmd mris_convert \
            --annot "${annot}" \
            "${FREESURFER_HOME}/subjects/fsaverage/surf/${hemi}.white" \
            "${gifti}"
    done

    # Determined from the comments in FreeSurferColorLUT.txt
    if [ "${atlas}" = "aparc" ]; then
        left_hemisphere_offset=1000
        right_hemisphere_offset=2000
    elif [ "${atlas}" = "aparc.a2009s" ]; then
        left_hemisphere_offset=11100
        right_hemisphere_offset=12100
    else
        echo "ERROR: unknown atlas ${atlas}"
        exit 1
    fi

    cat >script.m <<EOF
addpath(genpath('${CBIG_PATH}'));

lh = gifti('lh.${atlas}.gii').cdata';
rh = gifti('rh.${atlas}.gii').cdata';

lh(lh < 0) = 0;
rh(rh < 0) = 0;

lh(lh > 0) = lh(lh > 0) + ${left_hemisphere_offset};
rh(rh > 0) = rh(rh > 0) + ${right_hemisphere_offset};

[nii, ~] = CBIG_RF_projectfsaverage2Vol_single(...
    lh, ...
    rh, ...
    'nearest', ...
    'allSub_fsaverage_to_FSL_MNI152_FS4.5.0_RF_ANTs_avgMapping.prop.mat', ...
    'FSL_MNI152_FS4.5.0_cortex_estimate.nii');
MRIwrite(nii, '${atlas}.nii');
EOF
    run_cmd matlab -nodisplay -nosplash -nodesktop -batch script

    run_cmd rm script.m
done
