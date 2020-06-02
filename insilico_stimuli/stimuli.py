# when adding a stimulus class, always add at least the methods "params" and "stimulus".

import numpy as np
from numpy import pi

class StimuliSet:
    """
    Base class for all other stimuli classes.
    """
    def __init__(self):
        pass

    def params(self):
        raise NotImplementedError

    def num_params(self):
        '''
        Returns:
            list: Number of different input parameters for each parameter from the 'params' method.
        '''
        return [len(p[0]) for p in self.params()]

    def stimulus(self, *args, **kwargs):
        raise NotImplementedError

    def params_from_idx(self, idx):
        '''
        labels the different parameter combinations.

        Args:
            idx (int): The index of the desired parameter combination

        Returns:
            list: parameter combinations of the desired index 'idx'
        '''
        num_params = self.num_params()
        c = np.unravel_index(idx, num_params)  # c is tuple
        params = [p[0][c[i]] for i, p in enumerate(self.params())]  # p[0] is parameter content
        return params

    def params_dict_from_idx(self, idx):
        '''
        Args:
            idx (int): The index of the desired parameter combination

        Returns:
            dict: dictionary of the parameter combination specified in 'idx'
        '''
        params = self.params_from_idx(idx)
        return {p[1]: params[i] for i, p in enumerate(self.params())}

    def stimulus_from_idx(self, idx):
        """
        Args:
            idx (int): The index of the desired parameter combination

        Returns: The image as numpy.ndarray with pixel values belonging to the parameter combinations of index 'idx'
        """
        return self.stimulus(**self.params_dict_from_idx(idx))

    def image_batches(self, batch_size):
        """
        Generator function dividing the resulting images from all parameter combinations into batches.

        Args:
            batch_size (int): The number of images per batch.

        Yields: The image batches as numpy.ndarray with shape (batch_size, image height, image width) or
                (num_params % batch_size, image height, image width), for the last batch.
        """
        num_stims = np.prod(self.num_params())
        for batch_start in np.arange(0, num_stims, batch_size):
            batch_end = np.minimum(batch_start + batch_size, num_stims)  # if num_stims < batch_start + batch_size => end of image set
            images = [self.stimulus_from_idx(i)
                          for i in range(batch_start, batch_end)]
            yield np.array(images)

    def images(self):
        '''
        Generates the images for the desired stimuli.

        Returns: The images of all possible parameter combinations as numpy.ndarray with shape
        ('total number of parameter combinations', 'image height', 'image width')
        '''
        num_stims = np.prod(self.num_params())
        return np.array([self.stimulus_from_idx(i) for i in range(num_stims)])


class GaborSet(StimuliSet):
    """
    A class to generate Gabor stimuli as sinusoidal gratings modulated by Gaussian envelope.
    """
    def __init__(self, canvas_size, center_range, sizes, spatial_frequencies, contrasts, orientations, phases,
                 grey_level, pixel_boundaries=None, eccentricities=None, locations=None, relative_sf=True):
        """
        Args:
            canvas_size (list of int): The canvas size [width, height].
            center_range (list of int): The start and end locations for the center positions of the Gabor [x_start, x_end,
                y_start, y_end].
            sizes (list of float): Controls the size of the Gabor envelope. +/- 2 SD of envelope.
            spatial_frequencies (list of float): The inverse of the wavelength of the cosine factor entered in
                [cycles / envelop SD], i.e. depends on size. In order to prevent the occurrence of undesired effects at
                the image borders, the wavelength value should be smaller than one fifth of the input image size.
            contrasts (list of float): Defines the amplitude of the stimulus in %. Takes values from 0 to 1. For a
                grey_level=-0.2 and pixel_boundaries=[-1,1], a contrast of 1 (=100%) means the amplitude of the Gabor
                stimulus is 0.8.
            orientations (list or int): The orientation of the normal to the parallel stripes of a Gabor function. Its
                values are given in [rad] and can range from [0,pi). If orientations is handed to the class as an
                integer, e.g. orientations = 4, then the range from [0,pi) will be divided in 4 evenly spaced
                orientations, namely 0*pi/4, 1*pi/4, 2*pi/4 and 3*pi/4.
            phases (list or int): The phase offset in the cosine factor of the Gabor function. Its values are given in
                [rad] and can range from [0,pi). If phases is handed to the class as an integer, e.g. phases = 4, then
                the range from [0,2*pi) will be divided in 4 evenly spaced phase offsets, namely 0*2pi/4, 1*2pi/4,
                2*2pi/4 and 3*2pi/4.
            grey_level (float): Mean luminance/pixel value.
            pixel_boundaries (list or None): Range of values the monitor can display [lower value, upper value]. Default
                is [-1,1].
            eccentricities (list or None): The eccentricity determining the ellipticity of the Gabor. Takes values from
                [0,1]. For 1 it becomes rectangular.
            locations (list of list or None): list of lists specifying the position of the Gabor. If 'locations' is not
                specified, the Gabors are centered around the grid specified in 'center_range'.
            relative_sf (bool or None): Scale 'spatial_frequencies' by size (True, default) or use absolute units
                (False).
        """
        self.canvas_size = canvas_size
        self.cr = center_range

        if locations is None:
            self.locations = np.array([[x, y] for x in range(self.cr[0], self.cr[1])
                                              for y in range(self.cr[2], self.cr[3])])
        else:
            self.locations = locations

        self.sizes = sizes
        self.spatial_frequencies = spatial_frequencies
        self.contrasts = contrasts
        self.grey_level = grey_level

        if pixel_boundaries is None:
            self.pixel_boundaries = [-1, 1]
        else:
            self.pixel_boundaries = pixel_boundaries

        if type(orientations) is not list:
            self.orientations = np.arange(orientations) * pi / orientations
        else:
            self.orientations = orientations

        if type(phases) is not list:
            self.phases = np.arange(phases) * (2*pi) / phases
        else:
            self.phases = phases

        if eccentricities is None:
            self.gammas = [1]
        else:
            self.gammas = [1 - e ** 2 for e in eccentricities]

        self.relative_sf = relative_sf

    def params(self):
        return [
            (self.locations, 'location'),
            (self.sizes, 'size'),
            (self.spatial_frequencies, 'spatial_frequency'),
            (self.contrasts, 'contrast'),
            (self.orientations, 'orientation'),
            (self.phases, 'phase'),
            (self.gammas, 'gamma')
        ]

    def params_from_idx(self, idx):
        num_params = self.num_params()
        c = np.unravel_index(idx, num_params)
        params = [p[0][c[i]] for i, p in enumerate(self.params())]
        if self.relative_sf:
            params[2] /= params[1]
        return params

    def stimulus(self, location, size, spatial_frequency, contrast, orientation, phase, gamma, **kwargs):
        """
        Args:
            location (list of int): The center position of the Gabor.
            size (float): The overall size of the Gabor envelope.
            spatial_frequency (float): The inverse of the wavelength of the cosine factor.
            contrast (float): Defines the amplitude of the stimulus in %. Takes values from 0 to 1.
            orientation (float): The orientation of the normal to the parallel stripes.
            phase (float): The phase offset of the cosine factor.
            gamma (float): The spatial aspect ratio reflecting the ellipticity of the Gabor.
            **kwargs: Arbitrary keyword arguments.

        Returns: Image of the desired Gabor stimulus as numpy.ndarray.
        """
        x, y = np.meshgrid(np.arange(self.canvas_size[0]) - location[0],
                           np.arange(self.canvas_size[1]) - location[1])
        R = np.array([[np.cos(orientation), -np.sin(orientation)],
                      [np.sin(orientation),  np.cos(orientation)]])

        coords = np.stack([x.flatten(), y.flatten()])
        x, y = R.dot(coords).reshape((2, ) + x.shape)

        envelope = np.exp(-(x ** 2 + gamma * y ** 2) / (2 * (size/4)**2))
        grating = np.cos(spatial_frequency * x * (2*pi) + phase)
        gabor_no_contrast = envelope * grating

        # add contrast
        amplitude = contrast * min(abs(self.pixel_boundaries[0] - self.grey_level),
                                   abs(self.pixel_boundaries[1] - self.grey_level))
        gabor = amplitude * gabor_no_contrast + self.grey_level

        return gabor


class PlaidsSet(GaborSet):
    """
    A class to generate Plaid stimuli by adding two orthogonal Gabors.
    """
    def __init__(self, canvas_size, center_ranges, sizes, spatial_frequencies, orientations, phases,
                 contrasts_preferred, contrasts_orthogonal, grey_level, pixel_boundaries=None, eccentricities=None,
                 locations=None, relative_sf=True):
        """
        Args:
            canvas_size (list of int): The canvas size [width, height]
            center_ranges (list of int): The ranges for the center locations of the Plaid [x_start, x_end, y_start, y_end]
            sizes (list of float): The overall size of the Plaid. +/- 2 SD of envelope
            spatial_frequencies (list of float): cycles / envelop SD, i.e. depends on size
            orientations (list or int): The orientation of the preferred Gabor.
            phases (list or int): The phase offset of the cosine factor of the Plaid. Same value is used for both
                preferred and orthogonal Gabor.
            contrasts_preferred (list of float): Defines the amplitude of the preferred Gabor in %. Takes values from 0
                to 1. For grey_level=-0.2 and pixel_boundaries=[-1,1], a contrast of 1 (=100%) means the amplitude of
                the Gabor stimulus is 0.8.
            contrasts_orthogonal (list of float): Defines the amplitude of the orthogonal Gabor in %. Takes values from
                0 to 1. For grey_level=-0.2 and pixel_boundaries=[-1,1], a contrast of 1 (=100%) means the amplitude
                of the Gabor stimulus is 0.8.
            grey_level (float): Mean luminance/pixel value.
            pixel_boundaries (list or None): Range of values the monitor can display [lower value, upper value]. Default
                is [-1,1].
            eccentricities (list or None): The ellipticity of the Gabor (default: 0). Same value for both preferred and
                orthogonal Gabor. Takes values from [0,1].
            locations (list of list or None): list of lists specifying the location of the Plaid. If 'locations' is not
                specified, the Plaid centers are generated from 'center_ranges' (default is None).
            relative_sf (bool or None): Scale 'spatial_frequencies' by size (True, by default) or use absolute units
                (False).
        """
        self.canvas_size = canvas_size
        self.cr = center_ranges

        if locations is None:
            self.locations = np.array([[x, y] for x in range(self.cr[0], self.cr[1])
                                              for y in range(self.cr[2], self.cr[3])])
        else:
            self.locations = locations

        self.sizes = sizes
        self.spatial_frequencies = spatial_frequencies

        if type(orientations) is not list:
            self.orientations = np.arange(orientations) * pi / orientations
        else:
            self.orientations = orientations

        if type(phases) is not list:
            self.phases = np.arange(phases) * (2*pi) / phases
        else:
            self.phases = phases

        if eccentricities is None:
            self.gammas = [1]
        else:
            self.gammas = [1 - e ** 2 for e in eccentricities]

        self.contrasts_preferred = contrasts_preferred
        self.contrasts_orthogonal = contrasts_orthogonal
        self.grey_level = grey_level

        if pixel_boundaries is None:
            self.pixel_boundaries = [-1, 1]
        else:
            self.pixel_boundaries = pixel_boundaries

        self.relative_sf = relative_sf

    def params(self):
        return [
            (self.locations, 'location'),
            (self.sizes, 'size'),
            (self.spatial_frequencies, 'spatial_frequency'),
            (self.orientations, 'orientation'),
            (self.phases, 'phase'),
            (self.gammas, 'gamma'),
            (self.contrasts_preferred, 'contrast_preferred'),
            (self.contrasts_orthogonal, 'contrast_orthogonal')
        ]

    def stimulus(self, location, size, spatial_frequency, orientation, phase, gamma,
                 contrast_preferred, contrast_orthogonal, **kwargs):
        """
        Args:
            location (list of int): The center position of the Plaid.
            size (float): The overall size of the Plaid envelope.
            spatial_frequency (float): The inverse of the wavelength of the cosine factor of both Gabors.
            orientation (float): The orientation of the preferred Gabor.
            phase (float): The phase offset of the cosine factor for both Gabors.
            gamma (float): The spatial aspect ratio reflecting the ellipticity of both Gabors.
            contrast_preferred (float): Defines the amplitude of the preferred Gabor in %. Takes values from 0 to 1.
            contrast_orthogonal (float): Defines the amplitude of the orthogonal Gabor in %. Takes values from 0 to 1.
            **kwargs: Arbitrary keyword arguments.

        Returns: Pixel intensities of the desired Plaid stimulus as numpy.ndarray.
        """
        gabor_preferred = super().stimulus(
            location=location,
            size=size,
            spatial_frequency=spatial_frequency,
            contrast=contrast_preferred,
            orientation=orientation,
            phase=phase,
            gamma=gamma,
            **kwargs
        )

        gabor_orthogonal = super().stimulus(
            location=location,
            size=size,
            spatial_frequency=spatial_frequency,
            contrast=contrast_orthogonal,
            orientation=orientation + np.pi/2,
            phase=phase,
            gamma=gamma,
            **kwargs
        )

        plaid = gabor_preferred + gabor_orthogonal

        return plaid


class DiffOfGaussians(StimuliSet):
    """
    A class to generate Difference of Gaussians (DoG) by subtracting two Gaussian functions of different sizes.
    """
    def __init__(self, canvas_size, center_range, sizes, sizes_scale_surround, contrasts, contrasts_scale_surround,
                 grey_level, pixel_boundaries=None, locations=None):
        """
        Args:
            canvas_size (list of int): The canvas size [width, height].
            center_range (list of int): The grid of ranges for the center locations [x_start, x_end, y_start, y_end].
            sizes (list of float): Standard deviation of the center Gaussian.
            sizes_scale_surround (list of float): Scaling factor defining how much larger the standard deviation of the
                surround Gaussian is relative to the size of the center Gaussian. Must have values larger than 1.
            contrasts (list of float): Contrast of the center Gaussian in %. Takes values from 0 to 1.
            contrasts_scale_surround (list of float): Contrast of the surround Gaussian relative to the center Gaussian.
            grey_level (float): The mean luminance/pixel value.
            pixel_boundaries (list or None): Range of values the monitor can display [lower value, upper value]. Default
                is [-1,1].
            locations (list of list or None): list of lists specifying the center locations. If 'locations' is not
                specified, the center positions are generated from 'center_range' (default is None).
        """
        self.canvas_size = canvas_size
        self.cr = center_range

        if locations is None:
            self.locations = np.array([[x, y] for x in range(self.cr[0], self.cr[1])
                                              for y in range(self.cr[2], self.cr[3])])
        else:
            self.locations = locations

        self.sizes = sizes
        self.sizes_scale_surround = sizes_scale_surround
        self.contrasts = contrasts
        self.grey_level = grey_level
        self.contrasts_scale_surround = contrasts_scale_surround

        if pixel_boundaries is None:
            self.pixel_boundaries = [-1, 1]
        else:
            self.pixel_boundaries = pixel_boundaries

    def params(self):
        return [
            (self.locations, 'location'),
            (self.sizes, 'size'),
            (self.sizes_scale_surround, 'size_scale_surround'),
            (self.contrasts, 'contrast'),
            (self.contrasts_scale_surround, 'contrast_scale_surround')
        ]

    def gaussian_density(self, coords, mean, scale):
        """
        Args:
            coords: The evaluation points with shape (#points, 2) as numpy.ndarray.
            mean (int): The mean/location of the Gaussian.
            scale (int): The standard deviation of the Gaussian.

        Returns: Unnormalized Gaussian density values evaluated at the positions in 'coords' as numpy.ndarray.
        """
        mean = np.reshape(mean, [1, -1])
        r2 = np.sum(np.square(coords - mean), axis=1)
        return np.exp(-r2 / (2 * scale**2))

    def stimulus(self, location, size, size_scale_surround, contrast, contrast_scale_surround, **kwargs):
        """
        Args:
            location (list of int): The center position of the DoG.
            size (float): Standard deviation of the center Gaussian.
            size_scale_surround (float): Scaling factor defining how much larger the standard deviation of the surround
                Gaussian is relative to the size of the center Gaussian. Must have values larger than 1.
            contrast (float): Contrast of the center Gaussian in %. Takes values from 0 to 1.
            contrast_scale_surround (float): Contrast of the surround Gaussian relative to the center Gaussian.
            **kwargs: Arbitrary keyword arguments.

        Returns: Pixel intensities for desired Difference of Gaussians stimulus as numpy.ndarray.
        """
        if size_scale_surround <= 1:
            raise ValueError("size_surround must be larger than 1.")

        x, y = np.meshgrid(np.arange(self.canvas_size[0]),
                           np.arange(self.canvas_size[1]))
        coords = np.stack([x.flatten(), y.flatten()], axis=-1).reshape(-1, 2)

        center = self.gaussian_density(coords, mean=location, scale=size).reshape(self.canvas_size[::-1])
        surround = self.gaussian_density(coords, mean=location, scale=(size_scale_surround * size)
                                         ).reshape(self.canvas_size[::-1])
        center_surround = center - contrast_scale_surround * surround

        # add contrast
        min_val, max_val = center_surround.min(), center_surround.max()
        amplitude_current = max(np.abs(min_val), np.abs(max_val))
        amplitude_required = contrast * min(np.abs(self.pixel_boundaries[0] - self.grey_level),
                                            np.abs(self.pixel_boundaries[1] - self.grey_level))
        contrast_scaling = amplitude_required / amplitude_current

        diff_of_gaussians = contrast_scaling * center_surround + self.grey_level

        return diff_of_gaussians


class CenterSurround(StimuliSet):
    """
    A class to generate 'Center-Surround' stimuli with optional center and/or surround gratings.
    """
    def __init__(self, canvas_size, center_range, sizes_total, sizes_center, sizes_surround, contrasts_center,
                 contrasts_surround, orientations_center, orientations_surround, spatial_frequencies, phases_center,
                 phases_surround, grey_level, pixel_boundaries=None, locations=None, relative_sf=True):
        """
        Args:
            canvas_size (list of int): The canvas size [width, height].
            center_range (list of int): The grid of ranges for the center locations [x_start, x_end, y_start, y_end].
            sizes_total (list of float): The overall size of the Center-Surround stimulus.
            sizes_center (list of float): The size of the center as a fraction of the overall size. Takes values from 0
                to 1. 'size_center' is a scaling factor for 'size_total' so that 'size_center' * 'size_total' = radius
                of inner circle.
            sizes_surround (list of float): The size of the surround as a fraction of the overall size. Takes values
                from 0 to 1.
            contrasts_center (list of float): The contrast of the center grating in %. Takes values from 0 to 1.
            contrasts_surround (list of float): The contrast of the surround grating in %. Takes values from 0 to 1.
            orientations_center (list or int): The orientation of the center gratings. Takes values from 0 to pi. If
                orientations_center is handed to the class as an integer, e.g. orientations_center = 3, then the range
                from [0,pi) will be divided into 3 evenly spaced orientations, namely 0*pi/3, 1*pi/3 and 2*pi/3.
            orientations_surround (list or int): The orientation of the surround gratings. Takes values from 0 to pi. If
                orientations_surround is handed to the class as an integer, e.g. orientations_surround = 3, then the
                range from [0,pi) will be divided into 3 evenly spaced orientations, namely 0*pi/3, 1*pi/3 and 2*pi/3.
            spatial_frequencies (list of float): The inverse of the wavelength of the gratings in [cycles / envelop SD],
                i.e. depends on size.
            phases_center (list or int): The phase offset of the center sinusoidal gratings. Takes values from -pi to
                pi.
            phases_surround (list or int): The phase offset of the surround sinusoidal gratings. Takes values from -pi
                to pi.
            grey_level (float): The mean luminance/pixel value.
            pixel_boundaries (list of float or None): Range of values the monitor can display. Handed to the class in
                the format [lower pixel value, upper pixel value], default is [-1,1].
            locations (list of list or None): list of lists specifying the center locations (default: None). If
                'locations' is not specified, the center positions are generated from 'center_range'.
            relative_sf (bool or None): Scale 'spatial_frequencies' by size (True, default), otherwise use absolute
                units (False).
        """
        self.canvas_size = canvas_size
        self.cr = center_range

        if locations is None:
            self.locations = np.array([[x, y] for x in range(self.cr[0], self.cr[1])
                                              for y in range(self.cr[2], self.cr[3])])
        else:
            self.locations = locations

        self.sizes_total = sizes_total
        self.sizes_center = sizes_center
        self.sizes_surround = sizes_surround
        self.contrasts_center = contrasts_center
        self.contrasts_surround = contrasts_surround
        self.grey_level = grey_level

        if pixel_boundaries is None:
            self.pixel_boundaries =[-1,1]
        else:
            self.pixel_boundaries = pixel_boundaries

        if type(orientations_center) is not list:
            self.orientations_center = np.arange(orientations_center) * pi / orientations_center
        else:
            self.orientations_center = orientations_center

        if type(orientations_surround) is not list:
            self.orientations_surround = np.arange(orientations_surround) * pi / orientations_surround
        else:
            self.orientations_surround = orientations_surround

        if type(phases_center) is not list:
            self.phases_center = np.arange(phases_center) * (2*pi) / phases_center
        else:
            self.phases_center = phases_center

        if type(phases_surround) is not list:
            self.phases_surround = np.arange(phases_surround) * (2 * pi) / phases_surround
        else:
            self.phases_surround = phases_surround

        self.spatial_frequencies = spatial_frequencies
        self.relative_sf = relative_sf

    def params(self):
        return [
            (self.locations, 'location'),
            (self.sizes_total, 'size_total'),
            (self.sizes_center, 'size_center'),
            (self.sizes_surround, 'size_surround'),
            (self.contrasts_center, 'contrast_center'),
            (self.contrasts_surround, 'contrast_surround'),
            (self.orientations_center, 'orientation_center'),
            (self.orientations_surround, 'orientation_surround'),
            (self.spatial_frequencies, 'spatial_frequency'),
            (self.phases_center, 'phase_center'),
            (self.phases_surround, 'phase_surround')
        ]

    def stimulus(self, location, size_total, size_center, size_surround, contrast_center, contrast_surround,
                 orientation_center, orientation_surround, spatial_frequency, phase_center, phase_surround):
        """
        Args:
            location (list of int): The center position of the Center-Surround stimulus.
            size_total (float): The overall size of the Center-Surround stimulus.
            size_center (float): The size of the center as a fraction of the overall size.
            size_surround (float): The size of the surround as a fraction of the overall size.
            contrast_center (float): The contrast of the center grating in %. Takes values from 0 to 1.
            contrast_surround (float): The contrast of the surround grating in %. Takes values from 0 to 1.
            orientation_center (float): The orientation of the center grating.
            orientation_surround (float): The orientation of the surround grating.
            spatial_frequency (float): The inverse of the wavelength of the gratings. Same wavelength is used for center
                and surround.
            phase_center (float): The cosine phase-offset of the center grating.
            phase_surround (float): The cosine phase-offset of the surround grating.

        Returns: Pixel intensities of the desired Center-Surround stimulus as numpy.ndarray.
        """

        if size_center > size_surround:
            raise ValueError("size_center cannot be larger than size_surround")

        x, y = np.meshgrid(np.arange(self.canvas_size[0]) - location[0],
                           np.arange(self.canvas_size[1]) - location[1])

        R_center = np.array([[np.cos(orientation_center), -np.sin(orientation_center)],
                             [np.sin(orientation_center),  np.cos(orientation_center)]])

        R_surround = np.array([[np.cos(orientation_surround), -np.sin(orientation_surround)],
                               [np.sin(orientation_surround),  np.cos(orientation_surround)]])

        coords = np.stack([x.flatten(), y.flatten()])
        x_center, y_center = R_center.dot(coords).reshape((2, ) + x.shape)
        x_surround, y_surround = R_surround.dot(coords).reshape((2, ) + x.shape)

        norm_xy_center = np.sqrt(x_center ** 2 + y_center ** 2)
        norm_xy_surround = np.sqrt(x_surround ** 2 + y_surround ** 2)

        envelope_center = (norm_xy_center <= size_center * size_total)
        envelope_surround = (norm_xy_surround > size_surround * size_total) * (norm_xy_surround <= size_total)

        grating_center = np.cos(spatial_frequency * x_center * (2*pi) + phase_center)
        grating_surround = np.cos(spatial_frequency * x_surround * (2*pi) + phase_surround)

        # add contrast
        amplitude_center = contrast_center * min(abs(self.pixel_boundaries[0] - self.grey_level),
                                                 abs(self.pixel_boundaries[1] - self.grey_level))
        amplitude_surround = contrast_surround * min(abs(self.pixel_boundaries[0] - self.grey_level),
                                                     abs(self.pixel_boundaries[1] - self.grey_level))

        grating_center_contrast = amplitude_center * grating_center
        grating_surround_contrast = amplitude_surround * grating_surround

        return envelope_center * grating_center_contrast + envelope_surround * grating_surround_contrast

