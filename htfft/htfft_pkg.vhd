package htfft_pkg is
  function logceil(value: natural) return integer;
  function count_pipeline_length(pipeline: string) return natural;

  -- The pipeline for the butterflys should be moved to this package.
  constant BUTTERFLY_LATENCY: natural := 7;
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

  function count_pipeline_length(pipeline: string) return natural is
    variable count: natural := 0;
  begin
    for index in pipeline'range loop
      if pipeline(index) = '1' then
        count := count + 1;
      end if;
    end loop;
    return count;
  end function;

end package body;
