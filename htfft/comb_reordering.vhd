library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.htfft_pkg.all;

entity comb_reordering is
  generic (
    WIDTH: positive;
    SIZE: positive
    );
  port (
    i_data: in std_logic_vector(WIDTH*SIZE-1 downto 0);
    o_data: out std_logic_vector(WIDTH*SIZE-1 downto 0)
    );
end entity;

architecture arch of comb_reordering is

  function reverse_bits(value: natural; address_width: natural) return natural is
    constant original_unsigned: unsigned(address_width-1 downto 0) := to_unsigned(value, address_width);
    variable reversed_unsigned: unsigned(address_width-1 downto 0);
  begin
    for ii in 0 to address_width - 1 loop
      reversed_unsigned(ii) := original_unsigned(address_width-1-ii);
    end loop;
    return to_integer(reversed_unsigned);
  end function;

  subtype t_data is std_logic_vector(WIDTH-1 downto 0);
  type array_of_data is array(natural range <>) of t_data;
  signal i_dataarray: array_of_data(SIZE-1 downto 0);
  signal o_dataarray: array_of_data(SIZE-1 downto 0);
  
begin

  loop_pieces: for ii in 0 to SIZE-1 generate
    i_dataarray(ii) <= i_data((ii+1)*WIDTH-1 downto ii*WIDTH);
    o_dataarray(ii) <= i_dataarray(reverse_bits(ii, logceil(SIZE)));
    o_data((ii+1)*WIDTH-1 downto ii*WIDTH) <= o_dataarray(ii);
  end generate;

end architecture;

