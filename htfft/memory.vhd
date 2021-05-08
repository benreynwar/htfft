library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.htfft_pkg.all;

entity memory is
  generic (
    WIDTH: positive;
    DEPTH: positive;
    ADDRESS_CLASH: string
    );
  port (
    clk: in std_logic;
    write_valid: in std_logic;
    write_address: in unsigned(logceil(DEPTH)-1 downto 0);
    write_data: in std_logic_vector(WIDTH-1 downto 0);
    toread_valid: in std_logic;
    toread_address: in unsigned(logceil(DEPTH)-1 downto 0);
    fromread_data: out std_logic_vector(WIDTH-1 downto 0)
    );
end entity;

architecture arch of memory is
  subtype t_data is std_logic_vector(WIDTH-1 downto 0);
  type array_of_data is array(natural range <>) of t_data;
  signal memory_contents: array_of_data(DEPTH-1 downto 0);
begin

  assert (ADDRESS_CLASH = "UNDEFINED") or (ADDRESS_CLASH = "OLD") or (ADDRESS_CLASH = "NEW") severity failure;

  process(clk)
  begin
    if rising_edge(clk) then
      if write_valid = '1' then
        memory_contents(to_integer(write_address)) <= write_data;
      end if;
      if toread_valid = '1' then
        if (write_valid = '1') and (write_address = toread_address) then
          if ADDRESS_CLASH = "OLD" then
            fromread_data <= memory_contents(to_integer(toread_address));
          elsif ADDRESS_CLASH = "NEW" then
            fromread_data <= write_data;
          else
            fromread_data <= (others => 'U');
          end if;
        else
          fromread_data <= memory_contents(to_integer(toread_address));
        end if;
      end if;
    end if;
  end process;

end architecture;



  
