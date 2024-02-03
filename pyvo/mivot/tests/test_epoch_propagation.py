# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Test for mivot.features.epoch_propagation.py
"""
import os
import pytest
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
from pyvo.mivot.utils.exceptions import TimeFormatException, UnitException, SkyCoordParameterException
from pyvo.mivot.version_checker import check_astropy_version
from pyvo.mivot.viewer.model_viewer_level1 import ModelViewerLevel1
from pyvo.utils import activate_features


activate_features('MIVOT')


def test_epoch_propagation(m_viewer):
    if check_astropy_version() is False:
        pytest.skip("MIVOT test skipped because of the astropy version.")
    row_view = m_viewer.get_next_row_view()
    epoch_propagation = row_view.epoch_propagation
    assert epoch_propagation.sky_coordinate() == row_view.sky_coordinate
    assert epoch_propagation.ref_long == 10.0
    assert epoch_propagation.ref_lat == 10.0
    assert epoch_propagation.ref_pm_long == 10.0
    assert epoch_propagation.ref_pm_lat == -20.0


def test_epoch_propagation_sky_coord(m_viewer):
    if check_astropy_version() is False:
        pytest.skip("MIVOT test skipped because of the astropy version.")
    row_view = m_viewer.get_next_row_view()
    epoch_propagation = row_view.epoch_propagation
    sky_coord_to_compare = (
        SkyCoord(distance=(row_view.parallax.value * row_view.parallax.astropy_unit)
                 .to(u.parsec, equivalencies=u.parallax()),
                 radial_velocity=row_view.radialVelocity.value * u.km / u.s,
                 ra=row_view.longitude.value * u.degree, dec=row_view.latitude.value * u.degree,
                 pm_ra_cosdec=row_view.latitude.value * u.mas / u.yr,
                 pm_dec=row_view.pmLatitude.value * u.mas / u.yr,
                 frame=row_view.Coordinate_coosys.PhysicalCoordSys_frame.spaceRefFrame.value.lower(),
                 obstime=Time(row_view.epoch.value, format="decimalyear")))
    sky_coord_to_compare_from_value = (
        SkyCoord(distance=199.99999999999997 * u.pc, radial_velocity=1234 * u.km / u.s,
                 ra=10 * u.degree, dec=10 * u.degree,
                 pm_ra_cosdec=10 * u.mas / u.yr, pm_dec=-20 * u.mas / u.yr,
                 frame='icrs', obstime=Time(2015.0, format="decimalyear")))
    assert sky_coord_to_compare == sky_coord_to_compare_from_value == epoch_propagation.sky_coordinate()
    assert ((sky_coord_to_compare.apply_space_motion(dt=-42 * u.year).ra,
             sky_coord_to_compare.apply_space_motion(dt=-42 * u.year).dec)
            == epoch_propagation.apply_space_motion(dt=-42 * u.year))
    # Test with the frame galactic
    epoch_propagation.frame = "galactic"
    sky_coord_to_compare_galactic = (
        SkyCoord(distance=199.99999999999997 * u.pc, radial_velocity=1234 * u.km / u.s,
                 l=10 * u.degree, b=10 * u.degree,
                 pm_l_cosb=10 * u.mas / u.yr, pm_b=-20 * u.mas / u.yr,
                 frame='galactic', obstime=Time(2015.0, format="decimalyear")))
    assert epoch_propagation.sky_coordinate() == sky_coord_to_compare_galactic
    # Test with the frame fk4
    epoch_propagation.frame = "fk4"
    epoch_propagation.equinox = 'J2000.0'
    sky_coord_to_compare_fk4 = (
        SkyCoord(distance=199.99999999999997 * u.pc, radial_velocity=1234 * u.km / u.s,
                 ra=10 * u.degree, dec=10 * u.degree,
                 pm_ra_cosdec=10 * u.mas / u.yr, pm_dec=-20 * u.mas / u.yr,
                 frame='fk4', obstime=Time(2015.0, format="decimalyear"), equinox='J2000.0'))
    assert epoch_propagation.sky_coordinate() == sky_coord_to_compare_fk4
    with pytest.raises(
            SkyCoordParameterException,
            match="The equinox attribute is not in the SkyCoord constructor for the frame galactic"):
        epoch_propagation.frame = "galactic"
        epoch_propagation.sky_coordinate()


def test_epoch_propagation_time(m_viewer):
    """
    Test the conversion of the time from MIVOT data to Astropy time format, with each regex.
    """
    if check_astropy_version() is False:
        pytest.skip("MIVOT test skipped because of the astropy version.")
    row_view = m_viewer.get_next_row_view()
    epoch_propagation = row_view.epoch_propagation
    mivot_time_epoch = {"dmtype": "RealQuantity",
                        "value": 2015.0,
                        "unit": "year",
                        "ref": None}
    assert epoch_propagation._mivot_time_to_astropy_time(mivot_time_epoch["value"]).format == 'decimalyear'
    mivot_time_epoch["value"] = 51544.0
    assert epoch_propagation._mivot_time_to_astropy_time(mivot_time_epoch["value"]).format == 'mjd'
    mivot_time_epoch["value"] = 'B1950.0'
    assert epoch_propagation._mivot_time_to_astropy_time(mivot_time_epoch["value"]).format == 'byear_str'
    mivot_time_epoch["value"] = 'J2000.0'
    assert epoch_propagation._mivot_time_to_astropy_time(mivot_time_epoch["value"]).format == 'jyear_str'
    mivot_time_epoch["value"] = '2000:001:00:00:00.000'
    assert epoch_propagation._mivot_time_to_astropy_time(mivot_time_epoch["value"]).format == 'yday'
    mivot_time_epoch["value"] = '2000-01-01 00:00:00.000'
    assert epoch_propagation._mivot_time_to_astropy_time(mivot_time_epoch["value"]).format == 'iso'
    mivot_time_epoch["value"] = '2000-01-01T00:00:00.000'
    assert epoch_propagation._mivot_time_to_astropy_time(mivot_time_epoch["value"]).format == 'isot'
    mivot_time_epoch["value"] = {'year': 2010, 'month': 3, 'day': 1}
    assert epoch_propagation._mivot_time_to_astropy_time(mivot_time_epoch["value"]).format == 'ymdhms'
    with pytest.raises(TimeFormatException,
                       match="Can't find the Astropy Time equivalence for 2000-01-0100:00:00.000"):
        mivot_time_epoch["value"] = '2000-01-0100:00:00.000'
        epoch_propagation._mivot_time_to_astropy_time(mivot_time_epoch["value"])


def test_epoch_propagation_unit(m_viewer):
    """
    Test the conversion of the unit from MIVOT data to Astropy unit format.
    """
    if check_astropy_version() is False:
        pytest.skip("MIVOT test skipped because of the astropy version.")
    row_view = m_viewer.get_next_row_view()
    epoch_propagation = row_view.epoch_propagation
    del row_view.pmLatitude.astropy_unit
    with pytest.raises(UnitException, match="Can't find the Astropy Unit equivalence for mas/year"):
        epoch_propagation._mivot_unit_to_astropy_unit(**vars(row_view.pmLatitude))
    row_view.pmLatitude.astropy_unit = "year"
    assert epoch_propagation._mivot_unit_to_astropy_unit(**vars(row_view.pmLatitude)) == u.year


@pytest.fixture
def m_viewer(data_path):
    if check_astropy_version() is False:
        pytest.skip("MIVOT test skipped because of the astropy version.")
    votable = os.path.join(data_path, "data/simple-annotation-votable.xml")
    return ModelViewerLevel1(votable_path=votable)


@pytest.fixture
def data_path():
    return os.path.dirname(os.path.realpath(__file__))


if __name__ == '__main__':
    pytest.main()
