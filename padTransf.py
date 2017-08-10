"""Padded transformation module.

This module provides two functions, warpPerspectivePadded() and
warpAffinePadded(), which compliment the built-in OpenCV functions
warpPerspective() and warpAffine(). These functions calculate the
extent of the warped image and pads both the destination and the
warped image so the extent of both images can be displayed together.
"""


import cv2
import numpy as np


def warpPerspectivePadded(
        src, dst, transf,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0):
    """Performs a perspective warp with padding.

    Required args:
    --------------
    src --- source image, to be warped (numpy.ndarray)
    dst --- destination image, to be padded (numpy.ndarray)
    transf --- (3, 3) transformation matrix (numpy.ndarray)

    Optional kwargs:
    ----------------
    flags, borderMode, borderValue --- See OpenCV docs on
        warpPerspective() for usage and defaults.

    Returns:
    --------
    src_warped --- padded and warped source image (numpy.ndarray)
    dst_padded --- padded destination image (numpy.ndarray)

    See also:
    ---------
    warpAffinePadded() --- for (2, 3) affine transformations
    """

    assert transf.shape == (3, 3), \
        'Perspective transformation shape should be (3, 3).\n' \
        + 'Use warpAffinePadded() for (2, 3) affine transformations.'

    transf = transf / transf[2, 2]  # ensure a legal homography
    if flags in (cv2.WARP_INVERSE_MAP,
                 cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
                 cv2.INTER_NEAREST + cv2.WARP_INVERSE_MAP):
        transf = cv2.invert(transf)[1]
        flags -= cv2.WARP_INVERSE_MAP

    # it is enough to find where the corners of the image go to find
    # the padding bounds; points in clockwise order from origin
    src_h, src_w = src.shape[:2]
    lin_homg_pts = np.array([
        [0, src_w, src_w, 0],
        [0, 0, src_h, src_h],
        [1, 1, 1, 1]])

    # transform points
    transf_lin_homg_pts = transf.dot(lin_homg_pts)
    transf_lin_homg_pts /= transf_lin_homg_pts[2, :]

    # find min and max points
    min_x = np.floor(np.min(transf_lin_homg_pts[0])).astype(int)
    min_y = np.floor(np.min(transf_lin_homg_pts[1])).astype(int)
    max_x = np.ceil(np.max(transf_lin_homg_pts[0])).astype(int)
    max_y = np.ceil(np.max(transf_lin_homg_pts[1])).astype(int)

    # add translation to the transformation matrix to shift to positive values
    anchor_x, anchor_y = 0, 0
    transl_transf = np.eye(3, 3)
    if min_x < 0:
        anchor_x = -min_x
        transl_transf[0, 2] += anchor_x
    if min_y < 0:
        anchor_y = -min_y
        transl_transf[1, 2] += anchor_y
    shifted_transf = transl_transf.dot(transf)
    shifted_transf /= shifted_transf[2, 2]

    # create padded destination image
    dst_shape = dst.shape
    dst_h, dst_w = dst_shape[:2]
    if len(dst_shape) == 3:  # 3-ch image, don't pad the third dimension
        pad_widths = ((anchor_y, max(max_y, dst_h) - dst_h),
                      (anchor_x, max(max_x, dst_w) - dst_w),
                      (0, 0))
    else:
        pad_widths = ((anchor_y, max(max_y, dst_h) - dst_h),
                      (anchor_x, max(max_x, dst_w) - dst_w))
    dst_padded = np.pad(dst, pad_widths, mode='constant', constant_values=0)

    dst_pad_h, dst_pad_w = dst_padded.shape[:2]
    src_warped = cv2.warpPerspective(
        src, shifted_transf, (dst_pad_w, dst_pad_h),
        flags=flags, borderMode=borderMode, borderValue=borderValue)

    return dst_padded, src_warped


def warpAffinePadded(
        src, dst, transf,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0):
    """Performs an affine or Euclidean/rigid warp with padding.

    Required args:
    --------------
    src --- source image, to be warped (numpy.ndarray)
    dst --- destination image, to be padded (numpy.ndarray)
    transf --- (2, 3) transformation matrix (numpy.ndarray)

    Optional kwargs:
    ----------------
    flags, borderMode, borderValue --- See OpenCV docs on
        warpAffine() for usage and defaults.

    Returns:
    --------
    src_warped --- padded and warped source image (numpy.ndarray)
    dst_padded --- padded destination image (numpy.ndarray)

    See also:
    ---------
    warpPerspectivePadded() --- for (3, 3) perspective transformations
    """
    assert transf.shape == (2, 3), \
        'Affine transformation shape should be (2, 3).\n' \
        + 'Use warpPerspectivePadded() for (3, 3) homography transformations.'

    if flags in (cv2.WARP_INVERSE_MAP,
                 cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
                 cv2.INTER_NEAREST + cv2.WARP_INVERSE_MAP):
        transf = cv2.invertAffineTransform(transf)
        flags -= cv2.WARP_INVERSE_MAP

    # it is enough to find where the corners of the image go to find
    # the padding bounds; points in clockwise order from origin
    src_h, src_w = src.shape[:2]
    lin_pts = np.array([
        [0, src_w, src_w, 0],
        [0, 0, src_h, src_h]])

    # transform points
    transf_lin_pts = transf[:, :2].dot(lin_pts) + transf[:, 2].reshape(2, 1)

    # find min and max points
    min_x = np.floor(np.min(transf_lin_pts[0])).astype(int)
    min_y = np.floor(np.min(transf_lin_pts[1])).astype(int)
    max_x = np.ceil(np.max(transf_lin_pts[0])).astype(int)
    max_y = np.ceil(np.max(transf_lin_pts[1])).astype(int)

    # add translation to the transformation matrix to shift to positive values
    anchor_x, anchor_y = 0, 0
    if min_x < 0:
        anchor_x = -min_x
    if min_y < 0:
        anchor_y = -min_y
    shifted_transf = transf + [[0, 0, anchor_x], [0, 0, anchor_y]]

    # create padded destination image
    dst_shape = dst.shape
    dst_h, dst_w = dst_shape[:2]
    if len(dst_shape) == 3:  # 3-ch image, don't pad the third dimension
        pad_widths = ((anchor_y, max(max_y, dst_h) - dst_h),
                      (anchor_x, max(max_x, dst_w) - dst_w),
                      (0, 0))
    else:
        pad_widths = ((anchor_y, max(max_y, dst_h) - dst_h),
                      (anchor_x, max(max_x, dst_w) - dst_w))
    dst_padded = np.pad(dst, pad_widths, mode='constant', constant_values=0)

    dst_pad_h, dst_pad_w = dst_padded.shape[:2]
    src_warped = cv2.warpAffine(
        src, shifted_transf, (dst_pad_w, dst_pad_h),
        flags=flags, borderMode=borderMode, borderValue=borderValue)

    return dst_padded, src_warped
