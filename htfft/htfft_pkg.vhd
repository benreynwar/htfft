package htfft_pkg is
  function logceil(value: natural) return integer;
end package;

package body htfft_pkg is

  function logceil(value: natural) return integer is
    variable n_bits: integer := 0;
    variable remainder: natural := value;
  begin
    while remainder > 1 loop
      n_bits := n_bits + 1;
      remainder := remainder/2;
    end loop;
    return n_bits;
  end function;

end package body;
