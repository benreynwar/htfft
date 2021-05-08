def int_to_str(value, width):
    """
    Outputs a string of the binary of the value with
    LSB to the left.
    """
    s = bin(value)[2:]
    assert len(s) <= width
    s = '0' * (width - len(s)) + s
    return s


def signed_to_slv(value, width):
    """
    Takes a value between -1 to 1 inclusive and maps it
    into `width` bits.
    >>> bin(signed_to_slv(1, 8))
    '0b1000000'
    >>> bin(signed_to_slv(-1, 8))
    '0b11000000'
    """
    assert abs(value) <= 1
    max_mag = pow(2, width-2)
    scaled = round(value * max_mag)
    if scaled < 0:
        scaled = pow(2, width) + scaled
    assert scaled < pow(2, width)
    assert isinstance(scaled, int)
    return scaled


def slv_to_signed(value, width):
    max_mag = pow(2, width-2)
    if value >= pow(2, width-1):
        value = value - pow(2, width)
    scaled = value / max_mag
    assert scaled <= 1
    return scaled


def complex_to_slv(value, width):
    """
    Maps a complex number, `value`, (with mag <= 1) to an integer with
    bit width of width `width`.
    >>> bin(complex_to_slv(1+0j, 12))
    '0b10000000000'
    >>> bin(complex_to_slv(0.5-0.5j, 12))
    '0b1000111000'
    """
    assert width % 2 == 0
    assert abs(value) <= 1
    mapped_real = signed_to_slv(value.real, width//2)
    mapped_imag = signed_to_slv(value.imag, width//2)
    mapped = mapped_imag + mapped_real * pow(2, width//2)
    return mapped


def complex_from_slv(value, width):
    """
    Maps an integer (with bit-width `width`)
    to a complex number.
    """
    assert value < pow(2, width)
    assert width % 2 == 0
    real_part = value >> width//2
    imag_part = value % pow(2, width//2)
    imag_float = slv_to_signed(imag_part, width//2)
    real_float = slv_to_signed(real_part, width//2)
    as_complex = real_float + imag_float * (0+1j)
    return as_complex


def list_of_complex_to_slv(values, width):
    slv = 0
    f = 1
    for value in values:
        slv += complex_to_slv(value, width) * f
        f = f << width
    return slv


def list_of_complex_from_slv(value, width, size):
    assert value < pow(2, width*size)
    bits = ''.join(reversed(bin(value)[2:]))
    assert len(bits) <= width * size
    bits += '0' * (width*size - len(bits))
    lumps = [bits[index*width: (index+1)*width]
             for index in range(size)]
    complexes = []
    for lump in lumps:
        as_int = int(''.join(reversed(lump)), 2)
        as_complex = complex_from_slv(as_int, width)
        complexes.append(as_complex)
    return complexes


def list_of_uints_to_slv(values, width):
    slv = 0
    f = 1
    step = pow(2, width)
    for value in values:
        slv += value * f
        f *= step
    return slv


def list_of_uints_from_slv(slv, width, size):
    step = pow(2, width)
    values = []
    for i in range(size):
        values.append(slv % step)
        slv = slv >> width
    assert slv == 0
    return values


if __name__ == '__main__':
    import doctest
    doctest.testmod()
