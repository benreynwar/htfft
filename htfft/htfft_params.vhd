package htfft{{suffix}}_params is
  constant INPUT_WIDTH: positive := {{input_width}};
  constant OUTPUT_WIDTH: positive := {{output_width}};
  constant N: positive := {{n}};
  constant SPCC: positive := {{spcc}};
  constant BUTTERFLY_LATENCY: natural := {{butterfly_latency}};
  constant BARREL_SHIFTER_PIPELINE: string := "{{barrel_shifter_pipeline}}";
end package;
