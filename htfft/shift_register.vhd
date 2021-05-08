library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity shift_register is
  generic (
    WIDTH: positive;
    LENGTH: natural
    );
  port (
    clk: in std_logic;
    i_data: in std_logic_vector(WIDTH-1 downto 0);
    o_data: out std_logic_vector(WIDTH-1 downto 0)
  );
end entity;

architecture arch of shift_register is
  subtype t_data is std_logic_vector(WIDTH-1 downto 0);
  type array_of_data is array(natural range <>) of t_data;
  signal dataarray: array_of_data(LENGTH-1 downto 0);
begin
  zero_length: if LENGTH = 0 generate
    o_data <= i_data;
  end generate;
  nonzero_length: if LENGTH > 0 generate
    process(clk)
    begin
      if rising_edge(clk) then
        dataarray(LENGTH-1) <= i_data;
        for ii in 0 to LENGTH-2 loop
          dataarray(ii) <= dataarray(ii+1);
        end loop;
      end if;
    end process;
    o_data <= dataarray(0);
  end generate;
end architecture;
