from collections import namedtuple
from math import pi
from pytest import approx, fixture
from sympy import S, sin, cos, sqrt
from symplyphysics import (
    units,
    convert_to,
    Quantity,
    SI,
)
from symplyphysics.core.coordinate_systems.coordinate_systems import CoordinateSystem
from symplyphysics.core.fields.vector_field import VectorField
from symplyphysics.definitions import circulation_is_integral_along_curve as circulation_def


@fixture(name="test_args")
def test_args_fixture():
    C = CoordinateSystem()
    force_unit = Quantity(1 * units.newton)
    radius_unit = Quantity(1 * units.meter)
    # field is a field of gravitational forces, force is directed down by the Y coordinate
    # field is (0, -1 * G * m * M / y**2)
    # G * m * M = force * length**2 / mass**2 * mass**2 = force * length**2
    field = VectorField(C, lambda point: [0, -1 * force_unit * radius_unit**2 / point.y**2])
    Args = namedtuple("Args", ["C", "force_unit", "radius_unit", "field"])
    return Args(C=C, force_unit=force_unit, radius_unit=radius_unit, field=field)


def test_basic_circulation(test_args):
    field = VectorField(test_args.C, lambda point: [point.y, 0, point.x + point.z])
    curve = [cos(circulation_def.parameter), sin(circulation_def.parameter)]
    result = circulation_def.calculate_circulation(field, curve, 0, pi / 2)
    assert convert_to(result, S.One).evalf(4) == approx(-pi / 4, 0.001)


def test_two_parameters_circulation(test_args):
    field = VectorField(test_args.C, lambda point: [point.y, -point.x, 0])
    # circle function is: x**2 + y**2 = 9
    # parametrize by circulation_def.parameter
    circle = [3 * cos(circulation_def.parameter), 3 * sin(circulation_def.parameter)]
    result = circulation_def.calculate_circulation(field, circle, 0, 2 * pi)
    assert convert_to(result, S.One).evalf(4) == approx(-18 * pi, 0.001)
    # now try to define trajectory without parametrization
    # parametrized solution uses angle [0, 2*pi] that corresponds to the counter-clockwise direction
    # so we should integrate in the same direction: [r, -r] for upper part of the circle and [-r, r] for lower
    # y = sqrt(9 - x**2) for upper part of the circle
    # y = -sqrt(9 - x**2) for lower part of the circle
    circle_implicit_up = [circulation_def.parameter, sqrt(9 - circulation_def.parameter**2)]
    result_up = circulation_def.calculate_circulation(field, circle_implicit_up, 3, -3)
    circle_implicit_down = [circulation_def.parameter, -sqrt(9 - circulation_def.parameter**2)]
    result_down = circulation_def.calculate_circulation(field, circle_implicit_down, -3, 3)
    assert (convert_to(result_up, S.One).evalf(4) +
        convert_to(result_down, S.One).evalf(4)) == approx(-18 * pi, 0.001)


def test_orthogonal_movement_circulation(test_args):
    field = VectorField(test_args.C, lambda point: [point.y, -point.x, 1])
    # trajectory is upwards helix
    helix = [
        cos(circulation_def.parameter),
        sin(circulation_def.parameter), circulation_def.parameter
    ]
    result = circulation_def.calculate_circulation(field, helix, 0, 2 * pi)
    assert convert_to(result, S.One) == 0
    # trajectory is upwards straight line
    trajectory_vertical = [1, 0, circulation_def.parameter]
    result = circulation_def.calculate_circulation(field, trajectory_vertical, 0, 2 * pi)
    assert convert_to(result, S.One) == approx(2 * pi, 0.001)


def test_force_circulation(test_args):
    # trajectory is linear: y = x
    #HACK: gravitational force is undefined at 0 distance, use any non-zero value
    trajectory = [circulation_def.parameter, circulation_def.parameter]
    result = circulation_def.calculate_circulation(test_args.field, trajectory,
        1 * test_args.radius_unit, 2 * test_args.radius_unit)
    assert SI.get_dimension_system().equivalent_dims(result.dimension, units.energy)
    result_work = convert_to(result, units.joule).evalf(2)
    assert result_work == approx(-0.5, 0.01)


def test_force_circulation_horizontal(test_args):
    # trajectory is horizontal line: y = 5
    trajectory_horizontal = [circulation_def.parameter, 5 * test_args.radius_unit]
    result = circulation_def.calculate_circulation(test_args.field, trajectory_horizontal,
        1 * test_args.radius_unit, 2 * test_args.radius_unit)
    assert convert_to(result, S.One) == 0


def test_force_circulation_horizontal_up(test_args):
    # trajectory is vertical line: x = 5
    trajectory_vertical = [5 * test_args.radius_unit, circulation_def.parameter]
    result = circulation_def.calculate_circulation(test_args.field, trajectory_vertical,
        1 * test_args.radius_unit, 2 * test_args.radius_unit)
    result_work = convert_to(result, units.joule).evalf(2)
    assert result_work == approx(-0.5, 0.01)


def test_force_circulation_horizontal_down(test_args):
    # trajectory is vertical line, but with down direction: x = 6
    trajectory_vertical = [6 * test_args.radius_unit, circulation_def.parameter]
    result = circulation_def.calculate_circulation(test_args.field, trajectory_vertical,
        2 * test_args.radius_unit, 1 * test_args.radius_unit)
    result_work = convert_to(result, units.joule).evalf(2)
    assert result_work == approx(0.5, 0.01)
